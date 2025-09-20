'''✅❌
Day2, Main Goals:
1- create the database that will hold the tasks details ✅
2- compare the extracted data with the saved ones and print them 
3- stop if there is nothing new
4- if there is a unsubmitted task in the database keep checking it
'''

from playwright.sync_api import sync_playwright
from Scraper import Scraper
from Database import Database

def main():
    db = Database()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        scraper = Scraper()
        tasks_details = scraper.get_tasks(page)

    db.insert_tasks(tasks_details)

if __name__ == "__main__":
    main()