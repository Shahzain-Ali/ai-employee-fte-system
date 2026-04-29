"""Quick test: Post a tweet using Twitter/X Official API (OAuth 1.0a)."""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Read credentials from .env
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_secret = os.getenv("TWITTER_ACCESS_SECRET")

# Validate
missing = []
if not api_key: missing.append("TWITTER_API_KEY")
if not api_secret: missing.append("TWITTER_API_SECRET")
if not access_token: missing.append("TWITTER_ACCESS_TOKEN")
if not access_secret: missing.append("TWITTER_ACCESS_SECRET")

if missing:
    print(f"ERROR: Missing env vars: {', '.join(missing)}")
    print("Add them to your .env file first.")
    exit(1)

# Authenticate with Twitter API v2
client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret,
)

# Post a test tweet
tweet_text = "Hello from FTE AI Employee! 🤖 Testing official Twitter/X API integration. #AIEmployee #Hackathon"

try:
    response = client.create_tweet(text=tweet_text)
    tweet_id = response.data["id"]
    print(f"SUCCESS! Tweet posted!")
    print(f"Tweet ID: {tweet_id}")
    print(f"URL: https://x.com/i/status/{tweet_id}")
except tweepy.TweepyException as e:
    print(f"FAILED: {e}")