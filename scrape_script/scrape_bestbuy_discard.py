import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Define BestBuy product review URL
product_url = "https://www.bestbuy.ca/en-ca/product/dyson-v15-detect-extra-cordless-stick-vacuum-yellow-nickel-only-at-best-buy/17183902"

# Setup WebDriver with headless option for faster execution
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--disable-blink-features=AutomationControlled") #Disables Chrome's built-in detection of automation tools
## To avoid detetction of an automated script, we can set a user-agent
chrome_options.add_argument("user-agent=Mozilla/5.0")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Set path for ChromeDriver
## https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.165/mac-arm64/chromedriver-mac-arm64.zip
service = Service("/Users/jhambneha/drivers/chromedriver-mac-arm64/chromedriver")  # Update with correct path
driver = webdriver.Chrome(service=service, options=chrome_options) #launch the browser with specified config in chrome options
#driver = webdriver.Chrome(ChromeDriverManager().install())

# Open the product review page
driver.get(product_url)
# Wait for reviews section to load
time.sleep(5)


def get_reviews(driver):
    try:
        # First try to close any cookie banner if present
        try:
            cookie_banner = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
            )
            close_button = driver.find_element(By.CSS_SELECTOR, ".onetrust-close-btn-handler, .onetrust-close-btn-ui, .banner-close-button, .ot-close-icon")
            close_button.click()
            print("Closed cookie banner")
        except:
            pass  # No cookie banner found

        ## 🔄 **Scroll Down Multiple Times to Trigger Lazy Loading**
        scroll_attempts = 4
        for _ in range(scroll_attempts):
            driver.execute_script("window.scrollBy(0, 600);")  # Scroll in increments
            time.sleep(1)
        
        # Locate the reviews button using its data-automation attribute
        reviews_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button#reviews[data-automation='reviews-expandable-button']"))
        )
        # Check if the accordion is collapsed (aria-expanded="false")
        if reviews_button.get_attribute("aria-expanded") == "false":
            print("Reviews section is collapsed. Clicking to expand...")
            
            # Scroll to the button to ensure it's clickable
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reviews_button)
            
            # Click the button to expand reviews
            reviews_button.click()
            
            # Wait for the aria-expanded attribute to change to "true"
            WebDriverWait(driver, 10).until(
                lambda d: reviews_button.get_attribute("aria-expanded") == "true")
            
            print("Reviews section expanded successfully")
        # First, click on Explore more reivews button to go to reviews 
        scroll_attempts = 8
        for _ in range(scroll_attempts):
            driver.execute_script("window.scrollBy(0, 800);")  # Scroll in increments
            time.sleep(1)
        explore_more_reviews_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-automation='pdp-explore-all-reviews-link']"))
        )
        explore_more_reviews_btn.click()
        print("Clicked on 'Explore more reviews' button")

        # Now wait for reviews to load (modify this selector as needed)
        reviews_ul = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[class^='reviewListWrapper']"))
        )
        review_elements = reviews_ul.find_elements(By.CSS_SELECTOR, "li[class^='review_']")
        print("✅ Reviews section found!")
        
        print(f"Found {len(review_elements)} reviews")
        
        review_data = []
        for review in review_elements:
            rating_text = review.find_element(By.CSS_SELECTOR, "p.sr-only").text
            # Example output: "Customer rating: 5 out of 5 stars"
            rating = int(rating_text.split(":")[1].split("out")[0].strip())  # Extracts "5"
            print("star rating is:", rating)
            review_data.append({
                "rating": rating,
                "title": review.find_element(By.CSS_SELECTOR, "[class^='reviewTitle'] span").text,
                "body": review.find_element(By.CSS_SELECTOR, "[class^='reviewContent'] p span").text,
                "author": review.find_element(By.CSS_SELECTOR, "[class^='author'] span span span").text,
                "date": review.find_element(By.CSS_SELECTOR, "[class^='locationAndTime']").get_attribute("data-date")
            })


        return review_data
    except TimeoutException:
        print("Timeout")
    except Exception as e:
        print(f"Error extracting reviews: {str(e)}")
        return []

review_list = get_reviews(driver)
print(f"Found {len(review_list)} reviews!!! Yay!!!")
print(review_list[2])
# Convert list to Pandas DataFrame
df = pd.DataFrame(review_list)

# Save to CSV
df.to_csv("bestbuy_reviews.csv", index=False)

# Close WebDriver
driver.quit()
print("Scraping completed. Data saved to 'bestbuy_reviews.csv'.")

