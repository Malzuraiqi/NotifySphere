from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
#from webdriver_manager.chrome import ChromeDriverManager
from website.models import insert_tasks, get_tasks_for_comparison, get_user_cookies

class Scraper:
    def run_scraper(self, user_id, date):
        saved_cookies = get_user_cookies(user_id)
        print(f"DEBUG: Loaded {len(saved_cookies)} cookies from DB")
        
        if not saved_cookies:
            return False
        
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get("my.cud.ac.ae")
            for cookie in saved_cookies:
                if "my.cud.ac.ae" in cookie['domain']:
                    driver.add_cookie(cookie)

            driver.get("yourvoice.cud.ac.ae")
            for cookie in saved_cookies:
                if "yourvoice.cud.ac.ae" in cookie['domain']:
                    driver.add_cookie(cookie)
            
            driver.get("https://my.cud.ac.ae/my/")
            print(f"DEBUG: Final URL: {driver.current_url}")
            print(f"DEBUG: Page title: {driver.title}")
            
            # Check if still logged in
            if "my.cud.ac.ae/my/" not in driver.current_url:
                print("DEBUG: NOT logged in - redirect detected")
                return False
            
            print("DEBUG: Successfully logged in with cookies!")
            # ... rest of code
            
        except Exception as e:
            print(f"DEBUG: Error: {e}")
            return False
        finally:
            driver.quit()

    def check_database(self, driver, user_id):
        """Check for new tasks not already in database"""
        # Find days with tasks using CSS selector
        days = driver.find_elements(By.CSS_SELECTOR, "td.clickable[data-region='day']:has(li[data-region='event-item'])")
        print(days)
        tasks_by_day = []

        for day in days:
            try:
                day_anchor = day.find_element(By.CSS_SELECTOR, "a.day")
                day_number = int(day_anchor.text.strip())
                
                task_anchors = day.find_elements(By.CSS_SELECTOR, "li[data-region='event-item'] a[data-action='view-event']")
                
                for task_anchor in task_anchors:
                    title = task_anchor.get_attribute("title")
                    print(title, flush=True)
                    if title and " is due" in title:
                        title = title.replace(" is due", '')
                        tasks_by_day.append((day_number, title))
                        
            except Exception as e:
                continue  # Skip this day if any error

        database_tasks = get_tasks_for_comparison(user_id)
        return list(set(tasks_by_day) - set(database_tasks))

    def get_tasks(self, driver, date, user_id):
        """Get all tasks for a specific month"""
        all_tasks_details = []
        calendar_link = f"https://my.cud.ac.ae/calendar/view.php?view=month&time={date}"
        driver.get(calendar_link)
        
        tasks_by_day = self.check_database(driver, user_id)
        day_in_unix = 86400
        
        for day, _ in tasks_by_day:
            due_day = int(date) + (day - 1) * day_in_unix
            day_link = calendar_link.replace("month", "day").replace(date, str(due_day))
            driver.get(day_link)
            
            # Find "Go to activity" links
            tasks = driver.find_elements(By.XPATH, "//a[contains(text(), 'Go to activity')]")
            links = [task.get_attribute("href") for task in tasks]
            
            for link in links:
                task_details = self.get_task_details(driver, link)
                if task_details:
                    task_details.update({
                        'day': day,
                        'month': date
                    })
                    all_tasks_details.append(task_details)

        return all_tasks_details


    def get_task_details(self, driver, link):
        """Extract task details from assignment page with both formats"""
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try:
            # Try normal format first
            course_title = driver.find_element(By.CSS_SELECTOR, ".page-header-headings h1").text
            assignment = driver.find_element(By.CSS_SELECTOR, "main h2").text
            status_elements = driver.find_elements(By.CSS_SELECTOR, ".cell.c1.lastcol")
            
            if len(status_elements) >= 3:
                submission_status = status_elements[0].text
                due_date = status_elements[2].text
            else:
                print('First fails')
                raise Exception("Normal format failed")
                
        except Exception:
            # Alternative format
            try:
                course_title = driver.find_element(By.CSS_SELECTOR, ".page-header-headings h1").text
                assignment = driver.find_element(By.CSS_SELECTOR, ".cell.c0").text
                due_date = driver.find_element(By.CSS_SELECTOR, ".data.cell.c2").text
                
                # Check submission status from table
                submission_tables = driver.find_elements(By.CSS_SELECTOR, 'table.submissionsDataTable')
                if submission_tables and len(submission_tables) > 0:
                    rows = submission_tables[0].find_elements(By.CSS_SELECTOR, 'tbody tr')
                    submission_status = "Submitted for grading" if len(rows) > 0 else "Not submitted"
                else:
                    submission_status = "Not submitted"
                    
            except Exception as e:
                print(f"Both formats failed for {link}: {e}")
                return None

        return {
            'course': course_title.strip(),
            'assignment': assignment.strip(),
            'status': submission_status.strip(),
            'due_date': due_date.strip(),
            'url': link
        }