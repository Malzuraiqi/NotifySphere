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
        tasks_by_day = {}
        for day in days:

            day_anchor = day.query_selector("a.day")
            if day_anchor:
                day_number = int(day_anchor.text_content().strip())
            else:
                continue
            
            tasks_title = []

            task_anchors = day.query_selector_all("li[data-region='event-item'] a[data-action='view-event']")

            for task_anchor in task_anchors:
                title = task_anchor.get_attribute("title")
                if title:
                    if " is due" in title:
                        title = title.replace(" is due", '')

                    tasks_title.append(title)

            tasks_by_day[day_number] = tasks_title

        db = Database()
        database_tasks = db.get_tasks_details()

        for day_number in list(tasks_by_day.keys()): 
            for task_title in list(tasks_by_day[day_number]): 
                
                task_exists = any(
                    db_task['day'] == day_number and 
                    db_task['assignment'] == task_title  
                    for db_task in database_tasks
                )
                
                if task_exists:
                    tasks_by_day[day_number].remove(task_title)
            
            if not tasks_by_day[day_number]:
                del tasks_by_day[day_number]

        return tasks_by_day

    def get_tasks(self, page:Page):
        all_tasks_details = []
        calender_link = self.goto_calendar(page)       
        day_in_unix = 86400
        tasks_by_day = self.check_database(page)

        print(tasks_by_day)
        for day in tasks_by_day.keys():
            # change the link to be suitable for each day instead of the month
            day_one = int(calender_link[-10:])
            due_day = day_one + (day-1) * day_in_unix
            due_day_link = calender_link.replace(str(day_one), str(due_day)).replace("month", "day")
            
            page.goto(due_day_link)

            # get all the links for tasks that are due that day (can be more than one)
            tasks = page.query_selector_all('a:has-text("Go to activity")')

            # save the links to a list
            links = []
            for task in tasks:
                link = task.get_attribute("href")
                links.append(link)
            
            # visit all the links and extract the data
            for link in links:
                page.goto(link)
                page.wait_for_load_state('networkidle')

                # so that if there is any issue with a certain task it doesn't crash the whole program
                try:
                    course_title = page.locator(".page-header-headings h1").text_content()
                    assignment = page.get_by_role("main").locator("h2").text_content()
                    submission_status = page.locator(".submissionstatussubmitted.cell.c1.lastcol").text_content()
                    due_date = page.locator(".cell.c1.lastcol").nth(2).text_content()

                    task_details = {
                        'day': day,
                        'course': course_title.strip(),
                        'assignment': assignment.strip(),
                        'status': submission_status.strip(),
                        'due_date': due_date.strip(),
                        'url': link
                    }

                    all_tasks_details.append(task_details)

                except Exception as e:
                    print(f"Error processing task {link}: {e}")

        return all_tasks_details