import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import bot

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
    
    def get_news_sentiment(self, ticker, company_name):
        """Get news sentiment for a company"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return {'sentiment': 'No news available', 'news_count': 0, 'articles': []}
            
            # Keywords for sentiment analysis
            positive_keywords = ['beat', 'surge', 'gains', 'up', 'bull', 'optimistic', 'positive', 'growth', 'rise', 'boost', 'strong', 'record', 'profit', 'revenue', 'upgrade']
            negative_keywords = ['miss', 'fall', 'drop', 'down', 'bear', 'decline', 'concern', 'worry', 'risk', 'volatile', 'weak', 'loss', 'downgrade', 'cut', 'lower']
            
            analyzed_articles = []
            total_positive = 0
            total_negative = 0
            
            for article in news[:5]:  # Analyze top 5 news articles
                try:
                    content = article.get('content', {})
                    if not content:
                        continue
                    
                    title = content.get('title', 'No title')
                    text_to_analyze = (title + ' ' + content.get('summary', '')).lower()
                    
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
                        'publisher': content.get('provider', {}).get('displayName', 'Unknown')
                    })
                    
                except Exception:
                    continue
            
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
                'negative_count': total_negative,
                'articles': analyzed_articles
            }
            
        except Exception as e:
            print(f"Error getting news for {ticker}: {e}")
            return {'sentiment': 'Error getting news', 'news_count': 0, 'articles': []}
    
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
        #if not ticker:
        #     print(f"Company {company_name} not found in database")
        #     return
        
        # print("=" * 80)
        # print(f"📊 COMPREHENSIVE ANALYSIS: {company_name.upper()} ({ticker})")
        # print("=" * 80)
        
        # # 1. Fundamental Analysis
        # print(f"\n💼 FUNDAMENTAL ANALYSIS")
        # print("-" * 40)
        fundamentals = self.get_company_fundamentals(ticker)
        
        if fundamentals:
           # print(f"Market Cap: {self.format_large_number(fundamentals.get('market_cap'))}")
            large_tweet["market_cap: "]=str(self.format_large_number(fundamentals.get('market_cap')))
            large_tweet["P/E Ratio: "]=str(fundamentals.get('pe_ratio', 'N/A'))
            large_tweet["Dividend Yield: "]=str(self.format_percentage(fundamentals.get('dividend_yield')))
            large_tweet["Sector: "]=str(fundamentals.get('sector', 'N/A'))


         
            
            # print(f"P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}")
            # print(f"Dividend Yield: {self.format_percentage(fundamentals.get('dividend_yield'))}")
            # print(f"Sector: {fundamentals.get('sector', 'N/A')}")
            #print(f"Forward P/E: {fundamentals.get('forward_pe', 'N/A')}")
            #print(f"Price-to-Book: {fundamentals.get('price_to_book', 'N/A')}")
            #print(f"Debt-to-Equity: {fundamentals.get('debt_to_equity', 'N/A')}")
            # print(f"Return on Equity: {self.format_percentage(fundamentals.get('return_on_equity'))}")
            # print(f"Profit Margin: {self.format_percentage(fundamentals.get('profit_margin'))}")
            # print(f"Revenue Growth: {self.format_percentage(fundamentals.get('revenue_growth'))}")
            #print(f"Beta: {fundamentals.get('beta', 'N/A')}")
            #print(f"Employees: {fundamentals.get('employees', 'N/A'):,}" if fundamentals.get('employees') != 'N/A' else "Employees: N/A")
            
            
        
        # 2. Technical Analysis
      #  print(f"\n📈 TECHNICAL ANALYSIS")
       # print("-" * 40)
        technical = self.get_technical_analysis(ticker)
        
        if technical:
            #print(f"Current Price: ${technical['current_price']:.2f}")
            large_tweet["Current Price: "]=str(technical['current_price'])
           # print(f"20-day MA: ${technical['ma_20']:.2f}")
           # print(f"50-day MA: ${technical['ma_50']:.2f}")
            #print(f"200-day MA: ${technical['ma_200']:.2f}")
            #print(f"RSI: {technical['rsi']:.2f}")
            #print(f"Bollinger Bands: {technical['price_vs_bb']}")
            #print(f"52-week High: ${technical['52_week_high']:.2f}")
            #print(f"52-week Low: ${technical['52_week_low']:.2f}")
            #print(f"Distance from High: {technical['distance_from_high']:.1f}%")
            #print(f"Distance from Low: {technical['distance_from_low']:.1f}%")
            
            # print(f"\n📊 PERFORMANCE:")
            # print(f"YTD Return: {technical['ytd_return']:.1f}%")
            # print(f"1-Month Return: {technical['month_return']:.1f}%")
            # print(f"1-Year Return: {technical['year_return']:.1f}%")
            
            # print(f"\n🔍 TECHNICAL SIGNALS:")
            # if technical['current_price'] > technical['ma_200']:
            #     print("• Long-term trend: 🟢 BULLISH (above 200-day MA)")
            # else:
            #     print("• Long-term trend: 🔴 BEARISH (below 200-day MA)")
            
            # if technical['rsi'] > 70:
            #     print("• RSI: 🔴 OVERBOUGHT (>70)")
            # elif technical['rsi'] < 30:
            #     print("• RSI: 🟢 OVERSOLD (<30)")
            # else:
            #     print("• RSI: 🟡 NEUTRAL (30-70)")
        
        # 3. News Sentiment
       # print(f"\n📰 NEWS SENTIMENT ANALYSIS")
       # print("-" * 40)
        news_data = self.get_news_sentiment(ticker, company_name)
        #print(f"Overall Sentiment: {news_data['sentiment']}")
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
        
        # # 4. Valuation Assessment
        # print(f"\n💰 VALUATION ASSESSMENT")
        # print("-" * 40)
        # if fundamentals:
        #     assessments = self.get_valuation_assessment(fundamentals)
        #     for assessment in assessments:
        #         print(f"• {assessment}")
        
        # 5. Business Overview
        # if fundamentals and fundamentals.get('business_summary'):
        #     print(f"\n🏢 BUSINESS OVERVIEW")
        #     print("-" * 40)
        #     summary = fundamentals['business_summary'][:400] + "..." if len(fundamentals['business_summary']) > 400 else fundamentals['business_summary']
        #     print(summary)
        
        # print(f"\n⚠️ DISCLAIMER: This analysis is for informational purposes only and should not be considered investment advice.")
        # print("=" * 80)
        return large_tweet
    

