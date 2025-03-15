# Facebook Page Scraper

A Python-based Facebook page scraper using `facebook_page_scraper` to extract posts from public pages.

## 🚀 Features
- Scrapes posts from a Facebook page
- Supports login with email and password
- Works with headless Chrome
- Supports proxy usage
- Logs detailed information

## 📌 Requirements
- Python 3.8+
- Google Chrome installed
- ChromeDriver (automatically managed by `chromedriver_py`)

## 📦 Installation
First, clone this repository:

```sh
git clone https://github.com/alihassanml/Facebook-scraping.git
cd Facebook-scraping
```

Then, install the required dependencies:

```sh
pip install -r requirements.txt
```

## 🔑 Setup
Set your Facebook credentials as environment variables:

**Linux/macOS:**
```sh
export FB_EMAIL="your-email"
export FB_PASSWORD="your-password"
```

**Windows (Command Prompt):**
```sh
set FB_EMAIL=your-email
set FB_PASSWORD=your-password
```

Or, you can set them in Python before running the script:
```python
import os
os.environ["FB_EMAIL"] = "your-email"
os.environ["FB_PASSWORD"] = "your-password"
```

## 🛠 Usage
Run the script:
```sh
python scraper.py
```

## 📜 Code Overview

```python
import os
from facebook_page_scraper import Facebook_scraper
from chromedriver_py import binary_path
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Facebook Page Details
profile_url = "Meta"  # Change this to the desired page name or URL
posts_count = 10
browser = "chrome"
proxy = "http://IP:PORT"  # Ensure correct proxy format
timeout = 600
headless = True

# Load Facebook credentials
fb_email = os.getenv('FB_EMAIL')
fb_password = os.getenv('FB_PASSWORD')

if not fb_email or not fb_password:
    logging.error("🚨 FB_EMAIL or FB_PASSWORD is missing! Check your environment variables.")
    exit(1)

# Initialize Scraper
meta_ai = Facebook_scraper(
    profile_url=profile_url,
    posts_count=posts_count,
    browser=browser,
    proxy=proxy,
    timeout=timeout,
    headless=headless,
    email=fb_email,
    password=fb_password
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
            for post_data in json_data:
                logging.info(f"🌐 Found post: {post_data.get('post_url', 'No URL')}")
        elif isinstance(json_data, dict):
            for post_id, post_data in json_data.items():
                logging.info(f"🌐 Found post: {post_data.get('post_url', 'No URL')}")

except Exception as e:
    logging.error(f"🚨 Scraping Failed: {e}")
    logging.error(traceback.format_exc())
```

## 🛠 Troubleshooting
- Ensure **Facebook login credentials** are correct
- **Use a proxy** if you are facing rate-limiting issues
- **Update ChromeDriver** if the script fails due to browser version mismatch
- **Enable debugging logs** by modifying `logging.basicConfig(level=logging.DEBUG)`

## 📜 License
This project is licensed under the MIT License.

## 🤝 Contributing
Pull requests are welcome! Feel free to fork the repo and submit PRs.

## 🌟 Credits
Developed by [Ali Hassan](https://github.com/alihassanml).

