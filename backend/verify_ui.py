from playwright.sync_api import Page, sync_playwright
import os

def verify_feature(page: Page):
  page.goto("http://localhost:8000/workbench")
  page.wait_for_timeout(1000)

  # Click the Dividends Data Bank tab
  page.evaluate("document.querySelector('#nav-btn-dividends').click()")
  page.wait_for_timeout(1000)

  # Click "Board Meetings" Sub-tab
  page.evaluate("switchDividendsTab('meetings')")
  page.wait_for_timeout(1000)

  # Click Load Data
  page.evaluate("loadDividendsData()")
  page.wait_for_timeout(2000) # wait for fetch and render

  page.screenshot(path="/home/jules/verification/verification.png")
  page.wait_for_timeout(1000)

if __name__ == "__main__":
  os.makedirs("/home/jules/verification/video", exist_ok=True)
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(record_video_dir="/home/jules/verification/video")
    page = context.new_page()
    try:
      verify_feature(page)
    finally:
      context.close()
      browser.close()
