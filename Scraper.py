import requests
from bs4 import BeautifulSoup
from website.models import insert_tasks, get_tasks_for_comparison, get_user_cookies
import urllib3
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Scraper:
    BASE_URL = "https://my.cud.ac.ae" # to load the cookies

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        })

    def parse_due_date(self, date_str):
        """
        Converts a Moodle date string to a datetime object.
        Handles both formats:
        1. 'Wednesday, 5 November 2025, 12:00 AM'
        2. '25 Nov 2025 - 12:38'
        """
        try:
            # Format 1
            print("used format 1")
            dt = datetime.strptime(date_str, "%A, %d %B %Y, %I:%M %p")
            return dt.strftime("%d/%m/%Y %I:%M %p")
        except ValueError:
            try:
                # Format 2
                print("used format 2")
                dt = datetime.strptime(date_str, "%d %b %Y - %H:%M")
                return dt.strftime("%d/%m/%Y %I:%M %p")
            except ValueError:
                # Could not parse
                print(f"DEBUG: Unknown date format: {date_str}")
                return None

    def load_cookies_from_db(self, user_id):
        """Load cookies from database and add them to the session"""
        saved_cookies = get_user_cookies(user_id)
        print(f"DEBUG: Loaded {len(saved_cookies)} cookies from DB")

        if not saved_cookies:
            print("DEBUG: No cookies found for this user.")
            return False

        for cookie in saved_cookies:
            # Ensure minimal required fields exist
            if "name" in cookie and "value" in cookie:
                # Remove leading dot in domain if present
                domain = cookie.get("domain", "").lstrip(".")
                cookie_dict = {
                    "domain": domain or "my.cud.ac.ae",
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "path": cookie.get("path", "/"),
                }
                self.session.cookies.set(**cookie_dict)

        print(f"DEBUG: Added {len(self.session.cookies)} cookies to session")
        return True
    
    def check_login_status(self):
        """Check if current session is logged in by visiting the dashboard"""
        dashboard_url = f"{self.BASE_URL}/my/"
        response = self.session.get(dashboard_url)

        if "login" in response.url.lower() or response.status_code != 200:
            print("DEBUG: Not logged in - login required")
            return False

        print("DEBUG: Already logged in with current cookies")
        return True
    
    def init_session_with_cookies(self, user_id):
        """
        Load cookies from DB into the session and check if they are valid.
        Returns True if session is authenticated, False otherwise.
        """
        if not self.load_cookies_from_db(user_id):
            return False  # No cookies found

        # Check if session is valid
        if not self.check_login_status():
            return False  # Cookies invalid / expired

        return True
    
    def check_database(self, html, user_id):
        """
        Parse the calendar month HTML to find tasks not already in the database.
        Returns a list of tuples: (day_number, task_title)
        """
        soup = BeautifulSoup(html, "html.parser")

        # Find days with tasks
        days = []
        for td in soup.select("td.clickable[data-region='day']"):
            if td.select("li[data-region='event-item']"):
                days.append(td)

        tasks_by_day = []

        for day in days:
            try:
                day_anchor = day.select_one("a.day")
                day_number = int(day_anchor.text.strip()) if day_anchor else None
                if not day_number:
                    continue

                task_anchors = day.select("li[data-region='event-item'] a[data-action='view-event']")
                for task_anchor in task_anchors:
                    title = task_anchor.get("title", "")
                    if title and " is due" in title:
                        title = title.replace(" is due", "")
                    tasks_by_day.append((day_number, title))
            except Exception:
                continue  # Skip any problematic day

        # Compare with database tasks
        database_tasks = get_tasks_for_comparison(user_id)
        new_tasks = list(set(tasks_by_day) - set(database_tasks))

        return new_tasks
    
    def get_tasks(self, date, user_id):
        """
        Get all tasks for a specific month using requests + BS4.
        Returns a list of task details.
        """
        all_tasks_details = []

        # Month calendar URL
        calendar_url = f"{self.BASE_URL}/calendar/view.php?view=month&time={date}"

        # Step 1: Fetch month page
        response = self.session.get(calendar_url)
        if response.status_code != 200:
            print(f"DEBUG: Failed to fetch calendar month page ({response.status_code})")
            return []

        # Step 2: Find new tasks
        tasks_by_day = self.check_database(response.text, user_id)
        day_in_unix = 86400  # seconds in a day

        # Step 3: Fetch day pages and extract task links
        for day, _ in tasks_by_day:
            due_day = int(date) + (day - 1) * day_in_unix
            day_url = calendar_url.replace("month", "day").replace(date, str(due_day))
            day_response = self.session.get(day_url)
            if day_response.status_code != 200:
                continue

            day_soup = BeautifulSoup(day_response.text, "html.parser")
            # Find "Go to activity" links
            task_links = [
                a.get("href")
                for a in day_soup.select("a:-soup-contains('Go to activity')")
            ]

            # Step 4: Get task details for each link
            for link in task_links:
                task_details = self.get_task_details(link)
                if task_details:
                    task_details.update({
                        "day": day,
                        "month": date
                    })
                    all_tasks_details.append(task_details)

        return all_tasks_details
    
    def get_task_details(self, link):
        """
        Extract task details from an assignment page.
        Returns a dict with course, assignment, status, due_date, and url.
        """
        response = self.session.get(link)
        if response.status_code != 200:
            print(f"DEBUG: Failed to fetch task page: {link}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        try:
            # Try normal format first
            course_title = soup.select_one(".page-header-headings h1").text.strip()
            main_div = soup.select_one('div[role="main"]')
            assignment = main_div.select_one("h2").text.strip()
            status_elements = soup.select(".cell.c1.lastcol")

            if len(status_elements) >= 3:
                submission_status = status_elements[0].text.strip()
                due_date_str = status_elements[2].text.strip()
            else:
                raise Exception("Normal format failed")

        except Exception:
            # Alternative format
            try:
                course_title = soup.select_one(".page-header-headings h1").text.strip()
                assignment = soup.select_one(".cell.c0").text.strip()
                due_date_str = soup.select_one(".data.cell.c2").text.strip()

                submission_table = soup.select_one("table.submissionsDataTable tbody")
                if submission_table:
                    submitted_td = submission_table.select_one("td.right.cell.c7")
                    if submitted_td and submitted_td.text.strip() != "--":
                        submission_status = "Submitted for grading"
                    else:
                        submission_status = "Not submitted"
                else:
                    submission_status = "Not submitted"

            except Exception as e:
                print(f"DEBUG: Both formats failed for {link}: {e}")
                return None

        print(due_date_str)
        due_date = self.parse_due_date(due_date_str)
        print(due_date)
        return {
            "course": course_title,
            "assignment": assignment,
            "status": submission_status,
            "due_date": due_date,
            "url": link
        }