# news_extractor.py
from pygooglenews import GoogleNews
from datetime import datetime
import re
from html import unescape
import yfinance as yf
import twitter_client as tc
import working_wjson as wj


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
           
            for entry in entries:
                # Clean title and summary
                raw_title = entry.get('title', 'No title')
                raw_summary = entry.get('summary', 'No summary')
                raw_summary=self.clean_text(raw_summary)
                
                article = {
                    'title': self.clean_text(raw_title),
                    'summary': self.clean_text(raw_summary),
                    'provider': entry.get('published', ''),
                    #'source': entry.get('source', {}).get('title', 'Unknown'),
                    #'link': entry.get('link', ''), think on add link always i can in this return dict...
                }
                results[entry.get('id', '')] = article
            return results
            
        except Exception as e:
            print(f"Error searching news for {topic}: {e}")
            return None
        
    
      #extract news from y.finance, return none if not news or if error
    
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
        print(yf_all_company)
        wj.save_to_json(yf_all_company,'data/yf_news.json')
        wj.save_to_json(x_all_company,'data/x_tweets.json')
        wj.save_to_json(g_search_all_company,'data/google_news.json')

    # def united_news(self):
    #     g_news = wj.load_from_json('data/google_news.json')
    #     y_news=wj.load_from_json('data/yf_news.json')
    #     all_news={}
    #     for company in self.companies.keys():
    #         aux=g_news[company]
    #         aux

            

   

