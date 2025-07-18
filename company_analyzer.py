import yfinance as yf
from datetime import datetime
import working_wjson as wj
import news 
import bot


class CompanyAnalyzer:
    def get_single_company_sentiment_metrics(self, company):
        """Calculate and return sentiment metrics for a single company from all sources, ignoring sources with zero data."""
        import working_wjson as wj
        # Step 1: Data Collection Phase
        x_news = wj.load_from_json('data/x_tweets.json').get(company, {})
        y_news = wj.load_from_json('data/yf_news.json').get(company, {})
        g_news = wj.load_from_json('data/google_news.json').get(company, {})
        # Step 2: Sentiment Analysis Phase
        x_sentiment = self.get_news_sentiment(x_news)
        y_sentiment = self.get_news_sentiment(y_news)
        g_sentiment = self.get_news_sentiment(g_news)
        # Step 3: Only include sources with news_count > 0
        sources = []
        metrics = {}
        def sigfig(x, n=2):
            if x == 0:
                return 0.0
            s = f"{x:.{n}g}"
            if 'e' not in s and '.' in s:
                int_part, dec_part = s.split('.')
                if len(dec_part) < n-1:
                    s += '0' * (n-1 - len(dec_part))
            return float(s)
        if x_sentiment['news_count'] > 0:
            metrics['P_X'] = sigfig(x_sentiment['positive_porcent'] / 100)
            metrics['N_X'] = sigfig(x_sentiment['negative_porcent'] / 100)
            metrics['sample_X'] = x_sentiment['news_count']
            sources.append('X')
        if y_sentiment['news_count'] > 0:
            metrics['P_Y'] = sigfig(y_sentiment['positive_porcent'] / 100)
            metrics['N_Y'] = sigfig(y_sentiment['negative_porcent'] / 100)
            metrics['sample_Y'] = y_sentiment['news_count']
            sources.append('Yahoo')
        if g_sentiment['news_count'] > 0:
            metrics['P_G'] = sigfig(g_sentiment['positive_porcent'] / 100)
            metrics['N_G'] = sigfig(g_sentiment['negative_porcent'] / 100)
            metrics['sample_G'] = g_sentiment['news_count']
            sources.append('Google')
        # Add debug output to show which sources are used
        print(f"[DEBUG] Sentiment sources used for {company}: {sources}")
        if not sources:
            print(f"[DEBUG] No sentiment data found for {company} (all sources empty)")
        return metrics
    def __init__(self):
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
        if news is None or (isinstance(news, dict) and len(news.keys()) == 0):
            return {
                'sentiment': 'No news available', 
                'news_count': 0, 
                'positive_count': 0,
                'positive_porcent': 0,
                'negative_count': 0,
                'negative_porcent': 0,
                'articles': []
            }
            
        # Keywords for sentiment analysis
            # Expanded positive keywords list
       
        positive_keywords = [w.lower() for w in wj.load_from_json('data/positive_keywords.json')]
        negative_keywords = [w.lower() for w in wj.load_from_json('data/negative_keywords.json')]
         
        analyzed_articles = []
        total_positive = 0
        total_negative = 0
        #news will be a dict {title: "lalal", summary: "llalal", provider:"lalal"}
        for article in news.keys():
            title = news[article]['title']
            text_to_analyze = (title + ' ' + news[article]['summary']).lower()
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
            
        # Calculate percentages safely (avoid division by zero)
        if len(analyzed_articles) > 0:
            positive_porcent = total_positive*100/len(analyzed_articles)
            negative_porcent = total_negative*100/len(analyzed_articles)
        else:
            positive_porcent = 0
            negative_porcent = 0
        
        return {
            'sentiment': overall_sentiment,
            'news_count': len(analyzed_articles),
            'positive_count': total_positive,
            'positive_porcent': positive_porcent,
            'negative_count': total_negative,
            'negative_porcent': negative_porcent,
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
    def get_news_sentiment(self, news):
        """Get news sentiment for a company. Accepts dict or list of articles."""
        if news is None or (isinstance(news, dict) and len(news.keys()) == 0) or (isinstance(news, list) and len(news) == 0):
            return {
                'sentiment': 'No news available',
                'news_count': 0,
                'positive_count': 0,
                'positive_porcent': 0,
                'negative_count': 0,
                'negative_porcent': 0,
                'articles': []
            }
        positive_keywords = [w.lower() for w in wj.load_from_json('data/positive_keywords.json')]
        negative_keywords = [w.lower() for w in wj.load_from_json('data/negative_keywords.json')]
        analyzed_articles = []
        total_positive = 0
        total_negative = 0
        # Accept both dict and list
        articles = []
        if isinstance(news, dict):
            for k in news.keys():
                articles.append(news[k])
        elif isinstance(news, list):
            articles = news
        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', '')
            text_to_analyze = (title + ' ' + summary).lower()
            matched_pos = [word for word in positive_keywords if word in text_to_analyze]
            matched_neg = [word for word in negative_keywords if word in text_to_analyze]
            positive_score = len(matched_pos)
            negative_score = len(matched_neg)
            if positive_score > negative_score:
                sentiment = "📈 Positive"
                total_positive += 1
            elif negative_score > positive_score:
                sentiment = "📉 Negative"
                total_negative += 1
            else:
                sentiment = "➡️ Neutral"
            print(f"[DEBUG] Article: {title[:80]}...")
            print(f"         Sentiment: {sentiment} | Pos: {positive_score} ({matched_pos}) | Neg: {negative_score} ({matched_neg})")
            analyzed_articles.append({
                'title': title,
                'sentiment': sentiment,
                'publisher': article.get("provider", "?")
            })
        if total_positive > total_negative:
            overall_sentiment = "📈 Overall Positive"
        elif total_negative > total_positive:
            overall_sentiment = "📉 Overall Negative"
        else:
            overall_sentiment = "➡️ Overall Neutral"
        if len(analyzed_articles) > 0:
            positive_porcent = total_positive * 100 / len(analyzed_articles)
            negative_porcent = total_negative * 100 / len(analyzed_articles)
        else:
            positive_porcent = 0
            negative_porcent = 0
        print(f"[DEBUG] Total: {len(analyzed_articles)} | Positive: {total_positive} | Negative: {total_negative} | Neutral: {len(analyzed_articles) - total_positive - total_negative}")
        return {
            'sentiment': overall_sentiment,
            'news_count': len(analyzed_articles),
            'positive_count': total_positive,
            'positive_porcent': positive_porcent,
            'negative_count': total_negative,
            'negative_porcent': negative_porcent,
            'articles': analyzed_articles
        }

        
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

        # Step 4: Return Standardized Metrics (rounded to 3 significant figures)
        def sigfig(x, n=2):
            if x == 0:
                return 0.0
            # Use format to round to n significant digits, always as float
            s = f"{x:.{n}g}"
            # Ensure trailing zero for e.g. 0.80, 0.20
            if 'e' not in s and '.' in s:
                int_part, dec_part = s.split('.')
                if len(dec_part) < n-1:
                    s += '0' * (n-1 - len(dec_part))
            return float(s)
        return {
            'P_X': sigfig(positive_x_ratio),     # X positive sentiment ratio (0.0-1.0)
            'N_X': sigfig(negative_x_ratio),     # X negative sentiment ratio (0.0-1.0)
            'P_Y': sigfig(positive_y_ratio),     # Yahoo Finance positive sentiment ratio
            'N_Y': sigfig(negative_y_ratio),     # Yahoo Finance negative sentiment ratio
            'P_G': sigfig(positive_g_ratio),     # Google News positive sentiment ratio
            'N_G': sigfig(negative_g_ratio),     # Google News negative sentiment ratio
            'sample_X': sample_size_x,   # Number of X posts analyzed
            'sample_Y': sample_size_y,   # Number of Yahoo Finance articles analyzed
            'sample_G': sample_size_g    # Number of Google News articles analyzed
        }
      
    def get_company_name_from_ticker(self,ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            name = info.get('shortName') 
            if not name:
                name = info.get('longName', ticker)
                # Limpiar sufijos si es longName
                for suffix in [' Inc.', ' Inc', ' Corporation', ' Corp']:
                    if name.endswith(suffix):
                        name = name[:-len(suffix)]
                        break
            return str(name)  # Devuelve el nombre completo
        except:
            return str(ticker)  # Si falla, devuelve el ticker
      
    def get_multi_source_sentiment_analysis(self, companies=None, queries_path='data/queries_x.json'):
        """
        Performs comprehensive sentiment analysis ONLY for the provided list of companies.
        If companies is None or empty, does nothing.
        """
        if not companies:
            return {}
        # Load platform-specific search queries for each company (if needed)
        queries = wj.load_from_json(queries_path)
        total_data = {}
        for company in companies:
            total_data[company] = self.get_single_company_sentiment_metrics(company)
        wj.save_to_json(total_data, 'data/data_total_analyze.json')
        return total_data

class TwitterFormattedAnalyzer(CompanyAnalyzer):
    def __init__(self):
        super().__init__()
        self.political_uncertity=wj.load_from_json('data/uncertity_per_company.json')
        self.news_extractor= news.NewsExtractor()
    
    def format_twitter_analysis(self, company_name='Tesla', ticker=None):
        """Generate a Twitter-formatted analysis string for a company, aggregating news from all sources."""
        if ticker is None:
            ticker = self.companies.get(company_name)
            if not ticker:
                return f"Company {company_name} not found in database"

        fundamentals = self.get_company_fundamentals(ticker)
        technical = self.get_technical_analysis(ticker)

        # Always convert news dicts to lists before merging
        news_x_dict = wj.load_from_json('data/x_tweets.json').get(company_name, {})
        news_y_dict = wj.load_from_json('data/yf_news.json').get(company_name, {})
        news_g_dict = wj.load_from_json('data/google_news.json').get(company_name, {})
        news_x = list(news_x_dict.values()) if isinstance(news_x_dict, dict) else []
        news_y = list(news_y_dict.values()) if isinstance(news_y_dict, dict) else []
        news_g = list(news_g_dict.values()) if isinstance(news_g_dict, dict) else []
        print(f"[DEBUG] News counts for {company_name}: X={len(news_x)}, Y={len(news_y)}, G={len(news_g)}")
        all_articles = news_x + news_y + news_g
        print(f"[DEBUG] Total merged news articles for {company_name}: {len(all_articles)}")
        news_data = self.get_news_sentiment(all_articles)
        if news_data is None or news_data['news_count'] == 0:
            print(f"Warning: No news data found for {company_name} in any source.")
            news_data = self.get_news_sentiment(None)

        current_time = datetime.now().strftime('%B %d, %Y, %H:%M MDT')

        # Use real-time sentiment statistics from news_data for posted analysis
        real_positive = news_data.get('positive_porcent', 0.0)
        real_negative = news_data.get('negative_porcent', 0.0)
        real_neutral = 100.0 - real_positive - real_negative
        # Split neutral equally between positive and negative
        real_positive_final = real_positive + real_neutral / 2
        real_negative_final = real_negative + real_neutral / 2
        # Ensure sum is exactly 100.0 (handle floating point)
        total = real_positive_final + real_negative_final
        if abs(total - 100.0) > 0.01:
            # Normalize
            real_positive_final = real_positive_final * 100.0 / total
            real_negative_final = real_negative_final * 100.0 / total
     
        # Find the company name in political_uncertity (case-insensitive)
        political_uncertity_key = None
        for key in self.political_uncertity.keys():
            if key.lower() == company_name.lower():
                political_uncertity_key = key
                break
        
        # Use default value if company not found
        if political_uncertity_key:
            political_value = self.political_uncertity[political_uncertity_key]
        else:
            print(f"Warning: No political uncertainty data found for {company_name}, using default")
            political_value = 5  # Default moderate uncertainty
        
        if political_value<=2:
            uncertity=' Very Low '
        elif 2<political_value<=4:
            uncertity=' Low '
        elif 4< political_value<=6:
            uncertity=' Moderate'
        elif 6< political_value <= 8:
            uncertity=' High'
        else:
            uncertity='Very High'

        # Build the formatted string
        analysis = f"🚀 {company_name} Ai driven Analysis for Day Trading: 24h Opportunity? 📈\n"
        analysis += f"Date and Time: {current_time}\n\n"
        analysis += f"🔍 Market Sentiment (Last 24h)\n"

        # Add sentiment analysis
        if news_data['news_count'] > 0:
            analysis += f"Sentiment towards {company_name} is {news_data['sentiment'].lower()}\n\n"
            analysis += f"📊 Sentiment statistics: \n"
            analysis += f"-Positive: {real_positive_final:.1f}% \n"
            analysis += f"-Negative: {real_negative_final:.1f}% \n\n"
            analysis += f"🗞 News Sample: \n"
            for article in news_data['articles'][:2]:
                analysis += f"🧙‍♂ {article['title'][:60]}... ({article['publisher']})\n"
        else:
            analysis += f"\nLimited news data available for {company_name}.\n\n"

        analysis += "Summary: Market conditions suggest exploitable volatility.\n\n"
        analysis += f"🌪 Political Uncertainty: {uncertity}\n\n"

        # Technical Analysis Section
        analysis += "✅ Technical Analysis (Intraday)\n"

        if technical:
            analysis += f"Current Price: ${technical['current_price']:.2f}\n"
            analysis += f"Volume: {technical['volume']:,.0f} (vs average)\n"

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

        # Add 52-week high/low and YTD return
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
        
        analysis += "Monitor: News and volume in real-time.\n\n"
        
        # Risks section
        analysis += "⚠️ Risks\n"
        analysis += f"Volatility: Sharp movements common in ${ticker}\n\n"
        analysis += "News: Company announcements can change direction\n\n"
        
        analysis += "Disclaimer: For informational purposes only. Day trading is high risk."

        # Fallback: If analysis is None or empty, return a default message
        if not analysis or analysis.strip() == "":
            analysis = f"[INFO] No detailed analysis available for {company_name} at this time."
        return analysis
    def generate_ai_analysis(self, ticker, company_name=None):
        """
        Returns cached analysis for a ticker if available and fresh (10 min), else generates new and updates cache.
        Only analyzes the provided ticker/company, never all companies. Robust error handling.
        """
        if not ticker:
            return "[ERROR] No ticker provided for analysis."
        cache_key = ticker
        import time
        now = time.time()
        # Check cache
        if cache_key in self.company_analysis_cache:
            ts, cached_analysis = self.company_analysis_cache[cache_key]
            if now - ts < 600:  # 10 minutes
                return cached_analysis
        # Not cached or expired, generate new analysis
        try:
            import company_analyzer as ca
            analysis = ca.get_company_analysis(company_name, ticker)
        except Exception as e:
            return f"[ERROR] Could not generate analysis for {ticker}: {e}"
        # RSS feed code fully removed
        self.company_analysis_cache[cache_key] = (now, analysis)
        return analysis
        
        analysis += "Monitor: News and volume in real-time.\n\n\n"
        
        # Risks section
        analysis += "⚠️ Risks\n"
        analysis += f"Volatility: Sharp movements common in ${ticker}\n\n"
        analysis += "News: Company announcements can change direction\n\n"
        
        analysis += "Disclaimer: For informational purposes only. Day trading is high risk."
        
        return analysis
    

#idk where put this method
def get_company_analysis(company_name=None,ticker=None):
    """
    Get Twitter-formatted analysis for any company.
    
    Args:
        company_name (str): Company name ('Tesla', 'Apple', 'Microsoft', etc.)
    
    Returns:
        str: Formatted analysis string ready for Twitter
    """
    analyzer = TwitterFormattedAnalyzer()
    # Only analyze the provided ticker/company, never all companies
    if ticker is not None:
        if company_name is None:
            try:
                company_name = analyzer.get_company_name_from_ticker(ticker)
            except Exception as e:
                return f"[ERROR] Could not resolve company name for ticker {ticker}: {e}"
        # Step 1: Update queries and extract news
        try:
            print(f"[TRIGGER] Step 1: Updating queries and extracting news for {company_name} ({ticker})")
            analyzer.news_extractor.update_queries(ticker, company_name)
        except Exception as e:
            return f"[ERROR] Could not update queries for {company_name} ({ticker}): {e}"
        # Step 2: Update all JSONs (news, sentiment, political, etc.)
        try:
            print(f"[TRIGGER] Step 2: Updating all JSONs for {company_name} ({ticker})")
            import updater_jsons
            updater = updater_jsons.updater_data()
            updater.update_all_json(company_name, ticker)
        except Exception as e:
            return f"[ERROR] Could not update news/JSONs for {company_name} ({ticker}): {e}"
        # Step 3: Check that news is present before analysis
        import working_wjson as wj
        news_x = wj.load_from_json('data/x_tweets.json').get(company_name, {})
        news_y = wj.load_from_json('data/yf_news.json').get(company_name, {})
        news_g = wj.load_from_json('data/google_news.json').get(company_name, {})
        total_news = 0
        if isinstance(news_x, dict):
            total_news += len(news_x)
        if isinstance(news_y, dict):
            total_news += len(news_y)
        if isinstance(news_g, dict):
            total_news += len(news_g)
        print(f"[TRIGGER] Step 3: News counts for {company_name}: X={len(news_x) if isinstance(news_x, dict) else 0}, Y={len(news_y) if isinstance(news_y, dict) else 0}, G={len(news_g) if isinstance(news_g, dict) else 0}, Total={total_news}")
        if total_news == 0:
            return f"[ERROR] No news found for {company_name} ({ticker}). Analysis cannot proceed."
        # Step 4: Run analysis/formatting only if news is present
        print(f"[TRIGGER] Step 4: Running analysis/formatting for {company_name} ({ticker})")
        analysis = analyzer.format_twitter_analysis(company_name, ticker)
        if not analysis or analysis is None or (isinstance(analysis, str) and analysis.strip() == ""):
            return f"[ERROR] Analysis failed for {company_name} ({ticker}) despite news being present."
        return analysis
    else:
        return "[ERROR] No ticker provided for analysis."
        


    return analyzer.format_twitter_analysis(company_name,ticker)

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

if __name__ == "__main__":
    print(get_company_analysis(ticker='AMD'))




