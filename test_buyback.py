from playwright.sync_api import sync_playwright
import time

def run_cuj(page):
    # Navigate using file protocol
    page.goto(f"file:///app/test_charts.html") # Note we'll use a mocked page since FastAPI backend is failing to hit postgres locally
    page.wait_for_timeout(500)
