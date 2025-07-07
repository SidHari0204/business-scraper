import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Configure and return a Chrome WebDriver with Render-optimized settings"""
    chrome_options = Options()
    
    # Essential Render configurations
    chrome_options.binary_location = "/usr/bin/chromium"
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--single-process")  # Reduces memory usage
    
    # Performance and stealth settings
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Realistic user agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        # Primary method: Use system chromedriver (most reliable)
        service = Service("/usr/lib/chromium/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Verify driver works
        driver.get("about:blank")
        return driver
        
    except Exception as e:
        print(f"System chromedriver failed: {e}. Falling back to webdriver-manager")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            # Fallback with exact version matching
            service = Service(ChromeDriverManager(
                version="138.0.7045.6",  # Must match your Chromium version
                cache_valid_range=30
            ).install())
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as fallback_error:
            raise RuntimeError(f"All driver initialization failed: {fallback_error}")

def scrape_google_maps(city, category, max_results=10, scroll_attempts=3):
    """Scrape business listings from Google Maps with robust error handling"""
    driver = None
    results = []
    
    try:
        driver = setup_driver()
        query = f"{category} in {city}"
        driver.get(f"https://www.google.com/maps/search/{query}")
        
        # Wait for results to load
        results_xpath = '//div[contains(@aria-label, "Results for")]'
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, results_xpath)))
        
        # Scroll to load more results
        scrollable_div = driver.find_element(By.XPATH, results_xpath)
        for _ in range(scroll_attempts):
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", 
                scrollable_div)
            time.sleep(2.5)  # Increased delay for Render's limited resources
        
        # Process business cards
        cards = driver.find_elements(By.CLASS_NAME, "hfpxzc")[:max_results]
        
        for idx, card in enumerate(cards, 1):
            try:
                # Scroll to and click the card
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1.2)
                card.click()
                time.sleep(2.8)  # Allow details to load
                
                # Extract business information
                name = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))).text
                
                address = driver.find_element(By.CLASS_NAME, "Io6YTe").text
                
                # Enhanced phone number extraction
                phone = None
                for el in driver.find_elements(By.CLASS_NAME, "Io6YTe"):
                    txt = el.text.strip()
                    if re.match(r"^(\+?[\d\s\-\(\)]{7,}\d)$", txt):  # Robust international pattern
                        phone = txt
                        break
                
                # Rating extraction with fallback
                try:
                    rating = float(driver.find_element(
                        By.CLASS_NAME, "MW4etd").text)
                except Exception:
                    rating = None
                
                results.append({
                    "position": idx,
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "rating": rating
                })
                
            except Exception as e:
                print(f"Error processing card {idx}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        
    finally:
        if driver:
            driver.quit()
    
    return results