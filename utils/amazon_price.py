import os
import time
import re
from dotenv import load_dotenv
from supabase import create_client

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# =============================
# ENV + SUPABASE
# =============================

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")  # 🔴 SERVICE ROLE KEY
)


# =============================
# AMAZON PRICE SCRAPER
# =============================

def format_rupees(text):
    numbers = re.findall(r"\d+", text.replace(",", ""))
    if not numbers:
        return None
    value = int("".join(numbers))
    return f"₹{value:,}"


def get_amazon_price(url):
    options = Options()
    options.add_argument("--headless=new")   # comment this if you want to see browser
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        time.sleep(20)  # let Amazon fully load

        # 🔴 Deal price
        try:
            deal = driver.find_element(By.CSS_SELECTOR, "#priceblock_dealprice")
            price = format_rupees(deal.text)
            if price:
                return price
        except:
            pass

        # 🟡 Regular price
        try:
            regular = driver.find_element(By.CSS_SELECTOR, "#priceblock_ourprice")
            price = format_rupees(regular.text)
            if price:
                return price
        except:
            pass

        # 🟢 Fallback (mobile/dynamic)
        try:
            fallback = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
            price = format_rupees(fallback.text)
            if price:
                return price
        except:
            pass

        return None

    finally:
        driver.quit()


# =============================
# MAIN UPDATE LOGIC
# =============================

def update_all_prices():
    products = (
        supabase
        .table("products")
        .select("id, title, link, price")
        .execute()
        .data
    )

    print(f"\nFound {len(products)} products\n")

    updated = 0
    failed = 0

    for p in products:
        print(f"🔄 Updating: {p['title']}")

        if not p.get("link"):
            print("   ⚠️ No link found")
            failed += 1
            continue

        new_price = get_amazon_price(p["link"])

        if new_price and new_price != p["price"]:
            supabase.table("products").update({
                "price": new_price
            }).eq("id", p["id"]).execute()

            updated += 1
            print(f"   ✅ Updated to {new_price}")

        elif new_price:
            print(f"   ℹ️ Price unchanged ({new_price})")

        else:
            failed += 1
            print("   ❌ Price not found")

        time.sleep(2)  # ⛔ avoid Amazon blocking

    print("\n==============================")
    print(f"✅ Updated: {updated}")
    print(f"❌ Failed:  {failed}")
    print("🎉 DONE")
    print("==============================\n")


# =============================
# RUN
# =============================

if __name__ == "__main__":
    update_all_prices()
