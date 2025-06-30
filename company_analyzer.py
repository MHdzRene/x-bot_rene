import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import bot
import working_wjson as wj
import news

class CompanyAnalyzer:
    def __init__(self):
        # Top 5 tech companies with their ticker symbols
        self.companies = {
            'Microsoft': 'MSFT',
            'Nvidia': 'NVDA', 
            'Apple': 'AAPL',
            'Amazon': 'AMZN',
            'Alphabet': 'GOOGL',
            'Tesla': 'TSLA',
        }
    
    def get_company_fundamentals(self, ticker):
        """Get fundamental data for a company"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'forward_pe': info.get('forwardPE', 'N/A'),
                'price_to_book': info.get('priceToBook', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'return_on_equity': info.get('returnOnEquity', 'N/A'),
                'profit_margin': info.get('profitMargins', 'N/A'),
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
                'earnings_growth': info.get('earningsGrowth', 'N/A'),
                'current_ratio': info.get('currentRatio', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'beta': info.get('beta', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'business_summary': info.get('businessSummary', 'N/A')
            }
        except Exception as e:
            print(f"Error getting fundamentals for {ticker}: {e}")
            return {}
    
    def get_technical_analysis(self, ticker, period="1y"):
        """Get technical analysis for a company"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            # Calculate technical indicators
            hist['MA_20'] = hist['Close'].rolling(window=20).mean()
            hist['MA_50'] = hist['Close'].rolling(window=50).mean()
            hist['MA_200'] = hist['Close'].rolling(window=200).mean()
            
            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
            bb_std = hist['Close'].rolling(window=20).std()
            hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
            hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
            
            # Volatility
            hist['Volatility'] = hist['Close'].rolling(window=20).std()
            
            current = hist.iloc[-1]
            
            # Performance calculations
            ytd_start = hist.loc[hist.index >= f"{datetime.now().year}-01-01"].iloc[0] if len(hist.loc[hist.index >= f"{datetime.now().year}-01-01"]) > 0 else hist.iloc[0]
            month_ago = hist.iloc[-22] if len(hist) >= 22 else hist.iloc[0]
            year_ago = hist.iloc[-252] if len(hist) >= 252 else hist.iloc[0]
            
            return {
                'current_price': current['Close'],
                'ma_20': current['MA_20'],
                'ma_50': current['MA_50'],
                'ma_200': current['MA_200'],
                'rsi': current['RSI'],
                'volatility': current['Volatility'],
                'volume': current['Volume'],
                'bb_upper': current['BB_Upper'],
                'bb_lower': current['BB_Lower'],
                'price_vs_bb': self.get_bb_position(current['Close'], current['BB_Upper'], current['BB_Lower']),
                'ytd_return': ((current['Close'] - ytd_start['Close']) / ytd_start['Close']) * 100,
                'month_return': ((current['Close'] - month_ago['Close']) / month_ago['Close']) * 100,
                'year_return': ((current['Close'] - year_ago['Close']) / year_ago['Close']) * 100,
                '52_week_high': hist['Close'].max(),
                '52_week_low': hist['Close'].min(),
                'distance_from_high': ((current['Close'] - hist['Close'].max()) / hist['Close'].max()) * 100,
                'distance_from_low': ((current['Close'] - hist['Close'].min()) / hist['Close'].min()) * 100
            }
            
        except Exception as e:
            print(f"Error calculating technical analysis for {ticker}: {e}")
            return None
    
    def get_bb_position(self, price, upper, lower):
        """Determine position within Bollinger Bands"""
        if price > upper:
            return "Above Upper Band (Overbought)"
        elif price < lower:
            return "Below Lower Band (Oversold)"
        else:
            return "Within Bands (Normal)"
    
    def get_news_sentiment(self,news):
        """Get news sentiment for a company"""
        if news == None:
            return {'sentiment': 'No news available', 'news_count': 0, 'articles': []}
            
        # Keywords for sentiment analysis
            # Expanded positive keywords list
       
        positive_keywords =wj.load_from_json('data/positive_keywords.json')
        negative_keywords =wj.load_from_json('data/negative_keywords.json')
         
        analyzed_articles = []
        total_positive = 0
        total_negative = 0
        #news will be a dict {title: "lalal", summary: "llalal", provider:"lalal"}
        for article in news.keys():  # Analyze top 5 news articles
                title = news[article]['title']
                text_to_analyze = (title + ' ' + news[article]['summary'])
                    
                positive_score = sum(1 for word in positive_keywords if word in text_to_analyze)
                negative_score = sum(1 for word in negative_keywords if word in text_to_analyze)
                    
                if positive_score > negative_score:
                    sentiment = "📈 Positive"
                    total_positive += 1
                elif negative_score > positive_score:
                    sentiment = "📉 Negative"
                    total_negative += 1
                else:
                    sentiment = "➡️ Neutral"
                    
                analyzed_articles.append({
                        'title': title,
                        'sentiment': sentiment,
                        'publisher': news[article]["provider"]
                    })
                      
            
            # Overall sentiment
        if total_positive > total_negative:
            overall_sentiment = "📈 Overall Positive"
        elif total_negative > total_positive:
            overall_sentiment = "📉 Overall Negative"
        else:
            overall_sentiment = "➡️ Overall Neutral"
            
        return {
            'sentiment': overall_sentiment,
            'news_count': len(analyzed_articles),
            'positive_count': total_positive,
            'positive_porcent': total_positive*100/len(analyzed_articles),
            'negative_count': total_negative,
            'negative_porcent': total_negative*100/len(analyzed_articles),
            'articles': analyzed_articles
        }
    
    def format_large_number(self, num):
        """Format large numbers (market cap, etc.)"""
        if num == 'N/A' or num is None:
            return 'N/A'
        
        try:
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            else:
                return f"${num:,.0f}"
        except:
            return str(num)
    
    def format_percentage(self, num):
        """Format percentage values"""
        if num == 'N/A' or num is None:
            return 'N/A'
        try:
            return f"{num:.2f}%"
        except:
            return str(num)
    
    def get_valuation_assessment(self, fundamentals):
        """Provide basic valuation assessment"""
        assessments = []
        
        pe_ratio = fundamentals.get('pe_ratio', 'N/A')
        if pe_ratio != 'N/A' and pe_ratio is not None:
            if pe_ratio < 15:
                assessments.append("🟢 Low P/E ratio - potentially undervalued")
            elif pe_ratio > 30:
                assessments.append("🔴 High P/E ratio - potentially overvalued")
            else:
                assessments.append("🟡 Moderate P/E ratio - fair valuation")
        
        debt_to_equity = fundamentals.get('debt_to_equity', 'N/A')
        if debt_to_equity != 'N/A' and debt_to_equity is not None:
            if debt_to_equity < 0.3:
                assessments.append("🟢 Low debt-to-equity - strong balance sheet")
            elif debt_to_equity > 1.0:
                assessments.append("🔴 High debt-to-equity - high leverage")
            else:
                assessments.append("🟡 Moderate debt-to-equity - acceptable leverage")
        
        roe = fundamentals.get('return_on_equity', 'N/A')
        if roe != 'N/A' and roe is not None:
            if roe > 0.15:
                assessments.append("🟢 High ROE - efficient use of equity")
            elif roe < 0.1:
                assessments.append("🔴 Low ROE - less efficient")
            else:
                assessments.append("🟡 Moderate ROE - acceptable efficiency")
        
        return assessments if assessments else ["📊 Insufficient data for valuation assessment"]
    
    def analyze_single_company(self, company_name):
        large_tweet=dict()
        """Analyze a single company comprehensively"""
        ticker = self.companies.get(company_name)
        fundamentals = self.get_company_fundamentals(ticker)
        
        if fundamentals:
           # print(f"Market Cap: {self.format_large_number(fundamentals.get('market_cap'))}")
            large_tweet["market_cap: "]=str(self.format_large_number(fundamentals.get('market_cap')))
            large_tweet["P/E Ratio: "]=str(fundamentals.get('pe_ratio', 'N/A'))
            large_tweet["Dividend Yield: "]=str(self.format_percentage(fundamentals.get('dividend_yield')))
            large_tweet["Sector: "]=str(fundamentals.get('sector', 'N/A'))

        technical = self.get_technical_analysis(ticker)
        
        if technical:
            large_tweet["Current Price: "]=str(technical['current_price'])
 
        news_data = self.get_news_sentiment(ticker, company_name)
        large_tweet["Overall Sentiment: "]=str(news_data['sentiment'])

       # print(f"Recent Articles Analyzed: {news_data['news_count']}")
        large_tweet["Recent Articles Analyzed: "]=str(news_data['news_count'])

        if news_data['news_count'] > 0:
            # print(f"Positive: {news_data['positive_count']} | Negative: {news_data['negative_count']}")
            news=[]
            #print(f"\nRecent Headlines:")
            for article in news_data['articles'][:3]:
                #print(f"{article['sentiment']} {article['title'][:80]}...")
                #print(f"   Source: {article['publisher']}")
                news.append(f"{article['sentiment']} {article['title'][:80]}...Source: {article['publisher']}")
           # print(news)
        large_tweet['news']=news
        return large_tweet
    
    def analyze_all_companies(self):
        """Analyze all 5 companies"""
        print("🚀 BIG TECH STOCK ANALYSIS - TOP 5 COMPANIES")
        print("=" * 80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for company_name in self.companies.keys():
            self.analyze_single_company(company_name)
            print("\n" * 2)
        
        # Summary comparison
        self.create_comparison_summary()
    
    def create_comparison_summary(self):
        """Create a quick comparison summary of all companies"""
        print("=" * 80)
        print("📊 QUICK COMPARISON SUMMARY")
        print("=" * 80)
        
        summary_data = []
        
        for company_name, ticker in self.companies.items():
            fundamentals = self.get_company_fundamentals(ticker)
            technical = self.get_technical_analysis(ticker)
            
            if fundamentals and technical:
                summary_data.append({
                    'company': company_name,
                    'ticker': ticker,
                    'market_cap': fundamentals.get('market_cap', 0),
                    'pe_ratio': fundamentals.get('pe_ratio', 'N/A'),
                    'current_price': technical['current_price'],
                    'ytd_return': technical['ytd_return'],
                    'year_return': technical['year_return']
                })
        
        # Sort by market cap
        summary_data.sort(key=lambda x: x['market_cap'] if x['market_cap'] != 'N/A' and x['market_cap'] is not None else 0, reverse=True)
        
        print(f"{'Company':<12} {'Ticker':<6} {'Market Cap':<12} {'P/E':<8} {'Price':<10} {'YTD%':<8} {'1Y%':<8}")
        print("-" * 70)
        
        for data in summary_data:
            market_cap_str = self.format_large_number(data['market_cap'])
            pe_str = f"{data['pe_ratio']:.1f}" if data['pe_ratio'] != 'N/A' and data['pe_ratio'] is not None else 'N/A'
            
            print(f"{data['company']:<12} {data['ticker']:<6} {market_cap_str:<12} {pe_str:<8} ${data['current_price']:<9.2f} {data['ytd_return']:<7.1f}% {data['year_return']:<7.1f}%")
        
        print("\n⚠️ IMPORTANT: This analysis is for educational purposes only. Always consult with financial professionals before making investment decisions.")

    def get_single_company_sentiment_metrics(self,company):
        """
            Aggregates sentiment analysis data from three major sources for a single company.
            
            This function orchestrates the complete sentiment analysis pipeline:
            1. Fetches data from X (Twitter), Yahoo Finance, and Google News
            2. Applies sentiment analysis to each data source
            3. Normalizes sentiment percentages to ratios (0.0-1.0)
                4. Extracts sample sizes for statistical weighting
                5. Returns standardized metrics for cross-platform comparison
                
                Args:
                    topic_g (str): Company name or topic for Google News search
                                Example: "Tesla", "Apple Inc", "Microsoft Corporation"
                    ticker_y (str): Stock ticker symbol for Yahoo Finance news
                                Example: "TSLA", "AAPL", "MSFT"
                    query_x (str): Custom search query for X (Twitter) platform
                                Example: "Tesla OR TSLA OR 'Model 3' -is:retweet lang:en"
            
                Note:
                    - Neutral sentiment is calculated as: 1.0 - (positive_ratio + negative_ratio)
                    - Sample sizes are crucial for statistical significance in sentiment weighting
                    - If any source fails, that source will return 0 values for all metrics
            
                    # Result: {'P_X': 0.65, 'N_X': 0.20, 'P_Y': 0.45, ...}
        """
        
        # Step 1: Data Collection Phase
        # Fetch tweets from X using custom query
        x_news = wj.load_from_json('data/x_tweets.json')
        x_news=x_news[company]
        
        # Fetch financial news from Yahoo Finance using ticker
        y_news = wj.load_from_json('data/yf_news.json')
        y_news=y_news[company]

        # Fetch general news from Google News using company topic
        g_news =wj.load_from_json('data/google_news.json')
        g_news=g_news[company]

        # Step 2: Sentiment Analysis Phase
        # Apply sentiment analysis to each data source
        x_sentiment = self.get_news_sentiment(x_news)
        y_sentiment = self.get_news_sentiment(y_news)
        g_sentiment = self.get_news_sentiment(g_news)
        
        # Step 3: Data Normalization Phase
        # Convert percentages to ratios (0-100% → 0.0-1.0) for consistent scaling
        positive_x_ratio = x_sentiment['positive_porcent'] / 100
        negative_x_ratio = x_sentiment['negative_porcent'] / 100
        positive_y_ratio = y_sentiment['positive_porcent'] / 100
        negative_y_ratio = y_sentiment['negative_porcent'] / 100
        positive_g_ratio = g_sentiment['positive_porcent'] / 100
        negative_g_ratio = g_sentiment['negative_porcent'] / 100
        
        # Extract sample sizes for statistical weighting
        sample_size_x = x_sentiment['news_count']
        sample_size_y = y_sentiment['news_count']
        sample_size_g = g_sentiment['news_count']

        # Step 4: Return Standardized Metrics
        return {
            'P_X': positive_x_ratio,     # X positive sentiment ratio (0.0-1.0)
            'N_X': negative_x_ratio,     # X negative sentiment ratio (0.0-1.0)
            'P_Y': positive_y_ratio,     # Yahoo Finance positive sentiment ratio
            'N_Y': negative_y_ratio,     # Yahoo Finance negative sentiment ratio
            'P_G': positive_g_ratio,     # Google News positive sentiment ratio
            'N_G': negative_g_ratio,     # Google News negative sentiment ratio
            'sample_X': sample_size_x,   # Number of X posts analyzed
            'sample_Y': sample_size_y,   # Number of Yahoo Finance articles analyzed
            'sample_G': sample_size_g    # Number of Google News articles analyzed
        }
      
    def get_multi_source_sentiment_analysis(self, queries_path='data/queries_x.json'):
        """
        Performs comprehensive sentiment analysis for multiple companies using three data sources:
        X (Twitter), Yahoo Finance, and Google News.
        
        """
        # Load platform-specific search queries for each company
        queries = wj.load_from_json(queries_path)
        
        
        # Initialize container for all companies' sentiment data
        total_data = {}

        # Process each company individually
        for company in self.companies.keys():
            # Extract sentiment data from all three sources for this company
            total_data[company] = self.get_single_company_sentiment_metrics(
                company,                    # Company name ~
            )
        wj.save_to_json(total_data,'data/data_total_analyze.json')
        return total_data

class TwitterFormattedAnalyzer(CompanyAnalyzer):
    def __init__(self):
        super().__init__()
        self.news_extractor= news.NewsExtractor()
    
    def format_twitter_analysis(self, company_name):
        """Generate a Twitter-formatted analysis string for a company"""
        ticker = self.companies.get(company_name)
        if not ticker:
            return f"Company {company_name} not found in database"
        
        # Get all the data
        fundamentals = self.get_company_fundamentals(ticker)
        technical = self.get_technical_analysis(ticker)

        news=wj.load_from_json('data/yf_news.json')
        news=news[company_name]

        news_data = self.get_news_sentiment(news)
       
        
        # Current date and time
        current_time = datetime.now().strftime('%B %d, %Y, %H:%M MDT')
        
        #combine prob
        combine_prob=wj.load_from_json('data/Combined_Prob.json') 
        combine_prob_positive=combine_prob[company_name]["Combined_Prob_positive"]* 100
        combine_prob_positive=round(combine_prob_positive,3)
        combine_prob_negative=combine_prob[company_name]["Combined_Prob_negative"]* 100
        combine_prob_negative=round(combine_prob_negative)
     

        # Build the formatted string
        analysis = f"""🚀 {company_name} Ai driven Analysis for Day Trading: 24h Opportunity? 📈
        Date and Time: {current_time}

    🔍 Market Sentiment (Last 24h)"""
        
        # Add sentiment analysis
        if news_data['news_count'] > 0:
            analysis += f" Sentiment towards {company_name} is {news_data['sentiment'].lower()}\n\n"
            analysis += f"📊 Sentiment statistics: \n"
            analysis += f"-Positive: {combine_prob_positive}% \n"
            analysis += f"-Negative: {combine_prob_negative}% \n\n"
            
            analysis += f"🗞 News Sample: \n"
            for article in news_data['articles'][:2]:
                emoji = "📉" if "Negative" in article['sentiment'] else "📈" if "Positive" in article['sentiment'] else "➡️"
                analysis += f"{emoji} {article['sentiment'].replace('📈 ', '').replace('📉 ', '').replace('➡️ ', '')}: {article['title'][:60]}... ({article['publisher']})\n"
        else:
            analysis += f"\nLimited news data available for {company_name}.\n\n"
        
        analysis += "Summary: Market conditions suggest exploitable volatility.\n\n"
        
        # Technical Analysis Section
        analysis += "✅ Technical Analysis (Intraday)\n"
        
        if technical:
            analysis += f"Current Price: ${technical['current_price']:.2f}\n"
            analysis += f"Volume: {technical['volume']:,.0f} (vs average)\n"
            
            # Key levels (calculated from technical data)
            resistance = technical['current_price'] * 1.015  # 1.5% above current
            support_primary = technical['current_price'] * 0.985  # 1.5% below current
            support_secondary = technical['current_price'] * 0.97  # 3% below current
            
            analysis += "\n\nKey Levels:\n"
            analysis += f"🛡️ Resistance: ${resistance:.2f}\n"
            analysis += f"🛡️ Support: ${support_primary:.2f} (primary), ${support_secondary:.2f} (secondary)\n"
            
            # Indicators
            analysis += "\n\nIndicators:\n"
            analysis += f"RSI (15 min): {technical['rsi']:.0f} - {'Overbought' if technical['rsi'] > 70 else 'Oversold' if technical['rsi'] < 30 else 'Neutral'}\n\n"
            
            # Bollinger Bands position
            analysis += f"Bollinger Bands: {technical['price_vs_bb']}\n"
            
            # Trend analysis
            if technical['current_price'] > technical['ma_20']:
                analysis += "Pattern: Bullish momentum above 20-day MA\n"
            else:
                analysis += "Pattern: Bearish pressure below 20-day MA\n\n"
            
            # Signals
            analysis += "Signals:\n"
            if technical['current_price'] > technical['ma_50']:
                analysis += f"🟢 Bullish: Potential rally to ${resistance:.2f} if momentum holds\n\n"
            else:
                analysis += f"🔴 Bearish: Risk of decline to ${support_secondary:.2f} if support breaks\n\n"
        
        # Real-time data section
        analysis += "📊 Real-time Data\n"
        if fundamentals:
            analysis += f"Market Cap: {self.format_large_number(fundamentals.get('market_cap'))}\n"
            analysis += f"P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}\n"
            analysis += f"Sector: {fundamentals.get('sector', 'N/A')}\n"
        
        if technical:
            analysis += f"52-week High: ${technical['52_week_high']:.2f}\n"
            analysis += f"52-week Low: ${technical['52_week_low']:.2f}\n"
            analysis += f"YTD Return: {technical['ytd_return']:.1f}%\n\n"
        
        # Trading strategies
        analysis += "🛠️ Strategies for Next 24h\n"
        
        if technical:
            entry_long = technical['current_price'] * 1.008  # 0.8% above current
            target_long = technical['current_price'] * 1.02  # 2% above current
            stop_long = technical['current_price'] * 0.985   # 1.5% below current
            
            entry_short = technical['current_price'] * 0.992  # 0.8% below current
            target_short = technical['current_price'] * 0.975 # 2.5% below current
            stop_short = technical['current_price'] * 1.006   # 0.6% above current
            
            analysis += "Bullish:\n"
            analysis += f"Entry: Buy if breaks ${entry_long:.2f} with volume\n"
            analysis += f"Target: ${target_long:.2f}\n"
            analysis += f"Stop-loss: ${stop_long:.2f}\n"
            
            analysis += "Bearish:\n"
            analysis += f"Entry: Short if drops below ${entry_short:.2f}\n"
            analysis += f"Target: ${target_short:.2f}\n"
            analysis += f"Stop-loss: ${stop_short:.2f}\n"
        
        analysis += "Monitor: News and volume in real-time.\n\n\n"
        
        # Risks section
        analysis += "⚠️ Risks\n"
        analysis += f"Volatility: Sharp movements common in ${ticker}\n\n"
        analysis += "News: Company announcements can change direction\n\n"
        
        analysis += "Disclaimer: For informational purposes only. Day trading is high risk."
        
        return analysis
    

#idk where put this method
def get_company_analysis(company_name):
    """
    Get Twitter-formatted analysis for any company.
    
    Args:
        company_name (str): Company name ('Tesla', 'Apple', 'Microsoft', etc.)
    
    Returns:
        str: Formatted analysis string ready for Twitter
    """
    analyzer = TwitterFormattedAnalyzer()
    return analyzer.format_twitter_analysis(company_name)

def post_company_analysis(company_name):
    """Get analysis for a company and post it to Twitter"""
    
    print(f"📊 Getting analysis for {company_name}...")
    
    # Get the formatted analysis
    analysis = get_company_analysis(company_name) 
    
    # Post to Twitter
    print("📤 Posting to Twitter...")
    bot.create_tweet(analysis)
    
    print("✅ Done!")
    return analysis


