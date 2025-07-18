# news_extractor.py
from pygooglenews import GoogleNews
from datetime import datetime, timedelta, timezone
import re
from html import unescape
import yfinance as yf
import twitter_client as tc
import working_wjson as wj
import dateutil.parser  # For parsing various date formats



import json

class NewsExtractor:
    def __init__(self, lang='en', country='US'):
        #Initialize Google News client
        self.gn = GoogleNews(lang=lang, country=country)
        #initialize x client
        self.tc = tc.get_twitter_client()
        #initialize copany_analyzer
        self.companies = wj.load_from_json('data/companies.json')
        self.queries= wj.load_from_json('data/queries_x.json')
         
    def clean_text(self, text):
        """Clean HTML tags and noise from text"""
        if not text:
            return "No content"
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities (&amp; -> &, &quot; -> ", etc.)
        text = unescape(text)
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common noise patterns
        text = re.sub(r'\.\.\.$', '', text)  # Remove trailing ...
        text = re.sub(r'^[•\-\*\>\s]*', '', text)  # Remove leading bullets/dashes
        
        # Limit length for summary (optional)
        if len(text) > 200:
            text = text[:197] + "..."
        
        return text
    
    def search_news_google(self, topic, max_results=60):
        """Search news for a specific topic, with debug and fallback."""
        try:
            print(f"[DEBUG] GoogleNews: Searching for topic: '{topic}'")
            search_result = self.gn.search(topic)
            entries = search_result.get('entries', [])[:max_results]
            print(f"[DEBUG] GoogleNews: Found {len(entries)} entries for topic '{topic}'")
            if len(entries) == 0:
                # Fallback: try a more specific query
                fallback_topic = f"{topic} stock news"
                print(f"[DEBUG] GoogleNews: No results, trying fallback topic: '{fallback_topic}'")
                search_result = self.gn.search(fallback_topic)
                entries = search_result.get('entries', [])[:max_results]
                print(f"[DEBUG] GoogleNews: Fallback found {len(entries)} entries for topic '{fallback_topic}'")
            results = {}
            count = 0
            for entry in entries:
                raw_title = entry.get('title', 'No title')
                raw_summary = entry.get('summary', 'No summary')
                raw_summary = self.clean_text(raw_summary)
                article = {
                    'title': self.clean_text(raw_title),
                    'summary': self.clean_text(raw_summary),
                    'provider': entry.get('published', ''),
                }
                results[count] = article
                count += 1
            if len(results) == 0:
                print(f"[WARN] GoogleNews: No news found for topic '{topic}' or fallback.")
            return results
        except Exception as e:
            print(f"[ERROR] GoogleNews: Exception searching news for {topic}: {e}")
            return None
        
    
      #extract news from y.finance, return none if not news or if error

    def search_news_google_filter_time(self, topic, max_results=100):
        """Search news for a specific topic, filtering for articles from the last week."""
        try:
            # Get current date and the date one week ago (offset-aware, UTC)
            current_date = datetime.now(timezone.utc)
            one_month_ago = current_date - timedelta(weeks=2)

            # Search for news
            search_result = self.gn.search(topic)
            
            # Extract articles
            entries = search_result['entries'][:max_results]
            
            results = {}
            count = 0
            for entry in entries:
                # Parse the published date
                raw_published = entry.get('published', None)
                if raw_published:
                    try:
                        # Parse date (already offset-aware if timezone is included)
                        published_date = dateutil.parser.parse(raw_published)
                        # Check if the article is within the last week
                        if published_date >=  one_month_ago and published_date <= current_date:
                            # Clean title and summary
                            raw_title = entry.get('title', 'No title')
                            raw_summary = entry.get('summary', 'No summary')
                            
                            article = {
                                'title': self.clean_text(raw_title),
                                'summary': self.clean_text(raw_summary),
                                'provider': raw_published,
                            }
                            results[count] = article
                            count += 1
                        
                    except ValueError:
                        # Skip articles with unparseable dates
                        continue
                else:
                    # Skip articles with no published date
                    continue
                    
            return results

        except Exception as e:
            print(f"Error searching news for {topic}: {e}")
            return None
   
    def search_gnews_lits_of_topics(self,topics,max_results=5):
        """Search news for a list of topics
        return: list of dicts [{},{}...]
        """
        
        news=[]
        for topic in topics:
            #news_aux=self.search_news_google(topic,max_results=max_results)
            news_aux=self.search_news_google_filter_time(topic,max_results=max_results)
            news.extend(news_aux.values())
        return news 

    def yf_news(self,ticker):
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return None
            else:
                answer={}
                count=0
                aux={}
                #news will be a dict {title: "lalal", summary: "llalal", provider:"lalal"}
                for article in news[:100]:
                    try:
                        content = article.get('content', {})
                        if not content:
                            continue
                        title = content.get('title', 'No title')
                        text_to_analyze = (title + ' ' + content.get('summary', '')).lower() 
                        provider=content.get('provider', {}).get('displayName', 'Unknown')    
                        aux={'title': title, "summary": text_to_analyze,"provider":provider}
                        answer[str(count)]=aux
                        aux={}  
                        count=count+1
                    except Exception:
                        continue
               
                return answer
        except Exception as e:
            print(f"Error getting news for {ticker}: {e}")
            return None 
        
    def x_tweets(self, query):
        # X API usage for tweet search is disabled for minimal API usage
        print(f"[DEBUG] X/Twitter: Tweet search disabled for query: '{query}'")
        return {}
    
    def update_queries(self,ticker,company_name):
        querie=self.generate_standard_x_query(company_name,ticker)
        self.queries[company_name]= querie
        wj.save_to_json(self.queries,'data/queries_x.json')

    def generate_standard_x_query(self,company_name, ticker):
        """
        Genera una query estándar para X donde solo necesitas el nombre de la compañía
        """
        standard_query = f"{company_name} OR {ticker} -is:retweet -is:reply -discount -sale lang:en"
        return standard_query

    def save_news(self):
        import time
        yf_all_company = {}
        x_all_company = {}
        g_search_all_company = {}
        for company_name, ticker in self.companies.items():
            print(f"[PIPELINE] Processing: {company_name} (Ticker: {ticker})")
            # Yahoo Finance
            yf = self.yf_news(ticker)
            print(f"[PIPELINE] Yahoo Finance: {len(yf) if yf else 0} articles for {company_name}")
            if yf is not None and yf != {}:
                yf_all_company[company_name] = yf
            else:
                yf_all_company[company_name] = {}  # Always include the key
            # Google News (use company name as topic, like test script)
            g_search = self.search_news_google(company_name)
            if g_search is not None and g_search != {}:
                print(f"[PIPELINE] Google News: {len(g_search)} articles for topic '{company_name}'")
                g_search_all_company[company_name] = g_search
            else:
                print(f"[WARN] Google News: No news found for topic '{company_name}'. Saving empty entry.")
                g_search_all_company[company_name] = {}  # Always include the key
            # X/Twitter (use company name as query, like test script)
            x_query = f"{company_name} -is:retweet -is:reply lang:en"
            # X API usage for tweet search is disabled for minimal API usage
            print(f"[PIPELINE] X/Twitter: Tweet search disabled for query '{x_query}'")
            x = {}
            x_all_company[company_name] = x  # Always include the key
            time.sleep(1)  # avoid rate limits
        wj.save_to_json(yf_all_company, 'data/yf_news.json')
        wj.save_to_json(x_all_company, 'data/x_tweets.json')
        wj.save_to_json(g_search_all_company, 'data/google_news.json')
        # Post-save verification
        print("[DEBUG] Post-save verification:")
        for fname in ['data/yf_news.json', 'data/x_tweets.json', 'data/google_news.json']:
            try:
                with open(fname, 'r') as f:
                    data = json.load(f)
                print(f"[DEBUG] {fname} contains {len(data) if isinstance(data, dict) else 'non-dict'} items after save_news.")
            except Exception as e:
                print(f"[DEBUG] Error reading {fname} after save: {e}")
    
    def save_single_company_news(self,company_name):
        yf_all_companies=wj.load_from_json('data/yf_news.json')
        x_all_companies=wj.load_from_json('data/x_tweets.json')
        g_all_companies=wj.load_from_json('data/google_news.json')

        yf=self.yf_news(self.companies[company_name])
        if yf is not None and yf != {}:
            yf_all_companies[company_name]=yf
        # X API usage for tweet search is disabled for minimal API usage
        x = {}
        g_search=self.search_news_google(company_name)
        if g_search is not None and g_search != {}:
            g_all_companies[company_name]=g_search
        #save updates
        wj.save_to_json(yf_all_companies,'data/yf_news.json')
        wj.save_to_json(x_all_companies,'data/x_tweets.json')
        wj.save_to_json(g_all_companies,'data/google_news.json')
        # Post-save verification
        print(f"[DEBUG] Post-save verification for {company_name}:")
        for fname in ['data/yf_news.json', 'data/x_tweets.json', 'data/google_news.json']:
            try:
                with open(fname, 'r') as f:
                    data = json.load(f)
                print(f"[DEBUG] {fname} contains {len(data) if isinstance(data, dict) else 'non-dict'} items after save_single_company_news.")
            except Exception as e:
                print(f"[DEBUG] Error reading {fname} after save: {e}")





    
  

            


   

