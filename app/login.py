from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="/home/jan-israel/.config/google-chrome/Default",  # 👈 point directly to Default profile folder
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ]
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://webflow.com/dashboard/sites/new/ai-site-builder?workspace=jan-franciss-workspace-5a528a&ref=new-create-site")
    input("Press Enter to close browser...")
