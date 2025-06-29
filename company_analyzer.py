import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import bot
import working_wjson as wj

class CompanyAnalyzer:
    def __init__(self):
        # Top 5 tech companies with their ticker symbols
        self.companies = wj.load_from_json('data/companies.json')
    
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
    
    def analyze_single_company(self,news, company_name):
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
         
    
        news_data = self.get_news_sentiment(news,ticker, company_name)
        large_tweet["Overall Sentiment: "]=str(news_data['sentiment'])
        large_tweet["Recent Articles Analyzed: "]=str(news_data['news_count'])

        if news_data['news_count'] > 0:
            news=[]
            for article in news_data['articles'][:3]:
                news.append(f"{article['sentiment']} {article['title'][:80]}...Source: {article['publisher']}")
           # print(news)
        large_tweet['news']=news
      
        return large_tweet
    
class TwitterFormattedAnalyzer(CompanyAnalyzer):
    def __init__(self):
        super().__init__()
    
    def format_twitter_analysis(self, company_name):
        """Generate a Twitter-formatted analysis string for a company"""
        ticker = self.companies.get(company_name)
        if not ticker:
            return f"Company {company_name} not found in database"
        
        # Get all the data
        fundamentals = self.get_company_fundamentals(ticker)
        technical = self.get_technical_analysis(ticker)
        news=self.yf_news(ticker)
        news_data = self.get_news_sentiment(news)
        
        # Current date and time
        current_time = datetime.now().strftime('%B %d, %Y, %H:%M MDT')
        
        # Build the formatted string
        analysis = f"""🚀 {company_name} Ai driven Analysis for Day Trading: 24h Opportunity? 📈
        Date and Time: {current_time}

    🔍 Market Sentiment (Last 24h)"""
        
        # Add sentiment analysis
        if news_data['news_count'] > 0:
            analysis += f" Sentiment towards {company_name} is {news_data['sentiment'].lower()}:\n\n"
            
            for article in news_data['articles'][:3]:
                emoji = "📉" if "Negative" in article['sentiment'] else "📈" if "Positive" in article['sentiment'] else "➡️"
                analysis += f"{emoji} {article['sentiment'].replace('📈 ', '').replace('📉 ', '').replace('➡️ ', '')}: {article['title'][:60]}... ({article['publisher']})\n"
        else:
            analysis += f"\nLimited news data available for {company_name}.\n\n"
        
        analysis += "Summary: Market conditions suggest exploitable volatility.\n\n"
        
        # Technical Analysis Section
        analysis += "📈 Technical Analysis (Intraday)\n"
        
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


