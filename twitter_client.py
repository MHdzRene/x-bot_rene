import tweepy
import time
import get_creds
import re
from datetime import datetime, timedelta
import working_wjson as wj


#global variable for singleton
_twitter_client_instance = None

def get_twitter_client():
    """
    Obtiene la instancia singleton de TwitterClient.
    Solo se crea una vez durante toda la ejecución del programa.
    """
    global _twitter_client_instance
    if _twitter_client_instance is None:
        _twitter_client_instance = TwitterClient()
    return _twitter_client_instance

def reset_twitter_client():
    """Reinicia el singleton - útil para testing"""
    global _twitter_client_instance
    _twitter_client_instance = None
    

import pytz

class TwitterClient:
    def trigger_and_wait_for_analysis(self, company_name, company_ticker):
        """
        Ensures LLM analysis is completed and valid before posting. Returns analysis text or None.
        Prints all logic and data used for debugging if analysis fails.
        """
        import working_wjson as wj
        import company_analyzer as ca
        data_total = wj.load_from_json('data/data_total_analyze.json')
        pol = wj.load_from_json('data/uncertity_per_company.json')
        analyzer = ca.TwitterFormattedAnalyzer()
        analysis = analyzer.format_twitter_analysis(company_name, company_ticker)
        if not analysis or 'no sentiment data' in str(analysis).lower():
            print(f"[ERROR] LLM analysis failed or returned default for {company_name}. Analysis: {analysis}")
            print(f"[DEBUG] --- DATA USED FOR ANALYSIS ---")
            print(f"[DEBUG] Sentiment: {data_total.get(company_name)}")
            print(f"[DEBUG] Political: {pol.get(company_name)}")
            print(f"[DEBUG] Ticker: {company_ticker}, Name: {company_name}")
            print(f"[DEBUG] All sentiment keys: {list(data_total.keys())}")
            print(f"[DEBUG] All political keys: {list(pol.keys())}")
            print(f"[DEBUG] --- END DATA ---")
            return None
        print(f"[POST] LLM analysis ready for {company_name}: {analysis}")
        return analysis
    # Mensajes constantes
    MSG_MARKET_CLOSED = "Sorry, analysis is only available during market hours (9:30am-4:00pm ET, Mon-Fri)."
    MSG_MARKET_CLOSED_UNAUTH = MSG_MARKET_CLOSED + " Subscribe to get access to market analysis!"
    MSG_MARKET_OPEN_UNAUTH = "Subscribe to our plan or DM us for a free trial to access market analysis during open hours!"

    def get_mention_response(self, *, market_open, authorized, company_ticker, mention, username, text):
        """
        Decide y retorna el texto de respuesta y el tipo de log según el contexto.
        Si la compañía/ticker no existe en los JSONs, la agrega y fuerza extracción/analítica antes de responder.
        """
        if not company_ticker:
            return None, None  # No responde si formato incorrecto

        # --- Robust auto-add/analysis for new companies and always force news extraction ---
        import working_wjson as wj
        import updater_jsons
        import company_analyzer as ca
        # Try to resolve company name from ticker if not present
        companies = wj.load_from_json('data/companies.json')
        company_name = None
        for name, ticker in companies.items():
            if ticker.upper() == company_ticker.upper() or name.lower() == company_ticker.lower():
                company_name = name
                break
        updater = updater_jsons.updater_data()
        if not company_name:
            # Try to get company name from ticker using yfinance
            try:
                analyzer = ca.CompanyAnalyzer()
                company_name = analyzer.get_company_name_from_ticker(company_ticker)
            except Exception:
                company_name = company_ticker
            # Add to companies.json and trigger full update
            updater.add_company_to_companies(company_name, company_ticker)
            updater.update_news(company_name)
            # After update, reload companies
            companies = wj.load_from_json('data/companies.json')

        # Always force news extraction for the requested company before analysis
        updater.update_news(company_name)

        # Wait for news to be present in at least one source before proceeding
        import time
        max_wait = 30  # seconds
        wait_interval = 2
        waited = 0
        news_found = False
        while waited < max_wait:
            x_news = wj.load_from_json('data/x_tweets.json').get(company_name, {})
            y_news = wj.load_from_json('data/yf_news.json').get(company_name, {})
            g_news = wj.load_from_json('data/google_news.json').get(company_name, {})
            x_count = len(x_news) if isinstance(x_news, dict) else 0
            y_count = len(y_news) if isinstance(y_news, dict) else 0
            g_count = len(g_news) if isinstance(g_news, dict) else 0
            print(f"[DEBUG] News counts for {company_name}: X={x_count}, Y={y_count}, G={g_count}")
            if x_count > 0 or y_count > 0 or g_count > 0:
                news_found = True
                break
            print(f"[WAIT] No news found for {company_name} yet... {waited}/{max_wait} seconds elapsed.")
            time.sleep(wait_interval)
            waited += wait_interval

        if not news_found:
            print(f"[ERROR] No news found for {company_name} after extraction. Not posting.")
            return f"[ERROR] No news found for {company_name}. Please try again later.", f"[ERROR] No news for {company_name}."

        # Check if sentiment and political data exist, else force update and wait for real data
        waited = 0
        updater = updater_jsons.updater_data()
        while True:
            data_total = wj.load_from_json('data/data_total_analyze.json')
            pol = wj.load_from_json('data/uncertity_per_company.json')
            print(f"[DEBUG] data_total_analyze.json keys: {list(data_total.keys())}")
            print(f"[DEBUG] uncertity_per_company.json keys: {list(pol.keys())}")
            missing = False
            if company_name not in data_total:
                print(f"[WAIT] Sentiment data missing for {company_name}, updating...")
                updater.update_data_analyze_for_company(company_name)
                missing = True
            if company_name not in pol:
                print(f"[WAIT] Political uncertainty data missing for {company_name}, updating...")
                updater.update_political_uncertainty_for_company(company_name)
                missing = True
            if not missing:
                print(f"[READY] Analysis data found for {company_name}, proceeding to post.")
                break
            if waited >= max_wait:
                print(f"[ERROR] Timeout waiting for analysis data for {company_name}, using defaults.")
                break
            print(f"[WAIT] Waiting for analysis data for {company_name}... {waited}/{max_wait} seconds elapsed.")
            time.sleep(wait_interval)
            waited += wait_interval

        # Allow authorized users 24/7 access
        if authorized:
            analysis = self.trigger_and_wait_for_analysis(company_name, company_ticker)
            if not analysis:
                print(f"[ERROR] No valid analysis for {company_name}. Not posting.")
                return None, f"[ERROR] No valid analysis for {company_name}."
            print(f"[POST] Posting analysis for {company_name}: {analysis}")
            return analysis, f"[AUTHORIZED 24/7] Responded to @{username}: {text}"
        # If not authorized, check market hours
        if not market_open:
            return self.MSG_MARKET_CLOSED_UNAUTH, f"[CLOSED] Responded to @{username}: {text}"
        else:
            return self.MSG_MARKET_OPEN_UNAUTH, f"[OPEN-UNAUTH] Responded to @{username}: {text}"
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

        # Only use X API for mentions and posting answers
        self.authorized_users = set(wj.load_from_json('data/authorized_users.json'))
        self.company_analysis_cache = {}

        
    
    def create_tweet(self, text):
        """Creates a tweet safely with error handling and usage tracking"""
        print("[POST] Posting to X/Twitter:")
        print(text)
        try:
            from x_api_usage import increment_usage
            result = self.client.create_tweet(text=text)
            increment_usage(post_user=1, post_app=1)
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
    
    def search_tweets(self, query, max_total=100):
        """Search tweets with paginación eficiente (max_total resultados) y tracking de uso"""
        try:
            from x_api_usage import increment_usage
            tweets_results = {}
            title = 'no title'
            next_token = None
            fetched = 0
            while fetched < max_total:
                batch_size = min(100, max_total - fetched)
                tweets = self.client.search_recent_tweets(
                    query=query,
                    tweet_fields=['created_at', 'author_id', 'text'],
                    max_results=batch_size,
                    next_token=next_token
                )
                if tweets and tweets.data:
                    increment_usage(read=len(tweets.data))
                    for tweet in tweets.data:
                        aux = {
                            'title': title,
                            "summary": tweet.text,
                            "provider": tweet.author_id
                        }
                        tweets_results[tweet.id] = aux
                    fetched += len(tweets.data)
                else:
                    break
                # Paginación
                next_token = tweets.meta.get('next_token') if hasattr(tweets, 'meta') and tweets.meta else None
                if not next_token:
                    break
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
    
    def search_tweets_cleaned(self, query, max_total=100):
        """Search tweets and return cleaned text, paginación eficiente (max_total resultados) y tracking de uso"""
        try:
            from x_api_usage import increment_usage
            tweets_results = {}
            title = 'no title'
            next_token = None
            fetched = 0
            while fetched < max_total:
                batch_size = min(100, max_total - fetched)
                tweets = self.client.search_recent_tweets(
                    query=query,
                    tweet_fields=['created_at', 'author_id', 'text'],
                    max_results=batch_size,
                    next_token=next_token
                )
                if tweets and tweets.data:
                    increment_usage(read=len(tweets.data))
                    for tweet in tweets.data:
                        cleaned_text = self.clean_tweet(tweet.text)
                        aux = {
                            'title': title,
                            "summary": cleaned_text,
                            "provider": tweet.author_id
                        }
                        tweets_results[tweet.id] = aux
                    fetched += len(tweets.data)
                else:
                    break
                # Paginación
                next_token = tweets.meta.get('next_token') if hasattr(tweets, 'meta') and tweets.meta else None
                if not next_token:
                    break
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
    # All subscriber and dynamic authorized user loading from X API is disabled for minimal API usage
    # Only static authorized_users from JSON and promo_accounts are used

    def is_authorized(self,username):
        """Function to check if a username is authorized"""
        return username in self.authorized_users or username in self.promo_accounts
    #until here
  
    def generate_ai_analysis(self, company_name, ticker):
        """
        Returns cached analysis for a ticker if available and fresh (10 min), else generates new and updates cache.
        # Incluye solo noticias de Yahoo y Google News en el análisis.
        """
        cache_key = ticker or (company_name or '').lower()
        now = time.time()
        # Check cache
        if cache_key in self.company_analysis_cache:
            ts, cached_analysis = self.company_analysis_cache[cache_key]
            if now - ts < 600:  # 10 minutes
                return cached_analysis
        # Not cached or expired, generate new analysis
        import company_analyzer as ca
        analysis = ca.get_company_analysis(company_name, ticker)
        # RSS/feed code removed: only Yahoo and Google News are used.
        self.company_analysis_cache[cache_key] = (now, analysis)
        return analysis
    
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

    def is_market_open(self):
        # NYSE: 9:30am - 4:00pm America/New_York, Monday-Friday
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close

    # =====================
    # MONITORIZACIÓN Y RESPUESTA A MENCIONES CON CONTROL DE CONCURRENCIA Y RATE LIMITS
    # ------------------------------------------------------
    # Esta función implementa:
    # - Escaneo periódico de menciones a la cuenta.
    # - Respuesta automática solo a usuarios autorizados y durante horario de mercado.
    # - Control de concurrencia mediante file lock (múltiples procesos/hilos no pueden responder a la vez).
    # - Manejo avanzado de rate limits: si se alcanza el límite de la API, espera el tiempo indicado por X-Rate-Limit-Reset.
    # - Temporizador entre escaneos para evitar sobreuso de la API.
    #
    # Lógica de caps y rate limits:
    # - El bot respeta los límites de la API de X/Twitter (ejemplo: 300 consultas/15min para endpoints de usuario).
    # - Si se detecta un error 429 (TooManyRequests), se lee el header 'x-rate-limit-reset' y espera hasta que se pueda reintentar.
    # - El file lock asegura que solo un proceso accede a la API y actualiza el estado a la vez, evitando corrupción o doble uso.
    # - El temporizador base_sleep ajusta la frecuencia de escaneo según si el mercado está abierto o cerrado.
    #
    # Para más detalles, consulta la sección "Límites y control de uso" en el README.
    def monitor_and_respond_mentions(self):
        import os
        import threading
        from contextlib import contextmanager
        print("Starting monitoring for new mentions...")
        last_mention_id = None
        max_backoff = 900

        # Simple file lock context manager (cross-platform, works for single machine)
        @contextmanager
        def file_lock(lockfile, timeout=30):
            import time
            start = time.time()
            while True:
                try:
                    # Try to create the lock file exclusively
                    fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    os.close(fd)
                    break
                except FileExistsError:
                    if time.time() - start > timeout:
                        raise TimeoutError(f"Timeout waiting for lock {lockfile}")
                    time.sleep(0.2)
            try:
                yield
            finally:
                try:
                    os.remove(lockfile)
                except Exception:
                    pass

        lockfile = "mention_bot.lock"

        while True:
            try:
                market_open = self.is_market_open()
                if market_open:
                    base_sleep = 270  # 4 min 30 seg
                    scan_window = 5
                else:
                    base_sleep = 270  # 4 min 30 seg (changed from 1 hour)
                    scan_window = 65  # minutos para buscar menciones recientes

                # Print scan info and next scan timer
                next_scan_time = datetime.now() + timedelta(seconds=base_sleep)
                print(f"[SCAN] Escaneando menciones... Próximo escaneo en {base_sleep//60} min {base_sleep%60} seg (a las {next_scan_time.strftime('%H:%M:%S')})")

                scan_minutes_ago = datetime.utcnow() - timedelta(minutes=scan_window)

                mentions_response = self.client.get_users_mentions(
                    id=self.USER_ID,
                    since_id=last_mention_id,
                    start_time=scan_minutes_ago,
                    expansions=['author_id'],
                    user_fields=['username'],
                    tweet_fields=['created_at', 'author_id', 'text']
                )

                if mentions_response.data:
                    users_map = {user.id: user for user in mentions_response.includes.get('users', [])}
                    for mention in reversed(mentions_response.data):
                        username = None  # Ensure username is always defined
                        with file_lock(lockfile):
                            try:
                                # Only respond if mention is no more than 5 min old
                                if not hasattr(mention, 'created_at') or mention.created_at is None:
                                    author_id = getattr(mention, 'author_id', '?')
                                    user = users_map.get(author_id)
                                    username = user.username if user else None
                                    if username:
                                        print(f"[SKIP] Mention from @{username} (id: {author_id}) has no created_at, skipping.")
                                    else:
                                        print(f"[SKIP] Mention from @{author_id} has no created_at, skipping.")
                                    continue
                                mention_time = mention.created_at.replace(tzinfo=None)
                                now_utc = datetime.utcnow()
                                age_minutes = (now_utc - mention_time).total_seconds() / 60.0
                                if age_minutes > 5:
                                    print(f"[SKIP] Mention from @{getattr(mention, 'author_id', '?')} is {age_minutes:.1f} min old (>{5} min), skipping.")
                                    continue
                                author_id = mention.author_id
                                user = users_map.get(author_id)
                                if not user:
                                    print("User not found.")
                                    continue
                                username = user.username
                                text = mention.text
                                print(f"[MENTION] @{username}: {text}")
                                company_ticker = self.extract_ticker_from_text(text)
                                if not company_ticker:
                                    print(f"[SKIP] No ticker found in mention from @{username}: '{text}'")
                                    continue
                                authorized = self.is_authorized(username)
                                response_text, log_msg = self.get_mention_response(
                                    market_open=market_open,
                                    authorized=authorized,
                                    company_ticker=company_ticker,
                                    mention=mention,
                                    username=username,
                                    text=text
                                )
                                if response_text:
                                    print(f"[DEBUG] About to post response for @{username}: {response_text}")
                                    self.client.create_tweet(in_reply_to_tweet_id=mention.id, text=response_text)
                                    print(log_msg)
                                else:
                                    print(f"[SKIP] No response for @{username} ({company_ticker}). Log: {log_msg}")
                                # Wait 55 seconds between answers to comply with X API rate limits
                                time.sleep(55)
                            except Exception as e:
                                print(f"[ERROR] Could not process mention for @{username if username else '?'}: {e}")
                                import traceback
                                print(f"[DEBUG] Full error traceback: {traceback.format_exc()}")
                                continue

                    last_mention_id = mentions_response.data[0].id

                # Temporizador hasta el próximo escaneo
                for remaining in range(base_sleep, 0, -1):
                    mins, secs = divmod(remaining, 60)
                    print(f"Siguiente escaneo en {mins:02d}:{secs:02d} (mm:ss)   ", end='\r', flush=True)
                    time.sleep(1)

            except tweepy.errors.TooManyRequests as e:
                # Manejo avanzado de rate limit usando header X-Rate-Limit-Reset
                reset_time = None
                if hasattr(e, 'response') and e.response is not None:
                    reset_header = e.response.headers.get('x-rate-limit-reset')
                    if reset_header:
                        try:
                            reset_time = int(reset_header)
                        except Exception:
                            reset_time = None
                if reset_time is None:
                    reset_time = int(time.time()) + 900  # fallback 15 min
                wait_time = max(30, reset_time - int(time.time()))
                reset_dt = datetime.fromtimestamp(reset_time).strftime('%Y-%m-%d %H:%M:%S')
                print(f"[429] Rate limit alcanzado. Esperando {wait_time} segundos (hasta {reset_dt}) antes de reintentar.")
                for remaining in range(wait_time, 0, -1):
                    mins, secs = divmod(remaining, 60)
                    print(f"Reintento en {mins:02d}:{secs:02d} (mm:ss)   ", end='\r', flush=True)
                    time.sleep(1)

            except tweepy.TweepyException as e:
                print(f"Error: {e}")
                time.sleep(60)
        print("[DEBUG] Fetching recent mentions...")
        mentions = self.get_recent_mentions()
        print(f"[DEBUG] Total mentions fetched: {len(mentions)}")
        for mention in mentions:
            print(f"[DEBUG] --- New Mention ---")
            print(f"[DEBUG] Mention raw: {mention}")
            # Only process mentions with a ticker/company
            company, ticker = self.extract_company_from_mention(mention)
            print(f"[DEBUG] Extracted company: {company}, ticker: {ticker}")
            if not ticker:
                print(f"[DEBUG] No ticker found in mention: {mention.get('text')}")
                continue
            # Only respond to mentions no more than 5 minutes old
            if not self.is_recent_mention(mention):
                print(f"[DEBUG] Mention too old: {mention.get('created_at')}")
                continue
            print(f"[DEBUG] Processing mention: {mention.get('text')}")
            try:
                print(f"[DEBUG] Starting analysis pipeline for {company} ({ticker})...")
                from company_analyzer import get_company_analysis
                print(f"[DEBUG] Step 1: Data extraction and update for {company} ({ticker})")
                # get_company_analysis will update news and analysis JSONs
                analysis = get_company_analysis(company, ticker)
                print(f"[DEBUG] Step 2: Analysis generated for {company} ({ticker})")
                print(f"[DEBUG] Step 3: Saving analysis data to JSON (if not already done)")
                # Data saving is handled inside get_company_analysis and updater_jsons
                print(f"[DEBUG] Step 4: Posting analysis to X...")
                self.create_tweet(analysis, in_reply_to_status_id=mention['id'])
                print(f"[DEBUG] Step 5: Posted analysis for {company} ({ticker})")
                print(f"[DEBUG] --- End of Mention Processing ---\n")
            except Exception as e:
                print(f"[ERROR] Failed to analyze or post for {company} ({ticker}): {e}")
                continue