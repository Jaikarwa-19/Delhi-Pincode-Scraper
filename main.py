import asyncio
import time
import json
import re
import pandas as pd
from playwright.async_api import async_playwright
import requests
import os

GOOGLE_MAPS_API_KEY = "AIzaSyBMpVJjmrlz7Kq3la3jeQ1JlkD9oYsdny0"
CACHE_FILE = "address_cache.json"
PARTIAL_CSV = "partial_justdial_delhi_bedsheet_listings.csv"

# Load existing cache if available
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        address_cache = json.load(f)
else:
    address_cache = {}

async def scroll_page(page):
    for _ in range(10):
        await page.mouse.wheel(0, 1000)
        await asyncio.sleep(0.7)

async def extract_pincode_from_google_maps(address):
    if address in address_cache:
        return address_cache[address]

    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'OK':
            for component in data['results'][0]['address_components']:
                if 'postal_code' in component['types']:
                    pincode = component['long_name']
                    address_cache[address] = pincode
                    with open(CACHE_FILE, "w") as f:
                        json.dump(address_cache, f)
                    return pincode
    except Exception as e:
        print(f"⚠️ Google Maps API error for address '{address}': {e}")
    address_cache[address] = None
    with open(CACHE_FILE, "w") as f:
        json.dump(address_cache, f)
    return None

async def safe_goto(page, url, retries=3):
    for attempt in range(retries):
        try:
            await page.goto(url, timeout=60000, wait_until="load")
            await asyncio.sleep(3)
            return True
        except Exception as e:
            print(f"⚠️ Retry {attempt + 1} failed for {url}: {e}")
            try:
                html = await page.content()
                with open(f"debug_page_{url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except:
                pass
            await asyncio.sleep(2 + attempt * 2)
    print(f"❌ All retries failed for {url}")
    return False

async def scrape_justdial_delhi():
    listings = []
    if os.path.exists(PARTIAL_CSV):
        listings = pd.read_csv(PARTIAL_CSV).to_dict('records')
        print(f"🔁 Resuming from saved state with {len(listings)} records.")

    base_url = "https://www.justdial.com/Delhi/Bed-Sheet-Retailers/nct-10042823/page-{}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        page = await context.new_page()

        for page_num in range(1, 200):
            url = base_url.format(page_num)
            print(f"🔍 Visiting: {url}")

            success = await safe_goto(page, url)
            if not success:
                continue

            await scroll_page(page)
            listing_cards = await page.query_selector_all("a.resultbox_title_anchorbox")
            print(f"🔍 Found {len(listing_cards)} listings on page {page_num}")

            if not listing_cards:
                break

            detail_tasks = []
            for card in listing_cards:
                detail_url = await card.get_attribute("href")
                name = await card.inner_text()
                if detail_url:
                    if not detail_url.startswith("http"):
                        detail_url = "https://www.justdial.com" + detail_url
                    detail_tasks.append(scrape_detail_page(context, detail_url, name))

            results = await asyncio.gather(*detail_tasks)
            for result in results:
                if result:
                    listings.append(result)

            df = pd.DataFrame(listings)
            df.drop_duplicates(subset=["Name", "Pincode"], inplace=True)
            df.to_csv(PARTIAL_CSV, index=False)
            print(f"✅ Partial data saved at {PARTIAL_CSV}. Total collected so far: {len(df)}")

            if len(df) >= 3000:
                break

        await browser.close()

    final_path = os.path.expanduser("~/justdial_delhi_bedsheet_listings.csv")
    df = pd.DataFrame(listings)
    df.drop_duplicates(subset=["Name", "Pincode"], inplace=True)
    df.to_csv(final_path, index=False)
    print(f"✅ Final data saved to {final_path}")

async def scrape_detail_page(context, detail_url, name):
    try:
        detail_page = await context.new_page()
        await detail_page.goto(detail_url, timeout=30000)
        await asyncio.sleep(2)

        addr_el = await detail_page.query_selector("address")
        address = await addr_el.inner_text() if addr_el else ""

        await detail_page.close()

        if name and address:
            pincode = await extract_pincode_from_google_maps(address)
            return {
                "Name": name.strip(),
                "URL": detail_url,
                "Address": address.strip(),
                "Pincode": pincode.strip() if pincode else ""
            }
    except Exception as e:
        print(f"⚠️ Failed to extract from {detail_url}: {e}")
    return None

if __name__ == "__main__":
    asyncio.run(scrape_justdial_delhi())

