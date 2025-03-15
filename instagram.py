
import re
from instagram_posts_scraper.instagram_posts_scraper import InstaPeriodScraper
import pandas as pd

def extract_username(profile_url):
    """Extracts the username from a given Instagram profile URL."""
    match = re.search(r"instagram\.com/([^/?]+)", profile_url)
    return match.group(1) if match else None

profile_urls = [
    "https://www.instagram.com/kaicenat/",
    "https://www.instagram.com/nasa/",
    "https://www.instagram.com/__meaningfull__quotes/"
]

def scrape_instagram_posts(profile_urls):
    """
    Scrapes the latest Instagram posts from a list of profile URLs and returns
    a dictionary mapping each username to a dictionary containing the latest post text and image URL.
    """
    results = {}
    ig_posts_scraper = InstaPeriodScraper()

    for profile_url in profile_urls:
        username = extract_username(profile_url)
        
        if username:
            target_info = {"username": username, "days_limit": 1}  
            res = ig_posts_scraper.get_posts(target_info=target_info)
            
            if res and 'data' in res and res['data']:
                latest_post = res['data'][0]  
                
                post_content = latest_post.get('sum', 'No content available')
                post_image_url = latest_post.get('pic', 'No image URL available')
                results[username] = {"text": post_content, "url": post_image_url}
            else:
                results[username] = {"text": None, "url": None}
        else:
            
            results[profile_url] = {"text": None, "url": None}
    
    return results

if __name__ == "__main__":
    posts = scrape_instagram_posts(profile_urls=profile_urls)
    for username, post in posts.items():
        print(f"{username}: {post}")
