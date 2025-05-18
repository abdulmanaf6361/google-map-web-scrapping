from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
import time

# Setup WebDriver
service = Service('C:/Users/Abdul Manaf/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe')
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=service, options=options)

# Open Google Maps page
url = "https://www.google.co.in/maps/place/Shwana+Pet+Clinic/@13.1217572,77.5898406,14z/data=!4m10!1m2!2m1!1spet+clinic+near+me!3m6!1s0x3bae19ad38610e81:0x5067d466726ebdd0!8m2!3d13.1217572!4d77.6227996!15sChJwZXQgY2xpbmljIG5lYXIgbWUiA5ABAVoUIhJwZXQgY2xpbmljIG5lYXIgbWWSAQx2ZXRlcmluYXJpYW6qAVQKCC9tLzA2OGh5EAEqDiIKcGV0IGNsaW5pYygAMh4QASIaHvZYK3VqsIHwS8AdTGDbv4rD0pIkwA2tPLUyFhACIhJwZXQgY2xpbmljIG5lYXIgbWXgAQA!16s%2Fg%2F11ryhn89xf?entry=ttu&g_ep=EgoyMDI1MDUxMy4xIKXMDSoASAFQAw%3D%3D"
driver.get(url)
time.sleep(10)  # Initial page load

def click_reviews_button():
    try:
        # Try alternative selectors if the primary one fails
        selectors = [
            "//button[contains(@aria-label, 'reviews')]",
            "//button[contains(., 'Reviews')]",
            "//button[contains(@jsaction, 'reviews')]"
        ]
        
        for selector in selectors:
            try:
                reviews_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                reviews_button.click()
                print("Clicked reviews button successfully")
                time.sleep(5)  # Wait for reviews to load
                return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        print("Could not find reviews button with any selector")
        return False
    except Exception as e:
        print(f"Error clicking reviews button: {str(e)}")
        return False

def scroll_reviews_pane(target_count=100):
    try:
        # Wait for the reviews pane to load
        scroll_div = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'm6QErb') and contains(@class, 'DxyBCb')]"))
        )
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_div)
        review_elements = []
        attempts = 0
        max_attempts = 50
        
        while len(review_elements) < target_count and attempts < max_attempts:
            # Scroll to bottom
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scroll_div)
            time.sleep(3)  # Wait for new reviews to load
            
            # Get current reviews
            try:
                review_elements = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
                print(f"Found {len(review_elements)} reviews so far...")
            except StaleElementReferenceException:
                print("Stale element reference, retrying...")
                time.sleep(2)
                continue
            
            # Check if we've reached the end
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_div)
            if new_height == last_height:
                attempts += 1
                print(f"No new reviews loaded, attempt {attempts}/{max_attempts}")
                # Try clicking any "More reviews" button if available
                try:
                    more_reviews_btn = driver.find_element(By.XPATH, "//button[contains(., 'More reviews')]")
                    driver.execute_script("arguments[0].click();", more_reviews_btn)
                    time.sleep(3)
                except:
                    pass
            else:
                attempts = 0
                last_height = new_height
                
        return True
    except Exception as e:
        print(f"Error scrolling reviews: {str(e)}")
        return False

def expand_all_reviews():
    try:
        # First wait for some reviews to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jftiEf'))
        )
        
        # Find and click all "More" buttons
        max_retries = 3
        for retry in range(max_retries):
            try:
                more_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'w8nwRe') and contains(@class, 'kyuRq')]")
                print(f"Found {len(more_buttons)} 'More' buttons to expand (attempt {retry + 1})")
                
                for btn in more_buttons:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", btn)
                        time.sleep(0.3)  # Small delay
                    except:
                        continue
                return True
            except StaleElementReferenceException:
                print("Stale elements during expansion, retrying...")
                time.sleep(2)
                continue
        
        return False
    except Exception as e:
        print(f"Error expanding reviews: {str(e)}")
        return False

def extract_reviews():
    try:
        reviews = driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
        review_data = []
        
        for review in reviews:
            try:
                # Get the review text
                text_element = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd')
                review_text = text_element.text
                
                # Get the rating if available
                rating = None
                try:
                    rating_element = review.find_element(By.CSS_SELECTOR, 'span.kvMYJc')
                    rating = rating_element.get_attribute('aria-label')
                except:
                    pass
                
                if review_text.strip():
                    review_data.append({
                        'Review': review_text,
                        'Rating': rating
                    })
            except Exception as e:
                print(f"Error processing a review: {str(e)}")
                continue
                
        return review_data
    except Exception as e:
        print(f"Error extracting reviews: {str(e)}")
        return []

# Main execution
try:
    if click_reviews_button():
        if scroll_reviews_pane(1000):
            if expand_all_reviews():
                reviews_data = extract_reviews()
                
                # Save to CSV
                df = pd.DataFrame(reviews_data)
                df.to_csv("deep_other_full_reviews.csv", index=False, encoding='utf-8')
                print(f"Successfully extracted {len(reviews_data)} reviews.")
            else:
                print("Failed to expand all reviews")
        else:
            print("Failed to scroll reviews pane")
    else:
        print("Failed to click reviews button")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
finally:
    driver.quit()