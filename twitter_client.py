import tweepy
import time
import get_creds
import re
import company_analyzer as ca

class TwitterClient:
    def __init__(self):
        """Initialize Twitter client with credentials"""
        # Load environment variables
        get_creds.load_env_from_file()
        
        # Get credentials
        self.creds = get_creds.get_api_credentials()
        
        # Initialize client
        if self.creds:
            self.client = tweepy.Client(
                bearer_token=self.creds['BEARER_TOKEN'],
                consumer_key=self.creds['API_KEY'],
                consumer_secret=self.creds['API_SECRET'],
                access_token=self.creds['ACCESS_TOKEN'],
                access_token_secret=self.creds['ACCESS_TOKEN_SECRET']
            )
        else:
            print("❌ Cannot initialize credentials")
            raise Exception("Failed to initialize Twitter credentials")
    
    def create_tweet(self, text):
        """Creates a tweet safely with error handling"""
        try:
            self.client.create_tweet(text=text)
            print("✅ Tweet sent successfully")
            return True
        except tweepy.errors.TooManyRequests:
            print("⚠️ Tweet limit reached")
            return False
        except tweepy.errors.Forbidden:
            print("❌ You don't have permission to create tweets")
            return False
        except Exception as e:
            print(f"❌ Error creating tweet: {e}")
            return False
    
    def search_tweets(self, query, max_results):
        """Search tweets with a query inside of X"""
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'author_id', 'text'],  # Specify fields to return
                max_results=max_results  # Number of tweets to retrieve (10-100 per request)
            )
          
            # Process the results
            tweets_results = {}
            title = 'no title'
            
            if tweets and tweets.data:
                for tweet in tweets.data:
                    aux = {
                        'title': title, 
                        "summary": tweet.text,
                        "provider": tweet.author_id
                    }
                    tweets_results[tweet.id] = aux
                
            return tweets_results
            
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def clean_tweet(self, text):
        """Function to clean tweet text"""
        text = re.sub(r'http\S+', '', text)  # Remove URLs
        text = re.sub(r'@\w+', '', text)    # Remove mentions
        text = re.sub(r'#\w+', '', text)    # Remove hashtags
        text = text.strip().lower()         # Convert to lowercase
        return text
    
    def search_tweets_cleaned(self, query, max_results):
        """Search tweets and return cleaned text"""
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=['created_at', 'author_id', 'text'],
                max_results=max_results
            )
          
            tweets_results = {}
            title = 'no title'
            
            if tweets and tweets.data:
                for tweet in tweets.data:
                    cleaned_text = self.clean_tweet(tweet.text)
                    aux = {
                        'title': title, 
                        "summary": cleaned_text,
                        "provider": tweet.author_id
                    }
                    tweets_results[tweet.id] = aux
                
            return tweets_results
            
        except Exception as e:
            print(f"Error: {e}")
            return {}
        
    def post_company_analysis(self,company_name):
        """Get analysis for a company and post it to Twitter"""
    
        print(f"📊 Getting analysis for {company_name}...")
    
        # Get the formatted analysis
        analysis = ca.get_company_analysis(company_name)
    
        # Post to Twitter
        print("📤 Posting to Twitter...")
        self.create_tweet(analysis)
    
        print("✅ Done!")
        return analysis



