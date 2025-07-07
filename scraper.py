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

def scrape_google_maps(city, category, max_results=5):
    driver = setup_driver()
    results = []
    try:
        print(f"Searching for {category} in {city}")
        url = f"https://www.google.com/maps/search/{category}+in+{city}"
        driver.get(url)
        
        # Debug: Save initial page
        driver.save_screenshot("1_initial_load.png")
        
        # Wait for either results or "no results" message
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]') 
                or d.find_elements(By.XPATH, '//div[contains(text(), "No results found")]'))
        except Exception as e:
            print(f"Timeout waiting for results: {e}")
            driver.save_screenshot("2_timeout_error.png")
            return []
        
        # Check for "no results" message
        if driver.find_elements(By.XPATH, '//div[contains(text(), "No results found")]'):
            print("Google Maps shows 'No results found'")
            return []
            
        # Scroll and collect business cards
        scrollable_div = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
        
        for i in range(2):  # Reduced scroll attempts
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2)
            driver.save_screenshot(f"3_scroll_{i}.png")
        
        # Get all business cards
        cards = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]//a[contains(@href, "maps/place")]')
        print(f"Found {len(cards)} business cards")
        
        for i, card in enumerate(cards[:max_results]):
            try:
                print(f"\nProcessing business {i+1}/{len(cards)}")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1)
                card.click()
                time.sleep(2)
                
                # Debug: Save business page
                driver.save_screenshot(f"4_business_{i}.png")
                
                # Extract details with fallbacks
                name = driver.find_element(By.XPATH, '//h1[contains(@class, "fontHeadlineLarge")]').text
                address = driver.find_element(By.XPATH, '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]').text
                
                # Phone extraction with multiple attempts
                phone = None
                for attempt in range(2):
                    try:
                        phone_elem = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "phone")]')
                        phone = phone_elem.text.split('\n')[-1]
                        break
                    except:
                        pass
                
                # Rating extraction
                try:
                    rating = float(driver.find_element(
                        By.XPATH, '//div[@aria-label*="stars"]').get_attribute("aria-label").split()[0])
                except:
                    rating = None
                
                results.append({
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "rating": rating
                })
                
            except Exception as e:
                print(f"Error processing business {i+1}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        driver.quit()
    
    print(f"\nScraping complete. Found {len(results)} valid results")
    return results