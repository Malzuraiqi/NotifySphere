from dotenv import load_dotenv
import os, re
from playwright.sync_api import Page
from Database import Database

class Scraper:
    def login(self, page:Page):
        load_dotenv()
        page.goto("https://my.cud.ac.ae/my/")
        username = os.getenv('TEST_USERNAME', '')
        password = os.getenv('TEST_PASSWORD', '')
        page.fill('#username', username)
        page.fill('#password', password)

        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(r".*my\.cud\.ac\.ae.*")) # make sure you're still in mycud

    def goto_calendar(self, page:Page):
        self.login(page)
        calender = page.get_by_title("This month")
        calender_link = calender.get_attribute("href")
        calender.click()
        page.wait_for_load_state('networkidle')  # Wait for page to load

        return calender_link

    def check_database(self, page:Page):
        days = page.query_selector_all("td.clickable[data-region='day']:has(li[data-region='event-item'])")
        tasks_by_day = []
        for day in days:

            day_anchor = day.query_selector("a.day")
            if day_anchor:
                day_number = int(day_anchor.text_content().strip())
            else:
                continue

            task_anchors = day.query_selector_all("li[data-region='event-item'] a[data-action='view-event']")

            for task_anchor in task_anchors:
                title = task_anchor.get_attribute("title")
                if title:
                    if " is due" in title:
                        title = title.replace(" is due", '')

                    tasks_by_day.append((day_number, title))

        db = Database()
        database_tasks = db.get_tasks_for_comparison()

        return list(set(tasks_by_day) - set(database_tasks))

    def get_tasks(self, page:Page):
        all_tasks_details = []
        tasks_by_day = []
        month_links = []  # Store links for each month

        # First month
        calender_link = self.goto_calendar(page)
        month_links.append(calender_link)  # Store first month link
        tasks_by_day.extend([(day, title, 0) for day, title in self.check_database(page)])  # Add month index

        # Second month
        page.click("a[title='Next month']")
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Get new calendar link for second month - be more specific
        # Option 1: Get the current month link from the calendar header
        new_calender_link = page.locator("a[title='This month']").nth(1).get_attribute('href')
        # Or Option 2: Use the main calendar navigation
        # new_calender_link = page.locator(".calendar-controls >> a[title='This month']").get_attribute("href")
        # Or Option 3: Get the link that's currently visible in the main calendar area
        # new_calender_link = page.locator(".maincalendar >> a[title='This month']").first.get_attribute("href")
        
        month_links.append(new_calender_link)  # Store second month link
        
        tasks_by_day.extend([(day, title, 1) for day, title in self.check_database(page)])  # Add month index

        day_in_unix = 86400

        if tasks_by_day:
            for day, title, month_index in tasks_by_day:
                # Use the correct month link
                current_calender_link = month_links[month_index]
                
                day_one = int(current_calender_link[-10:])
                due_day = day_one + (day-1) * day_in_unix
                due_day_link = current_calender_link.replace(str(day_one), str(due_day)).replace("month", "day")
                
                page.goto(due_day_link)

                # Rest of your processing code...
                tasks = page.query_selector_all('a:has-text("Go to activity")')
                links = []
                for task in tasks:
                    link = task.get_attribute("href")
                    links.append(link)
                
                for link in links:
                    page.goto(link)
                    page.wait_for_load_state('networkidle')

                    try:
                        course_title = page.locator(".page-header-headings h1").text_content()
                        assignment = page.get_by_role("main").locator("h2").text_content()
                        submission_status = page.locator(".cell.c1.lastcol").nth(0).text_content()
                        due_date = page.locator(".cell.c1.lastcol").nth(2).text_content()

                        task_details = {
                            'day': day,
                            'month': month_index + 1,
                            'course': course_title.strip(),
                            'assignment': assignment.strip(),
                            'status': submission_status.strip(),
                            'due_date': due_date.strip(),
                            'url': link
                        }

                        all_tasks_details.append(task_details)

                    except Exception as e:
                        print(f"Error processing task {link}: {e}")
        else:
            print(f"{len(tasks_by_day)} new task/s")

        return all_tasks_details