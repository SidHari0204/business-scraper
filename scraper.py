import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Configure and return a Chrome WebDriver with optimized settings"""
    chrome_options = Options()
    
    # Essential configurations
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--single-process")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Performance settings
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Realistic user agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    try:
        # Try with system chromedriver
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"System chromedriver failed: {e}. Falling back to webdriver-manager")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as fallback_error:
            raise RuntimeError(f"All driver initialization failed: {fallback_error}")

def scrape_google_maps(city, category, max_results=1, scroll_attempts=1):
    """Scrape business listings from Google Maps with robust error handling"""
    driver = None
    results = []
    
    try:
        driver = setup_driver()
        query = f"{category} in {city}".replace(" ", "+")
        url = f"https://www.google.com/maps/search/{query}"
        driver.get(url)
        
        # Wait for results to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        
        # Scroll to load more results
        scrollable_div = driver.find_element(By.CLASS_NAME, "m6QErb.DxyBCb.kA9KIf.dS8AEf")
        for _ in range(scroll_attempts):
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight",
                scrollable_div)
            time.sleep(2)
        
        # Process business cards
        cards = driver.find_elements(By.CLASS_NAME, "hfpxzc")[:max_results]
        
        for idx, card in enumerate(cards, 1):
            try:
                # Scroll to and click the card
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1)
                card.click()
                time.sleep(2)  # Allow details to load
                
                # Extract business information
                name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))).text
                
                # Get all info elements
                info_elements = driver.find_elements(By.CLASS_NAME, "Io6YTe")
                
                # Address is usually first element
                address = info_elements[0].text if len(info_elements) > 0 else "Not found"
                
                # Phone number extraction
                phone = None
                for el in info_elements:
                    txt = el.text.strip()
                    if re.match(r"^(\+?[\d\s\-\(\)]{7,}\d)$", txt):
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

if __name__ == "__main__":
    results = scrape_google_maps("New York", "restaurants", 5)
    print(f"Found {len(results)} results:")
    for biz in results:
        print(f"{biz['name']} - {biz.get('rating', 'No rating')} stars")