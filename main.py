'''✅❌
Day4, Main Goals:
1- do a simple tkinter GUI
2- add a button to start the automation process
3- go study
'''

from playwright.sync_api import sync_playwright
from Scraper import Scraper
from Database import Database
from GUI import App
import tkinter as tk

def main():
    db = Database()
    '''
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        scraper = Scraper()
        tasks_details = scraper.get_tasks(page)

    db.insert_tasks(tasks_details)
    '''
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()