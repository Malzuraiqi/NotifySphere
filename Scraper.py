from dotenv import load_dotenv
import os, re
from playwright.sync_api import Page

class Scraper:
    def login(self, page:Page):
        load_dotenv()
        page.goto("https://my.cud.ac.ae/my/")
        username = os.getenv('TEST_USERNAME', '')
        password = os.getenv('TEST_PASSWORD', '')
        page.fill('#username', username)
        page.fill('#password', password)

        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(r".*my\.cud\.ac\.ae.*"))

    def goto_calendar(self, page:Page):
        self.login(page)
        calender = page.get_by_title("This month")
        calender_link = calender.get_attribute("href")
        calender.click()
        page.wait_for_load_state('networkidle')  # Wait for page to load

        return calender_link

    def get_due_days(self, page:Page):
        calender_link = self.goto_calendar(page)
        day_in_unix = 86400

        due_days_element_format = page.query_selector_all("a.day")
        due_days_number_format = list({int(day.text_content().strip()) for day in due_days_element_format})

        for day in due_days_number_format:
            day_one = int(calender_link[-10:])
            this_day = day_one + (day-1) * day_in_unix
            this_day_link = calender_link.replace(str(day_one), str(this_day)).replace("month", "day")
            page.goto(this_day_link)

            tasks = page.query_selector_all('a:has-text("Go to activity")')

            links = []
            for task in tasks:
                link = task.get_attribute("href")
                links.append(link)
            
            all_tasks_details = []

            for link in links:
                page.goto(link)
                page.wait_for_load_state('networkidle')

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

                page.go_back()
                page.wait_for_load_state('networkidle')