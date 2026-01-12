from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re


URL = "https://www.amazon.in/gp/aw/d/B0DGQ6Z78X?_encoding=UTF8&pd_rd_plhdr=t&aaxitk=e8a87e4f5d7e8fa93776ca96e0a36c3f&hsa_cr_id=0&qid=1766927391&sr=1-1-1ee1b2e4-01d1-4cd0-b737-4c27ebfc8105&aref=TBOjSprCCS&pd_rd_w=VkZhr&content-id=amzn1.sym.a66b3449-0491-4455-b928-7d9918a72d25%3Aamzn1.sym.a66b3449-0491-4455-b928-7d9918a72d25&pf_rd_p=a66b3449-0491-4455-b928-7d9918a72d25&pf_rd_r=D4JERH316BEPF4R6MB7D&pd_rd_wg=lNOUw&pd_rd_r=803b884b-b2bf-4d61-8778-4fce0a86aedb&th=1&linkCode=ll1&tag=mirzaasim2001-21&linkId=a6ee8748379b616c0e1f823fd60cbe99&language=en_IN&ref_=as_li_ss_tl"


def format_rupees(text):
    """
    Extract numbers and return formatted ₹ value
    """
    numbers = re.findall(r"\d+", text.replace(",", ""))
    if not numbers:
        return None

    value = int("".join(numbers))
    return f"₹{value:,}".replace(",", ",")


def get_amazon_price(url):
    options = Options()

    # Make browser look human
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # COMMENT this if you want to see browser
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        time.sleep(6)  # let Amazon fully load

        deal_price = None
        regular_price = None

        # 🔴 DEAL PRICE (highest priority)
        try:
            deal = driver.find_element(By.CSS_SELECTOR, "#priceblock_dealprice")
            deal_price = format_rupees(deal.text)
        except:
            pass

        # 🟡 REGULAR PRICE
        try:
            regular = driver.find_element(By.CSS_SELECTOR, "#priceblock_ourprice")
            regular_price = format_rupees(regular.text)
        except:
            pass

        # 🟢 FALLBACK (mobile / dynamic layouts)
        if not deal_price and not regular_price:
            try:
                fallback = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                regular_price = format_rupees(fallback.text)
            except:
                pass

        # ✅ FINAL OUTPUT LOGIC
        if deal_price:
            print("🔥 DEAL PRICE FOUND:", deal_price)
            return deal_price

        if regular_price:
            print("✅ REGULAR PRICE FOUND:", regular_price)
            return regular_price

        print("❌ PRICE NOT FOUND")
        return None

    finally:
        driver.quit()


if __name__ == "__main__":
    price = get_amazon_price(URL)
    print("FINAL PRICE TO SAVE IN DB:", price)
