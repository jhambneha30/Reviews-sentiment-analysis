import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# Define BestBuy product review URL
product_url = "https://www.bestbuy.ca/en-ca/product/dyson-v15-detect-extra-cordless-stick-vacuum-yellow-nickel-only-at-best-buy/17183902/review"

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
###driver = webdriver.Chrome(ChromeDriverManager().install())

# Open the product review page
driver.get(product_url)
# Wait for reviews section to load
time.sleep(4)

FILTER_NAME = "lowestRating" # Mix of different filtered reviews for a balanced dataset
MAX_SHOW_MORE_CLICKS = 6 # Maximum number of 'Show more' clicks to load more reviews
## Note: Each show more loads 10 reviews

def get_review_id(review_element):
    try:
        # Method 1: Use reviewer + date
        reviewer = review_element.find_element(By.CSS_SELECTOR, ".author_20vgR span span").text
        date = review_element.find_element(By.CSS_SELECTOR, "[data-date]").get_attribute("data-date").split("T")[0]
        return f"{reviewer}_{date}"
    
    except Exception:
        # Fallback: Use timestamp
        return review_element.find_element(By.CSS_SELECTOR, "[data-date]").get_attribute("data-date")


def get_reviews(driver):
    try:
        # First try to close any cookie banner if present
        try:
            # cookie_banner = WebDriverWait(driver, 2).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
            # )
            close_button = driver.find_element(By.CSS_SELECTOR, ".onetrust-close-btn-handler, .onetrust-close-btn-ui, .banner-close-button, .ot-close-icon")
            close_button.click()
            print("Closed cookie banner")
        except:
            pass  # No cookie banner found

        ## Use filters such as "Most Helpful," "Newest," etc. to refine the review extraction process
        # Define filter mapping for dropdown
        filter_mapping = {
            "Most_Relevant": "relevancy",
            "Most_Helpful": "helpfulness",
            "Newest": "newest",
            "Highest_Rating": "highestRating",
            "Lowest_Rating": "lowestRating"
        }
        
        try:
            # Wait for dropdown to be present
            sort_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "Sort"))
            )
            
            # Scroll to the dropdown
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_dropdown)
            time.sleep(0.5)
            
            # Create Select object
            select = Select(sort_dropdown)
            
            # Apply the filter using value attribute
            select.select_by_value(filter_mapping[FILTER_NAME])
            
            print(f"Applied filter: {FILTER_NAME}")
        except TimeoutException:
            print("Timeout waiting for sort dropdown")
        
        
        show_more_selector = "[data-automation='load-more-button'] div button"
        loaded_reviews = set()  # Track unique reviews to detect when loading stops
        
        for click_attempt in range(MAX_SHOW_MORE_CLICKS):
            try:

                # Scroll until button is visible (with dynamic adjustment)
                button_visible = False
                scroll_attempts = 0
                max_scroll_attempts = 10
                
                while not button_visible and scroll_attempts < max_scroll_attempts:
                    # Get current reviews count before scrolling
                    current_reviews = driver.find_elements(By.CSS_SELECTOR, "div[class^='reviewItem']")
                    
                    # Scroll down (smaller increments work better)
                    driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(0.5)  # Shorter wait between scrolls
                    
                    try:
                        # Check if button is now clickable
                        show_more_btn = WebDriverWait(driver, 1).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, show_more_selector))
                        )
                        button_visible = True
                    except:
                        scroll_attempts += 1
                        
                        # If we've scrolled too far, scroll back up a bit
                        if scroll_attempts > max_scroll_attempts/2:
                            driver.execute_script("window.scrollBy(0, -200);")
                            time.sleep(0.3)
                
                if not button_visible:
                    print("Button not found after scrolling - may have reached end")
                    break
                    
                # Scroll button into center view (more reliable than just into view)
                driver.execute_script("""
                    arguments[0].scrollIntoView({
                        behavior: 'auto',
                        block: 'center',
                        inline: 'center'
                    });
                """, show_more_btn)
                
                # Click using ActionChains for better reliability
                ActionChains(driver).move_to_element(show_more_btn).pause(0.5).click().perform()
                print(f"Clicked 'Show more' ({click_attempt + 1}/{MAX_SHOW_MORE_CLICKS})")
                
                # Wait for new content to load
                # WebDriverWait(driver, 5).until(
                #     lambda d: len(d.find_elements(By.CSS_SELECTOR, "div[class^='reviewItem']")) > len(current_reviews)
                # )
                # time.sleep(1)  # Additional stabilization time
                            
            except Exception as e:
                print(f"Error during click attempt {click_attempt + 1}: {str(e)}")
                break

        # Now wait for reviews to load (modify this selector as needed)
        reviews_ul = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[class^='reviewListWrapper']"))
        )
        review_elements = reviews_ul.find_elements(By.CSS_SELECTOR, "li[class^='review_']")
        print("✅ Reviews section found!")
        
        print(f"Found {len(review_elements)} reviews")
        
        review_data = []
        for review in review_elements:
            review_id = get_review_id(review)
            print(f"Review ID: {review_id}")
            rating_text = review.find_element(By.CSS_SELECTOR, "p.sr-only").text
            # Example output: "Customer rating: 5 out of 5 stars"
            rating = int(rating_text.split(":")[1].split("out")[0].strip())  # Extracts "5"
            print("star rating is:", rating)
            review_data.append({
                "review_ID": review_id,
                "rating": rating,
                "title": review.find_element(By.CSS_SELECTOR, "[class^='reviewTitle'] span").text,
                "review_content": review.find_element(By.CSS_SELECTOR, "[class^='reviewContent'] p span").text,
                "reviewer": review.find_element(By.CSS_SELECTOR, "[class^='author'] span span span").text,
                "posted_date": review.find_element(By.CSS_SELECTOR, "[class^='locationAndTime']").get_attribute("data-date")
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
df.to_csv(f"bestbuy_reviews_{FILTER_NAME}.csv", index=False)

# Close WebDriver
driver.quit()
print(f"Scraping completed. Data saved to bestbuy_reviews_{FILTER_NAME}.csv.")

