# news_extractor.py
from pygooglenews import GoogleNews
from datetime import datetime, timedelta, timezone
import re
from html import unescape
import yfinance as yf
import twitter_client as tc
import working_wjson as wj
import dateutil.parser  # For parsing various date formats





class NewsExtractor:
    def __init__(self, lang='en', country='US'):
        #Initialize Google News client
        self.gn = GoogleNews(lang=lang, country=country)
        #initialize x client
        self.tc= tc.TwitterClient()
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
        """Search news for a specific topic"""
        try:
            # Search for news
            search_result = self.gn.search(topic)
            
            # Extract articles
            entries = search_result['entries'][:max_results]
            results={}
            count=0
            for entry in entries:
                # Clean title and summary
                raw_title = entry.get('title', 'No title')
                raw_summary = entry.get('summary', 'No summary')
                raw_summary=self.clean_text(raw_summary)
                
                article = {
                    'title': self.clean_text(raw_title),
                    'summary': self.clean_text(raw_summary),
                    'provider': entry.get('published', ''),
                }
                results[count] = article
                count=count+1
            return results
            
        except Exception as e:
            print(f"Error searching news for {topic}: {e}")
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
        
    def x_tweets(self,query):
        tweets=self.tc.search_tweets(query,max_results=30)
        return tweets
    
    def save_news(self):
        yf_all_company={}
        x_all_company={}
        g_search_all_company={}
        for i in self.companies.keys():
            yf=self.yf_news(self.companies[i])
            g_search=self.search_news_google(i)
            x=self.x_tweets(self.queries[i])
            yf_all_company[i]=yf
            x_all_company[i]=x
            g_search_all_company[i]=g_search
       
        wj.save_to_json(yf_all_company,'data/yf_news.json')
        wj.save_to_json(x_all_company,'data/x_tweets.json')
        wj.save_to_json(g_search_all_company,'data/google_news.json')
    

def main():
    topic=' "Tesla" AND ("political" OR "policy") AND ("regulation" OR "legislation" OR "trade_policy" OR "sanction" OR "tariff") AND "news" -("opinion" OR "rumor" OR "editorial")'
    ne=NewsExtractor()
    # news_filtered=ne.search_news_google_filter_time(topic,100)
    # print(len(news_filtered))
    # print(news_filtered)
    ne.yf_news("TSLA")

    
  

            


   

