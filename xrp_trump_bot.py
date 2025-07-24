
import time
import requests
import html
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# ======== CONFIGURATION ========
TELEGRAM_TOKEN = "7591942021:AAEUGrEjejo8O8BaxXwhlap5t_qt4-KlCe8"
TELEGRAM_CHAT_ID = None  # Will be auto-filled after first use
CHECK_INTERVAL_SECONDS = 300  # 5 minutes

TRUMP_TWITTER_USERNAME = "realDonaldTrump"
TRUMP_TRUTH_SOCIAL_URL = "https://truthsocial.com/@realDonaldTrump"

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)

# ========== TELEGRAM ==========
def send_telegram_message(message):
    global TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if TELEGRAM_CHAT_ID:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    else:
        # Auto-discovery of first user
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates").json()
        if updates["ok"] and updates["result"]:
            TELEGRAM_CHAT_ID = updates["result"][-1]["message"]["chat"]["id"]
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        else:
            logging.warning("No chat ID found yet. Start the bot by sending it a message.")
            return
    requests.post(url, data=payload)

# ========== TWITTER CHECK ==========
def check_twitter_for_xrp(last_seen_id=None):
    try:
        url = f"https://nitter.net/{TRUMP_TWITTER_USERNAME}"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        tweets = soup.select(".timeline-item")
        for tweet in tweets:
            content = tweet.select_one(".tweet-content").text.strip().lower()
            tweet_id = tweet["data-id"]
            if "xrp" in content and (last_seen_id is None or tweet_id != last_seen_id):
                logging.info("XRP mentioned on Twitter!")
                send_telegram_message(f"🐦 טראמפ צייץ על XRP:\n\n{content[:280]}")
                return tweet_id
    except Exception as e:
        logging.error(f"Error checking Twitter: {e}")
    return last_seen_id

# ========== TRUTH SOCIAL CHECK ==========
def check_truth_social_for_xrp(last_seen_texts):
    try:
        resp = requests.get(TRUMP_TRUTH_SOCIAL_URL, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        posts = soup.select("div.status__content")
        new_last_seen = last_seen_texts.copy()
        for post in posts:
            text = post.text.strip().lower()
            if "xrp" in text and text not in last_seen_texts:
                logging.info("XRP mentioned on Truth Social!")
                send_telegram_message(f"🟣 טראמפ פרסם על XRP ב-Truth Social:\n\n{text[:280]}")
                new_last_seen.append(text)
        return new_last_seen[-5:]  # keep last 5 to avoid duplicates
    except Exception as e:
        logging.error(f"Error checking Truth Social: {e}")
    return last_seen_texts

# ========== MAIN LOOP ==========
def main():
    logging.info("Starting XRP alert bot...")
    twitter_last_id = None
    truth_seen_posts = []
    while True:
        twitter_last_id = check_twitter_for_xrp(twitter_last_id)
        truth_seen_posts = check_truth_social_for_xrp(truth_seen_posts)
        logging.info(f"Sleeping for {CHECK_INTERVAL_SECONDS} seconds...")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
