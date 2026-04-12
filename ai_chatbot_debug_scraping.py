import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_scrape(product):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Navigating to https://quickcompare.in/ ...")
        driver.get("https://quickcompare.in/")
        driver.save_screenshot("step1_initial.png")
        
        print("Looking for search input...")
        search_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Search']"))
        )
        print("Found search input. Typing...")
        search_input.send_keys(product)
        time.sleep(2)
        driver.save_screenshot("step2_typed.png")
        
        print("Pressing ENTER...")
        search_input.send_keys(Keys.ENTER)
        
        print("Waiting for results (₹ symbol)...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'₹')]"))
            )
            print("Found ₹ symbol. Results loaded.")
        except Exception as e:
            print(f"Timeout waiting for ₹ symbol. Current URL: {driver.current_url}")
            driver.save_screenshot("error_timeout.png")
            # Maybe we need to click "See All" or something?
            return pd.DataFrame({"Error": [f"Timeout: {str(e)}"]})

        driver.save_screenshot("step3_results.png")
        
        print("Finding product cards...")
        # Try both the original and the new selector
        cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'rounded-md') and contains(@class, 'hover:shadow-md')]")
        print(f"Found {len(cards)} cards using original selector.")
        
        if len(cards) == 0:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.grid > div")
            print(f"Found {len(cards)} cards using 'div.grid > div' selector.")

        data = []
        for i, p_card in enumerate(cards):
            try:
                # Try to extract title to see if it's a valid card
                title = "Unknown"
                try:
                    title = p_card.find_element(By.CSS_SELECTOR, ".line-clamp-2").text
                except:
                    try:
                        title = p_card.text.split('\n')[0]
                    except:
                        pass
                
                print(f"Card {i}: {title[:30]}...")
                
                # ... existing logic or simplified for debug ...
            except:
                continue
                
        return pd.DataFrame(data)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.save_screenshot("final_error.png")
        return pd.DataFrame({"Error": [str(e)]})
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_scrape("milk")
