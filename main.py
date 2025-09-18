from playwright.sync_api import sync_playwright
from Scraper import Scraper

def main():
    scraper = Scraper()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        scraper.get_due_days(page)

if __name__ == "__main__":
    main()