# news_extractor.py
from pygooglenews import GoogleNews
from datetime import datetime
import re
from html import unescape
import company_analyzer as ca
import yfinance as yf
import twitter_client as tc


class NewsExtractor:
    def __init__(self, lang='en', country='US'):
        #Initialize Google News client
        self.gn = GoogleNews(lang=lang, country=country)
        #initialize x client
        self.tc= tc.TwitterClient()
    
    
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
    
    def search_news_google(self, topic, max_results=10):
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
        tweets=self.tc.search_tweets(query,max_results=50)
        return tweets
class newsSentiment:
    def __init__(self):
        #initialize news extractor
        self.news_extractor=NewsExtractor()
        #initialize Company analizer
        self.company_analyzer=ca.CompanyAnalyzer()
    '''
    conform actual data and save ir in a json
    data = {
    'microsoft': {
        'P_X': 0.60,  # Example: 60% of tweets are Positive
        'P_Y': 0.70,  # Example: 70% of Yahoo Finance articles are positive
        'P_G': 0.65,  # Example: 65% of Google News articles are positive
        'sample_X': 1000,  # Number of tweets
        'sample_Y': 50,    # Number of Yahoo Finance articles
        'sample_G': 20     # Number of Google News articles
    },
    '''

    





# Usage examples
def main():
    # Initialize news extractor
    news_extractor = NewsExtractor()
    company_a=ca.CompanyAnalyzer()

    # Example 1: Search Tesla news
    tesla_news = news_extractor.search_news_google("Tesla", max_results=15)
    # for i in tesla_news.keys():
    #     print(tesla_news[i]['summary'])
    sentiments=company_a.get_news_sentiment(tesla_news)
    

    print('sentiment ',sentiments['sentiment'])
    print('news_count',sentiments['news_count'])
    print(f'positive_porcent {sentiments['positive_porcent']}')
    print(f' negative_porcent: {sentiments[ 'negative_porcent']}')
   

if __name__ == "__main__":
    main()