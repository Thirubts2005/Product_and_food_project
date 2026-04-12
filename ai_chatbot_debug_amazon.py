import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_amazon(product):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    
    driver.get("https://www.amazon.in/")
    time.sleep(2)
    try:
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_box.send_keys(product)
        search_box.send_keys(Keys.ENTER)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        
        data = []
        for item in items[:5]: # top 5
            try:
                title = item.find_element(By.CSS_SELECTOR, "h2 a span").text
                price = item.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                try:
                    old_price = item.find_element(By.CSS_SELECTOR, ".a-text-price span[aria-hidden='true']").text
                except:
                    old_price = ""
                image = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
                
                data.append({"Platform": "Amazon", "Product": title, "Price": "₹" + price, "Old Price": old_price, "Delivery": "Standard", "Extra": "", "Image": image})
            except Exception as e:
                continue
        return pd.DataFrame(data)
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    df = scrape_amazon("usb c cable")
    print(df)
