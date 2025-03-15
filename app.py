from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uvicorn
from instagram import scrape_instagram_posts
from selenium.webdriver.common.action_chains import ActionChains


# Load environment variables
load_dotenv()

# FastAPI App
app = FastAPI()

# Global Selenium WebDriver (to be initialized at startup)
driver = None


# ✅ *Startup: Initialize WebDriver & Login*
@app.on_event("startup")
async def startup_event():
    global driver
    
    # Load credentials from environment variables
    FB_EMAIL = os.getenv("FB_EMAIL")
    FB_PASSWORD = os.getenv("FB_PASSWORD")

    if not FB_EMAIL or not FB_PASSWORD:
        raise ValueError("Facebook credentials are missing! Set FB_EMAIL and FB_PASSWORD in .env")

    # Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Required for headless mode on some systems
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.facebook.com/")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        ).send_keys(FB_EMAIL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "pass"))
        ).send_keys(FB_PASSWORD)

        # Click login button
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "login"))
        ).click()

        time.sleep(60)

        print("✅ Facebook login successful!")

    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.quit()
        raise HTTPException(status_code=500, detail="Facebook login failed")


# ✅ *POST Route: Scrape Multiple Facebook Profiles*
class ScrapeRequestFB(BaseModel):
    urls: list[str]  # List of Facebook profile URLs


