import os
from facebook_page_scraper import Facebook_scraper
from chromedriver_py import binary_path
import logging
import traceback

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

profile_url = "Meta"
posts_count = 10
browser = "chrome"
proxy = "http://IP:PORT"
timeout = 600
headless = True

fb_email = os.getenv('FB_EMAIL')
fb_password = os.getenv('FB_PASSWORD')

if not fb_email or not fb_password:
    logging.error("🚨 FB_EMAIL or FB_PASSWORD is missing! Check your environment variables.")
    exit(1)


email = fb_email
password=fb_password

meta_ai = Facebook_scraper(
    profile_url,
    posts_count=posts_count,
    browser=browser,
    proxy=proxy,
    timeout=timeout,
    headless=headless,
    )

meta_ai.chrome_driver_path = binary_path

try:
    logging.info("🔍 Starting Facebook Scraper...")
    json_data = meta_ai.scrap_to_json()

    if not json_data:
        logging.warning("⚠️ No posts found! Possible reasons: login required, private profile, or scraper issue.")
    else:
        logging.info(f"✅ Scraped {len(json_data)} posts.")

        if isinstance(json_data, list):
            all_posts_length = len(json_data)
            logging.info(f"📌 Total posts: {all_posts_length}")

            for post_data in json_data:
                post_url = post_data.get("post_url", None)
                if post_url:
                    logging.info(f"🌐 Found post URL: {post_url}")
                else:
                    logging.warning("⚠️ No post_url found, skipping.")

        elif isinstance(json_data, dict):
            all_posts_length = len(json_data)
            logging.info(f"📌 Total posts: {all_posts_length}")

            for post_id, post_data in json_data.items():
                post_url = post_data.get("post_url", None)
                if post_url:
                    logging.info(f"🌐 Found post URL: {post_url}")
                else:
                    logging.warning(f"⚠️ No post_url for post {post_id}, skipping.")

except Exception as e:
    logging.error(f"🚨 Scraping Failed: {e}")
    logging.error(traceback.format_exc())
