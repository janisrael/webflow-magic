from playwright.sync_api import sync_playwright

WEBFLOW_URL = "https://webflow.com/dashboard/sites/new/ai-site-builder?workspace=jan-franciss-workspace-5a528a&ref=new-create-site"

BUSINESS_NAME = "SourceSelect"
BUSINESS_DESC = "A Canadian digital agency helping startups build AI-powered apps and websites."

def run(playwright):
    browser = playwright.chromium.launch(headless=False)  # set headless=True to hide browser
    context = browser.new_context()
    
    page = context.new_page()
    page.goto(WEBFLOW_URL)

    # --- STEP 1: Select "a business"
    page.wait_for_selector("text=a business", timeout=10000)
    page.click("text=a business")

    # --- STEP 2: Input business name
    page.wait_for_selector("input[placeholder='What’s the name of your business?']", timeout=5000)
    page.fill("input[placeholder='What’s the name of your business?']", BUSINESS_NAME)

    page.click("text=Next")

    # --- STEP 3: Input business description
    page.wait_for_selector("textarea", timeout=5000)
    page.fill("textarea", BUSINESS_DESC)

    page.click("text=Next")

    # --- STEP 4: Click Generate
    page.wait_for_selector("button:has-text('Generate')", timeout=5000)
    page.click("button:has-text('Generate')")

    print("🎉 Site generation initiated.")
    # browser.close()  # Optional: keep it open

with sync_playwright() as playwright:
    run(playwright)
