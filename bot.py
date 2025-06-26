import tweepy
import time
import get_creds


# Load environment variables
get_creds.load_env_from_file()

# Get credentials
creds = get_creds.get_api_credentials()

#geting client 
if creds:
    client = tweepy.Client(
        bearer_token=creds['BEARER_TOKEN'],
        consumer_key=creds['API_KEY'],
        consumer_secret=creds['API_SECRET'],
        access_token=creds['ACCESS_TOKEN'],
        access_token_secret=creds['ACCESS_TOKEN_SECRET']
    )
else:
    print("❌ Cannot initialize credentials")
    exit(1)

# Create tweet function
def create_tweet(text, client=client):
    """Creates a tweet safely with error handling"""
    try:
        client.create_tweet(text=text)
        print("✅ Tweet sent successfully")
    except tweepy.errors.TooManyRequests:
        print("⚠️ Tweet limit reached")
    except tweepy.errors.Forbidden:
        print("❌ You don't have permission to create tweets")
    except Exception as e:
        print(f"❌ Error creating tweet: {e}")
#search tweets with a query inside of x
def search_tweets(query, max_results=10):
    """Searches for tweets with error handling"""
    try:
        print(f"🔍 Searching: {query}")
        tweets = client.search_recent_tweets(query=query, max_results=max_results)
        
        if tweets and tweets.data:
            print(f"✅ {len(tweets.data)} tweets found:")
            for i, tweet in enumerate(tweets.data, 1):
                text = tweet.text.replace('\n', ' ')[:100]
                print(f"  {i}. {text}...")
            return tweets.data
        else:
            print("ℹ️ No tweets found")
            return None
            
    except tweepy.errors.TooManyRequests:
        print("⚠️ API limit reached. Wait 15 minutes")
        return None
    except Exception as e:
        print(f"❌ Search error: {e}")
        return None


# # Execute the search
# if __name__ == "__main__":
#     # # Create a tweet
#     # create_tweet("🤖 Bot working!", client)
    
#     # # Search tweets
#     # tweets_found = search_tweets("news lang:en -is:retweet", 10)