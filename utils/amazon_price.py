from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re


def get_amazon_price(url):
    options = Options()
    options.add_argument("--headless=new")  # 👈 silent
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    price = None

    try:
        driver.get(url)
        time.sleep(5)

        selectors = [
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            "span.a-price-whole"
        ]

        for selector in selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                text = el.text.strip()

                if text:
                    number = re.sub(r"[^\d]", "", text)
                    if number:
                        price = f"₹{int(number):,}"
                        break
            except:
                continue

    finally:
        driver.quit()

    return price
