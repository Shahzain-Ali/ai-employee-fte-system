"""Debug: dump LinkedIn feed share box HTML to find correct selectors."""
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [debug] %(message)s")

SESSION_PATH = Path(os.getenv("LINKEDIN_SESSION_PATH", ".sessions/linkedin"))
SESSION_PATH.mkdir(parents=True, exist_ok=True)

for lf in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
    lp = SESSION_PATH / lf
    if lp.exists():
        lp.unlink(missing_ok=True)

pw = sync_playwright().start()
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=str(SESSION_PATH),
    headless=False,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
)
Stealth().apply_stealth_sync(ctx)
page = ctx.pages[0] if ctx.pages else ctx.new_page()

page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
time.sleep(5)
print(f"URL: {page.url}")

# Dump the entire share-box-feed-entry area
print("\n=== Share box feed entry area ===")
share_entry = page.query_selector('div[class*="share-box-feed-entry"]')
if share_entry:
    html = share_entry.evaluate("e => e.outerHTML")
    print(html[:5000])
else:
    print("No share-box-feed-entry found")
    # Try broader search
    all_buttons = page.query_selector_all('button')
    print(f"\nTotal buttons on page: {len(all_buttons)}")
    for btn in all_buttons[:30]:
        try:
            txt = btn.evaluate("e => e.innerText?.trim()?.slice(0, 50)")
            cls = btn.evaluate("e => e.className?.slice(0, 80)")
            if txt:
                print(f"  btn: text='{txt}', class='{cls}'")
        except:
            pass

ctx.close()
pw.stop()
