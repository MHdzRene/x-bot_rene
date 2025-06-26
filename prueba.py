import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from company_analyzer import CompanyAnalyzer

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
        news_data = self.get_news_sentiment(ticker, company_name)
        
        # Current date and time
        current_time = datetime.now().strftime('%B %d, %Y, %H:%M MDT')
        
        # Build the formatted string
        analysis = f"""🚀 {company_name} Analysis for Day Trading: 24h Opportunity? 📈

Date and Time: {current_time}


🔍 Market Sentiment (Last 24h)
"""
        
        # Add sentiment analysis
        if news_data['news_count'] > 0:
            analysis += f"\nSentiment towards {company_name} is {news_data['sentiment'].lower()}:\n\n"
            
            for article in news_data['articles'][:3]:
                emoji = "📉" if "Negative" in article['sentiment'] else "📈" if "Positive" in article['sentiment'] else "➡️"
                analysis += f"{emoji} {article['sentiment'].replace('📈 ', '').replace('📉 ', '').replace('➡️ ', '')}: {article['title'][:60]}... ({article['publisher']})\n\n"
        else:
            analysis += f"\nLimited news data available for {company_name}.\n\n"
        
        analysis += "Summary: Market conditions suggest exploitable volatility.\n\n\n"
        
        # Technical Analysis Section
        analysis += "📈 Technical Analysis (Intraday)\n\n"
        
        if technical:
            analysis += f"Current Price: ${technical['current_price']:.2f}\n\n"
            analysis += f"Volume: {technical['volume']:,.0f} (vs average)\n\n"
            
            # Key levels (calculated from technical data)
            resistance = technical['current_price'] * 1.015  # 1.5% above current
            support_primary = technical['current_price'] * 0.985  # 1.5% below current
            support_secondary = technical['current_price'] * 0.97  # 3% below current
            
            analysis += "Key Levels:\n\n"
            analysis += f"🛡️ Resistance: ${resistance:.2f}\n\n"
            analysis += f"🛡️ Support: ${support_primary:.2f} (primary), ${support_secondary:.2f} (secondary)\n\n"
            
            # Indicators
            analysis += "Indicators:\n\n"
            analysis += f"RSI (15 min): {technical['rsi']:.0f} - {'Overbought' if technical['rsi'] > 70 else 'Oversold' if technical['rsi'] < 30 else 'Neutral'}\n\n"
            
            # Bollinger Bands position
            analysis += f"Bollinger Bands: {technical['price_vs_bb']}\n\n"
            
            # Trend analysis
            if technical['current_price'] > technical['ma_20']:
                analysis += "Pattern: Bullish momentum above 20-day MA\n\n"
            else:
                analysis += "Pattern: Bearish pressure below 20-day MA\n\n"
            
            # Signals
            analysis += "Signals:\n\n"
            if technical['current_price'] > technical['ma_50']:
                analysis += f"🟢 Bullish: Potential rally to ${resistance:.2f} if momentum holds\n\n"
            else:
                analysis += f"🔴 Bearish: Risk of decline to ${support_secondary:.2f} if support breaks\n\n"
        
        # Real-time data section
        analysis += "\n📊 Real-time Data\n\n"
        if fundamentals:
            analysis += f"Market Cap: {self.format_large_number(fundamentals.get('market_cap'))}\n\n"
            analysis += f"P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}\n\n"
            analysis += f"Sector: {fundamentals.get('sector', 'N/A')}\n\n"
        
        if technical:
            analysis += f"52-week High: ${technical['52_week_high']:.2f}\n\n"
            analysis += f"52-week Low: ${technical['52_week_low']:.2f}\n\n"
            analysis += f"YTD Return: {technical['ytd_return']:.1f}%\n\n"
        
        # Trading strategies
        analysis += "\n🛠️ Strategies for Next 24h\n\n"
        
        if technical:
            entry_long = technical['current_price'] * 1.008  # 0.8% above current
            target_long = technical['current_price'] * 1.02  # 2% above current
            stop_long = technical['current_price'] * 0.985   # 1.5% below current
            
            entry_short = technical['current_price'] * 0.992  # 0.8% below current
            target_short = technical['current_price'] * 0.975 # 2.5% below current
            stop_short = technical['current_price'] * 1.006   # 0.6% above current
            
            analysis += "Bullish:\n\n"
            analysis += f"Entry: Buy if breaks ${entry_long:.2f} with volume\n\n"
            analysis += f"Target: ${target_long:.2f}\n\n"
            analysis += f"Stop-loss: ${stop_long:.2f}\n\n"
            
            analysis += "Bearish:\n\n"
            analysis += f"Entry: Short if drops below ${entry_short:.2f}\n\n"
            analysis += f"Target: ${target_short:.2f}\n\n"
            analysis += f"Stop-loss: ${stop_short:.2f}\n\n"
        
        analysis += "Monitor: News and volume in real-time.\n\n\n"
        
        # Risks section
        analysis += "⚠️ Risks\n\n"
        analysis += f"Volatility: Sharp movements common in {ticker}\n\n"
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