@app.post("/scrape")
async def scrape_facebook(request: ScrapeRequestFB):
    global driver
    if driver is None:
        raise HTTPException(status_code=500, detail="WebDriver is not initialized!")

    results = {}

    for url in request.urls:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        time.sleep(3)  # Allow page to fully render
        with open("page_source.txt", "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        try:
            # Extract profile name and image first
            profile_info = {
                "name": "",
                "profile_image": ""
            }

            # Extract profile name
            try:
                # Look for the profile name in h1 tags
                name_elements = driver.find_elements(By.XPATH, "//h1[contains(@class, 'x1qlqyl8') or contains(@class, 'xvs91rp')]")
                if name_elements:
                    profile_info["name"] = name_elements[0].text.strip()
                else:
                    # Alternative selectors for profile name
                    name_elements = driver.find_elements(
                        By.XPATH, "//span[contains(@class, 'x1heor9g') or contains(@class, 'xsgj6o6')]//span"
                    )
                    if name_elements:
                        profile_info["name"] = name_elements[0].text.strip()
            except Exception as e:
                print(f"Error extracting profile name: {e}")
            
            
            # Extract profile image
            try:
                # Find all divs with class 'x15sbx0n'
                profile_divs = driver.find_elements(By.CLASS_NAME, "x15sbx0n")
                
                if profile_divs:
                    first_profile_div = profile_divs[0]  # Select the first div
                    
                    # Try extracting <image> inside <svg>
                    profile_img_element = first_profile_div.find_elements(By.TAG_NAME, "image")
                    for img in profile_img_element:
                        src = img.get_attribute("xlink:href")
                        if src and "scontent" in src:  # Ensure it's a valid profile picture
                            profile_info["profile_image"] = src
                            break  # Stop once we get the first valid image
                    
                    # If no <image> found, try extracting from <img> inside the div
                    if not profile_info["profile_image"]:
                        img_elements = first_profile_div.find_elements(By.TAG_NAME, "img")
                        for img in img_elements:
                            src = img.get_attribute("src")
                            if src and "scontent" in src:
                                profile_info["profile_image"] = src
                                break  # Stop once we get the first valid image

            except Exception as e:
                print(f"Error extracting profile image: {e}")



            set_posts = set()
            set_images = set()

            # Click "See more" buttons
            try:
                see_more_buttons = driver.find_elements(
                    By.XPATH, "//div[@role='button' and contains(text(), 'See more')]"
                )
                print(f"Found {len(see_more_buttons)} 'See more' buttons")
                
                for button in see_more_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1.5)
                    except Exception as e:
                        print(f"Failed to click 'See more' button: {e}")
            except Exception as e:
                print(f"Error finding 'See more' buttons: {e}")

            time.sleep(2)  # Allow expanded content to load

            # Find top-level post containers - look for elements that are more likely to be complete posts
            try:
                # Try to find the most top-level containers that represent full posts
                post_selectors = [
                    # Look for elements with data-ad-preview attribute (from your HTML sample)
                    "//div[@data-ad-comet-preview='message' or @data-ad-preview='message']",
                    "//div[contains(@class, 'x1lliihq') and contains(@class, 'x6ikm8r')]/div[contains(@class, 'x78zum5')]"
                ]
                
                all_post_containers = []
                for selector in post_selectors:
                    containers = driver.find_elements(By.XPATH, selector)
                    all_post_containers.extend(containers)
                    print(f"Found {len(containers)} containers with selector: {selector}")
                
                # If we didn't find any posts with the above selectors, fall back to more general approach
                if not all_post_containers:
                    # Look for divs that contain the text containers but aren't deeply nested
                    all_post_containers = driver.find_elements(
                        By.XPATH, "//div[.//div[contains(@class, 'x11i5rnm')]][count(ancestor::div) < 20]"
                    )
                    print(f"Using fallback selector, found {len(all_post_containers)} containers")
                
                # Process each post container
                processed_post_count = 0
                for container in all_post_containers:
                    try:
                        # Extract all text from this container
                        all_text = container.text.strip()
                        
                        # Clean up the text - remove UI elements text
                        text_to_remove = ["See more", "See original", "See translation", "Translate", "Like", "Comment", "Share"]
                        clean_text = all_text
                        
                        for remove_text in text_to_remove:
                            clean_text = clean_text.replace(remove_text, "")
                        
                        # Split by newlines and rejoin to clean up formatting
                        text_parts = [part.strip() for part in clean_text.split('\n') if part.strip()]
                        clean_text = " ".join(text_parts)
                        
                        # Only add if we have meaningful content
                        if clean_text and len(clean_text) > 10:  # Avoid very short snippets
                            set_posts.add(clean_text)
                            processed_post_count += 1
                            print(f"Processed post {processed_post_count}: {clean_text[:50]}...")
                    except Exception as e:
                        print(f"Error extracting text from container: {e}")
            except Exception as e:
                print(f"Error finding post containers: {e}")

            # Extract images
            try:
                # Find the parent div with the specific class where images are located
                post_image_containers = driver.find_elements(By.CLASS_NAME, "x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z")
                print(f"length of image container {len(post_image_containers)}")
                for container in post_image_containers:
                    # Extract images only from this div
                    image_elements = container.find_elements(By.XPATH, ".//img")

                    for img in image_elements:
                        try:
                            src = img.get_attribute("src")
                            if src and "scontent" in src and not src.endswith(".svg"):
                                set_images.add(src)
                        except Exception as e:
                            print(f"Error extracting image src: {e}")
            except Exception as e:
                print(f"Error finding images within the specified div: {e}")

            # Create the result structure for this URL
            url_result = {
                "profile": profile_info,
                "posts": list(set_posts),
                "images": list(set_images)
            }
            
            results[url] = url_result
            
            print(f"Extracted profile info: {profile_info['name']}, {len(set_posts)} posts and {len(set_images)} images from {url}")
            
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            results[url] = {
                "profile": {"name": "", "profile_image": ""},
                "posts": [],
                "images": []
            }

    return {
        "status": "success", 
        "results": results
    }


class ScrapeRequest(BaseModel):
    urls: list[str]  # Accept multiple Instagram profile URLs


class ScrapeResponse(BaseModel):
    message: str
    data: dict[str, dict[str, str]]  # Mapping of username -> {text, url}


@app.post("/instagram", response_model=ScrapeResponse)
async def scrape_instagram(request: ScrapeRequest):
    result = scrape_instagram_posts(request.urls)
    return ScrapeResponse(
        message="Scraping task completed",
        data=result
    )

@app.on_event("shutdown")
async def shutdown_event():
    await driver.quit()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)