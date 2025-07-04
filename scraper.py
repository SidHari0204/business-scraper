import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Required for Render
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    # Use Chromium on Render (Chrome isn't installed by default)
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_google_maps(city, category, limit=20):  # Reduced limit to avoid rate limits
    driver = setup_driver()
    try:
        query = f"{category} in {city}"
        driver.get(f"https://www.google.com/maps/search/{query}")
        time.sleep(5)

        panel_xpath = '//div[contains(@aria-label, "Results for") or contains(@aria-label, "places") or contains(@aria-label, "Search results")]'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, panel_xpath)))
        scrollable_div = driver.find_element(By.XPATH, panel_xpath)

        for _ in range(5):  # Reduced scrolls to avoid timeouts
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2)

        results = []
        for i in range(min(limit, 5)):  # Max 5 results for stability
            try:
                cards = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                if i >= len(cards):
                    break
                card = cards[i]
                driver.execute_script("arguments[0].scrollIntoView();", card)
                time.sleep(1)
                card.click()
                time.sleep(3)

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf")))
                name = driver.find_element(By.CLASS_NAME, "DUwDvf").text
                address = driver.find_element(By.CLASS_NAME, "Io6YTe").text

                phone = None
                text_blocks = driver.find_elements(By.CLASS_NAME, "Io6YTe")
                for el in text_blocks:
                    txt = el.text.strip()
                    if re.match(r"^0?\d{5}\s?\d{5}$", txt):
                        phone = txt
                        break

                try:
                    rating = float(driver.find_element(By.CLASS_NAME, "MW4etd").text)
                except:
                    rating = None

                results.append({
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "rating": rating
                })
            except Exception as e:
                print(f"Skipped card {i+1}: {e}")
                continue
    finally:
        driver.quit()
    return results