import tweepy
import time
import get_creds
import re


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
        print("⚠️ Tweet l~imit reached")
    except tweepy.errors.Forbidden:
        print("❌ You don't have permission to create tweets")
    except Exception as e:
        print(f"❌ Error creating tweet: {e}")
        
#search tweets with a query inside of x
def search_tweets(query, max_r,client=client):
    # Search recent tweets (last 7 days)
    try:
        tweets = client.search_recent_tweets(
            query=query,
            tweet_fields=['created_at', 'author_id', 'text'],  # Specify fields to return
            max_results=max_r # Number of tweets to retrieve (10-100 per request),
        )
      
        # Process the results
        tweets_results={}
        aux={}
        title='no title'
        for tweet in tweets.data:
            aux={'title':title, "summary": tweet.text,"provider":tweet.author_id}
            tweets_results[tweet.id]=aux
            aux={}
        return tweets_results
    except Exception as e:
        print(f"Error: {e}")
   #news will be a dict {title: "lalal", summary: "llalal", provider:"lalal"}


# Function to clean tweet text
def clean_tweet(text):
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'@\w+', '', text)    # Remove mentions
    text = re.sub(r'#\w+', '', text)    # Remove hashtags
    text = text.strip().lower()         # Convert to lowercase
    return text

def main():
    query_tesla = 'Tesla OR TSLA OR "Model 3" OR "Model Y" OR Cybertruck -is:retweet  -from:teslapromo -discount -sale lang:en ' 
    example=search_tweets(query_tesla,50,client)
    print(len(example))
main()