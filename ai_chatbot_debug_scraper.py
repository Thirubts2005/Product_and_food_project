from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=options)

driver.get("https://quickcompare.in/")  # Note: loading the home page to start fresh

try:
    # Wait for the search input
    search_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Search']"))
    )
    
    search_input.send_keys("milk")
    time.sleep(1)
    search_input.send_keys(Keys.ENTER)
    
    print("Sent Enter key, waiting for results...")
    
    # Wait for the cards
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'₹')]"))
    )
    
    cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='rounded-xl']")
    data = []
    for card in cards:
        try:
            platform = card.find_element(By.TAG_NAME, "img").get_attribute("alt")
            price = card.find_element(By.XPATH, ".//span[contains(text(),'₹')]").text
            data.append({
                "Platform": platform,
                "Price": price
            })
        except:
            continue
            
    df = pd.DataFrame(data)
    print(df)

except Exception as e:
    print(f"Error: {e}")
finally:
    driver.save_screenshot('screenshot2.png')
    with open('source2.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    driver.quit()
