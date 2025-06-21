import time
import pandas as pd
from playwright.sync_api import sync_playwright
import re
import requests
import os

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyBMpVJjmrlz7Kq3la3jeQ1JlkD9oYsdny0")

CACHE_FILE = "address_cache.json"
PARTIAL_CSV = "partial_justdial_delhi_bedsheet_listings.csv"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        address_cache = json.load(f)
else:
    address_cache = {}

def extract_pincode_from_html(html):
    match = re.search(r"\b1\d{5}\b", html)  # Delhi pincode pattern
    return match.group() if match else ""

def get_pincode_from_latlng(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results", [])
        for result in results:
            for component in result.get("address_components", []):
                if "postal_code" in component.get("types", []):
                    return component.get("long_name")
    return ""

def scrape_justdial_bedsheets_delhi():
    BASE_LISTING_URL = "https://www.justdial.com/Delhi/Bed-Sheet-Retailers/nct-10042823/page-{}"
    MAX_PAGES = 215
    raw_listings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        page = context.new_page()

        for page_num in range(1, MAX_PAGES + 1):
            url = BASE_LISTING_URL.format(page_num)
            print(f"\n🔄 Loading page {page_num}: {url}")

            for retry in range(3):
                try:
                    page.goto(url, timeout=60000)
                    time.sleep(5)
                    for _ in range(3):
                        page.mouse.wheel(0, 1500)
                        time.sleep(2)
                    page.wait_for_selector("a.resultbox_title_anchorbox", timeout=10000)
                    break
                except Exception as e:
                    print(f"⚠️ Retry {retry+1} failed: {e}")
                    if retry == 2:
                        print("❌ Skipping page after 3 retries.")
                        continue

            cards = page.query_selector_all('a.resultbox_title_anchorbox')
            print(f"↳ Found {len(cards)} listings")
            if not cards:
                break

            for card in cards:
                try:
                    name = card.inner_text().strip()
                    href = card.get_attribute("href")
                    if href and href.startswith("/"):
                        href = "https://www.justdial.com" + href
                    if not href or not href.startswith("http"):
                        continue
                    raw_listings.append({"Name": name, "URL": href, "Address": "", "Pincode": ""})
                except:
                    continue

        browser.close()

    print(f"\n🔎 Collected {len(raw_listings)} raw listings. Now extracting details...")

    detailed_listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        for idx, listing in enumerate(raw_listings):
            print(f"📍 [{idx + 1}/{len(raw_listings)}] Visiting: {listing['Name']}")
            try:
                page.goto(listing["URL"], timeout=60000)
                time.sleep(3)
                html = page.content()
                pincode = extract_pincode_from_html(html)
                listing["Pincode"] = pincode
                try:
                    address = page.locator("address").first.inner_text()
                    listing["Address"] = address
                except:
                    pass
                print(f"✅ Pincode found: {pincode}")
                detailed_listings.append(listing)

                if idx % 25 == 0:
                    pd.DataFrame(detailed_listings).to_csv(PARTIAL_CSV, index=False)
                    print(f"💾 Progress saved after {idx} listings")

            except Exception as e:
                print(f"⚠️ Failed to extract for {listing['Name']}: {e}")
                continue

        browser.close()

    print(f"\n🧹 Deduplicating {len(detailed_listings)} listings by Name + Pincode...")
    seen = set()
    deduped_listings = []
    for l in detailed_listings:
        key = l["Name"].strip().lower() + "|" + l["Pincode"]
        if key not in seen:
            seen.add(key)
            deduped_listings.append(l)
    print(f"✅ Reduced to {len(deduped_listings)} unique listings")

    df = pd.DataFrame(deduped_listings)
    df.to_csv("justdial_delhi_bedsheets.csv", index=False)
    print(f"\n🎉 Done. Saved {len(df)} deduplicated listings to CSV.")

if __name__ == "__main__":
    scrape_justdial_bedsheets_delhi()
