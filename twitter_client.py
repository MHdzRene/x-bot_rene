import tweepy
import time
import get_creds
import re
from datetime import datetime, timedelta
import working_wjson as wj

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
        #user id
        self.USER_ID = self.client.get_me().data.id 
        # List of promotional accounts (usernames without @)
        # These are the 10 accounts with 10k-30k followers that get free access
        self.promo_accounts = [
            'luci5425','rene_y_sherlyn',
        ]

        # Global cache for subscribers to avoid frequent API calls
        self.subscribers_cache = []
        self.last_update = 0
        # Global set for authorized users (subscribers + promo accounts)
        self.authorized_users =set(wj.load_from_json('data/authorized_users.json')) 

        
    
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
        import company_analyzer as ca
        analysis = ca.get_company_analysis(company_name)
    
        # Post to Twitter
        print("📤 Posting to Twitter...")
        self.create_tweet(analysis)
    
        print("✅ Done!")
        return analysis

    #fix this part to only respond to subcrit [people]
    def load_subscribers(self,user_id):
        """
        Function to load subscribers from X API
        Note: This uses a hypothetical endpoint; check developer.x.com for the exact one
        If the endpoint doesn't exist, you may need to export manually or use alternatives
        """
        try:
            # Hypothetical API call to get subscriptions (adjust based on actual docs)
            # Example: subscribers = client.get_users_subscriptions(id=user_id)
            # For demonstration, assuming it's available; replace with real call
            subscribers_response = self.client.get_users_subscriptions(id=user_id)  # Placeholder
            if subscribers_response.data:
                return [sub['username'] for sub in subscribers_response.data]
            else:
                return []
        except tweepy.TweepyException as e:
            print(f"Error loading subscribers: {e}")
            return []
        
    def get_updated_subscribers(self,user_id):
        """
        Function to get updated subscribers with caching (update every hour)
        """
        if time.time() - self.last_update > 3600:  # 3600 seconds = 1 hour
            self.subscribers_cache = self.load_subscribers(user_id)
            self.last_update = time.time()
        return self.subscribers_cache
    
    def load_authorized(self,user_id):
        """
        Function to load or update authorized users
        """
        subscribers = self.get_updated_subscribers(user_id)
        self.authorized_users = set(subscribers + self.promo_accounts)
        print(self.authorized_users)

    def is_authorized(self,username):
        """Function to check if a username is authorized"""
        return username in self.authorized_users
    #until here
  
    def generate_ai_analysis(self,company_name,ticker):
        # Example: Parse text for stock symbol and return analysis
        # In real implementation, integrate your AI here
        import company_analyzer as ca
        analysis = ca.get_company_analysis(company_name,ticker)
        return f" {analysis} "
    
    def contains_company(self,text):
        # Regex para tickers como $TSLA, $AAPL (1-5 letras uppercase) fix this method
        ticker_pattern = r'\$[A-Z]{1,5}'
        # O nombres comunes (agrega más si quieres)
        company_names = ['Tesla', 'Apple', 'Amazon', "Alphabet", 'Microsoft','Nvidia']  # Expande esta lista
        if re.search(ticker_pattern, text):
            return True #fix to obten ticker 
        for name in company_names:
            if name.lower() in text.lower():
                return name
        return None
    
    def extract_ticker_from_text(self, text):
        """
        Extrae el ticker exacto que escribió el usuario en el texto
        
        Args:
            text (str): El texto donde buscar el ticker
            
        Returns:
            str: El ticker encontrado (sin el símbolo $) o None si no encuentra nada
        """
        # Regex para tickers como $TSLA, $AAPL (1-5 letras uppercase)
        ticker_pattern = r'\$([A-Z]{1,5})'
        
        # Buscar ticker pattern ($TSLA, $AAPL, etc.)
        ticker_match = re.search(ticker_pattern, text)
        if ticker_match:
            return ticker_match.group(1)  # Devuelve solo el ticker sin el $ (ej: "TSLA")
        
        return None

     #Nuevo método para monitorizar y responder mentions

    def monitor_and_respond_mentions(self):
        print("Starting monitoring for new mentions...")
        last_mention_id = None  # Para tests, setea a un ID reciente si sabes uno, e.g., 1944122257439416808
        base_sleep = 90  # Ajustado para Basic tier: ~10 requests/15 min
        max_backoff = 900  # Max 15 min

        while True:
            try:
                # Calcular tiempo de hace 5 minutos
                five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
                
                # Fetch con since_id y start_time para últimos 5 minutos
                mentions_response = self.client.get_users_mentions(
                    id=self.USER_ID,
                    since_id=last_mention_id,
                    start_time=five_minutes_ago,
                    expansions=['author_id'],
                    user_fields=['username']
                )
                
                # Log rate limit no disponible directamente, pero maneja en except

                if mentions_response.data:
                    users_map = {user.id: user for user in mentions_response.includes.get('users', [])}
                    
                    for mention in reversed(mentions_response.data):
                        author_id = mention.author_id
                        user = users_map.get(author_id)
                        if not user:
                            print("User not found.")
                            continue
                        
                        username = user.username
                        text = mention.text

                        if self.is_authorized(username):
                            # Para prueba: ignora autorización, responde si contiene company
                            company_ticker=self.extract_ticker_from_text(text)
                            analysis=self.generate_ai_analysis(ticker=company_ticker,company_name=None)
                            response_text= analysis
                            self.client.create_tweet(in_reply_to_tweet_id=mention.id, text=response_text)
                            print(f"Responded to @{username}: {text}")
                        else:
                            response_text= 'You can subcribe to our plan or ask to the dm for a free trial'
                            self.client.create_tweet(in_reply_to_tweet_id=mention.id, text=response_text)
                            print(f"Responded to @{username}: {text}")

                    last_mention_id = mentions_response.data[0].id  # Actualiza a newest
                
                time.sleep(base_sleep)
            
            except tweepy.errors.TooManyRequests as e:
                # Extrae reset de headers
                reset_time = int(e.response.headers.get('x-rate-limit-reset', time.time() + 900)) if e.response else time.time() + 900
                wait_time = max(30, reset_time - int(time.time()))
                print(f"Rate limit hit. Waiting {wait_time} seconds for reset.")
                time.sleep(wait_time)
            
            except tweepy.TweepyException as e:
                print(f"Error: {e}")
                time.sleep(60)