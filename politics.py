from datetime import datetime
from typing import Dict, List
import working_wjson as wj  # Assuming this is your JSON utility module
import news as nw
from transformers import pipeline
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ollama_config import OllamaClient, OLLAMA_CONFIG 

class PoliticalUncertaintyAnalyzer:
    """
    analyzer for political uncertainty impact on company stock value.
    Outputs a single score per company based on news and sector risks.
    return dict with this format: {company_name:[list of news]} 
    """
    def __init__(self, use_llm: bool = True):
        
        # Company to sector mapping
        self.company_sectors = wj.load_from_json('data/company_sectors.py')
        
        # Sector-specific political risk keywords and weights
        self.sector_risks = wj.load_from_json('data/sector_risks.py')

        #queries for get political news
        self.political_queries=wj.load_from_json('data/political_news_queries.json')

        #news extractor(maybe no needeed)
        self.news_extractor=nw.NewsExtractor()
        
        # LLM Configuration - Supporting both HuggingFace and Ollama
        self.use_llm = use_llm
        self.llm_client = None
        self.ollama_client = None
        
        if self.use_llm:
            self._initialize_llm()
        
        # General political uncertainty keywords
        self.political_keywords = [
            'election', 'congress', 'senate', 'house', 'biden', 'trump',
            'federal reserve', 'fed', 'interest rates', 'inflation',
            'government shutdown', 'debt ceiling', 'budget', 'fiscal policy',
            'geopolitical', 'war', 'sanctions', 'trade agreement'
        ]
        
        # Intensity multipliers for different types of political events
        self.event_multipliers = {
            'election_year': 1.3,
            'policy_hearing': 1.5,
            'regulatory_announcement': 1.4,
            'trade_dispute': 1.2,
            'geopolitical_crisis': 1.6
        }
          
        
    def _initialize_llm(self):
        """Initialize both HuggingFace and Ollama LLM clients."""
        # Try Ollama first (faster and more powerful)
        self.ollama_client = OllamaClient()
        
        if self.ollama_client.is_available():
            models = self.ollama_client.list_models()
            if "llama2:7b" in models:
                print("✅ Ollama LLM (llama2:7b) initialized successfully")
                return
            else:
                print("⚠️ Ollama running but llama2:7b not found")
        else:
            print("⚠️ Ollama not available, falling back to HuggingFace")
        
        # Fallback to HuggingFace
        try:
            self.llm_client = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            print("✅ HuggingFace LLM initialized successfully")
                
        except ImportError as e:
            print(f"⚠️ HuggingFace transformers not available: {e}")
            print("💡 Install with: pip install transformers torch")
            self.use_llm = False
        except Exception as e:
            print(f"❌ Error initializing HuggingFace LLM: {e}")
            self.use_llm = False
 
    def get_news_data(self):
        start = time.time()
        
        news_per_company = {
            company: self.news_extractor.search_gnews_lits_of_topics(queries, 3)
            for company, queries in self.political_queries.items()
        }
        
        end = time.time()
        print('duration', end - start)
        return news_per_company
    
    def get_news_data_using_thread(self):
        start = time.time()
        
        def _fetch_company_news_throttled(self, company_queries_pair):
            company, queries = company_queries_pair
            try:
                # Rate limiting: pequeña pausa para evitar sobrecarga
                time.sleep(0.1)  
                news = self.news_extractor.search_gnews_lits_of_topics(queries, 1)
                return company, news
            except Exception as e:
                print(f"❌ Error fetching news for {company}: {e}")
                return company, []
        
        company_queries_pairs = list(self.political_queries.items())
        news_per_company = {}
        
        # Usar menos workers para evitar rate limiting
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_company = {
                executor.submit(_fetch_company_news_throttled, self, pair): pair[0] 
                for pair in company_queries_pairs
            }
            
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    company_name, news = future.result(timeout=60)
                    news_per_company[company_name] = news
                    print(f"✅ {company_name}: {len(news)} articles")
                except Exception as e:
                    print(f"❌ {company}: {e}")
                    news_per_company[company] = []
        
        end = time.time()
        print(f'Parallel duration: {end - start:.2f} seconds')
        return news_per_company
    
    def analyze_news_political_content(self,company_name, news_data: Dict) -> Dict:
        """
        Analyze news content for political uncertainty indicators.
        
        Returns:
            Dict with political analysis results
        """
        if not news_data:
            return {'political_score': 0, 'risk_factors': [], 'affected_articles': 0}
        
        political_articles = []
        total_political_score = 0
        risk_factors = set()
        count=0
        for article in news_data[company_name]:
            article_text=f"{article['title']}: {article['summary']}"
           
            
            # Check for general political content
            political_mentions = sum(1 for keyword in self.political_keywords if keyword in article_text)
            
            if political_mentions > 0:
                political_articles.append({
                    'id': count,
                    'title': article.get('title', ''),
                    'political_score': political_mentions,
                    'provider': article.get('provider', 'Unknown')
                })
                count=count+1
                
                total_political_score += political_mentions
                
                # Identify specific risk factors
                for keyword in self.political_keywords:
                    if keyword in article_text:
                        risk_factors.add(keyword)
        
        # Calculate normalized political uncertainty score (0-100)
        max_possible_score = len(news_data) * len(self.political_keywords)
        political_uncertainty_score = min(100, (total_political_score / max_possible_score) * 100) if max_possible_score > 0 else 0
        
        return {
            'political_score': round(political_uncertainty_score, 2),
            'risk_factors': list(risk_factors),
            'affected_articles': len(political_articles),
            'total_articles': len(news_data),
            'political_articles': political_articles[:5]  # Top 5 most political articles
        }
    
    def analyze_with_llm(self, text: str, analysis_type: str = "political_sentiment") -> Dict:
        """
        Analyze text using available LLM (Ollama or HuggingFace) for political sentiment insights.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis ('political_sentiment', 'risk_assessment', 'impact_analysis')
        
        Returns:
            Dict with LLM analysis results
        """
        if not self.use_llm:
            return {"error": "LLM not available", "fallback": True}
        
        try:
            # Try Ollama first
            if self.ollama_client and self.ollama_client.is_available():
                return self._analyze_with_ollama(text, analysis_type)
            # Fallback to HuggingFace
            elif self.llm_client:
                return self._analyze_with_huggingface(text, analysis_type)
            else:
                return {"error": "No LLM available", "fallback": True}
                
        except Exception as e:
            print(f"❌ LLM analysis error: {e}")
            return {"error": str(e), "fallback": True}
    
    def _analyze_with_ollama(self, text: str, analysis_type: str) -> Dict:
        """Analyze using Ollama llama2:7b model."""
        
        # Create specialized prompts for different analysis types
        if analysis_type == "political_sentiment":
            prompt = f"""
Analyze the political sentiment of this text and provide a JSON response:

Text: "{text}"

Please respond with a JSON object containing:
1. political_sentiment: "positive", "negative", or "neutral"
2. uncertainty_level: "low", "medium", or "high" 
3. confidence_score: a number between 0.0 and 1.0
4. key_political_topics: list of identified political topics

JSON Response:"""
            
        elif analysis_type == "risk_assessment":
            prompt = f"""
Analyze the business/political risk level of this text and provide a JSON response:

Text: "{text}"

Please respond with a JSON object containing:
1. risk_level: "low", "medium", or "high"
2. business_impact: "minimal", "moderate", or "significant"
3. confidence_score: a number between 0.0 and 1.0
4. risk_factors: list of identified risk factors

JSON Response:"""

        elif analysis_type == "impact_analysis":
            prompt = f"""
Analyze the potential business impact of this text and provide a JSON response:

Text: "{text}"

Please respond with a JSON object containing:
1. impact_level: "low", "medium", or "high"
2. affected_sectors: list of business sectors that might be affected
3. confidence_score: a number between 0.0 and 1.0
4. time_horizon: "short-term", "medium-term", or "long-term"

JSON Response:"""
        else:
            prompt = f"Analyze this text for political content: {text}"

        # Call Ollama
        response = self.ollama_client.generate("llama2:7b", prompt)
        
        if response and 'response' in response:
            llm_text = response['response']
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                import json
                
                # Find JSON-like content
                start_idx = llm_text.find('{')
                end_idx = llm_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = llm_text[start_idx:end_idx]
                    parsed_result = json.loads(json_str)
                    parsed_result["llm_provider"] = "ollama"
                    parsed_result["model"] = "llama2:7b"
                    return parsed_result
                    
            except (json.JSONDecodeError, ValueError):
                pass
            
            # Fallback: extract sentiment from text
            llm_lower = llm_text.lower()
            
            if analysis_type == "political_sentiment":
                if any(word in llm_lower for word in ['positive', 'optimistic', 'favorable']):
                    sentiment = "positive"
                elif any(word in llm_lower for word in ['negative', 'pessimistic', 'unfavorable']):
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                if any(word in llm_lower for word in ['uncertain', 'unclear', 'ambiguous']):
                    uncertainty = "high"
                elif any(word in llm_lower for word in ['somewhat', 'moderate']):
                    uncertainty = "medium"
                else:
                    uncertainty = "low"
                
                return {
                    "political_sentiment": sentiment,
                    "uncertainty_level": uncertainty,
                    "confidence_score": 0.7,
                    "llm_provider": "ollama",
                    "model": "llama2:7b",
                    "raw_response": llm_text[:200] + "..." if len(llm_text) > 200 else llm_text
                }
            
            else:
                # For risk and impact analysis
                if any(word in llm_lower for word in ['high', 'significant', 'major']):
                    level = "high"
                elif any(word in llm_lower for word in ['medium', 'moderate']):
                    level = "medium"
                else:
                    level = "low"
                
                return {
                    "risk_level": level,
                    "business_impact": level,
                    "impact_level": level,
                    "confidence_score": 0.7,
                    "llm_provider": "ollama",
                    "model": "llama2:7b",
                    "raw_response": llm_text[:200] + "..." if len(llm_text) > 200 else llm_text
                }
        
        return {
            "error": "Failed to get response from Ollama",
            "llm_provider": "ollama",
            "fallback": True
        }

    def _analyze_with_huggingface(self, text: str, analysis_type: str) -> Dict:
        """Analyze using HuggingFace models."""
        if analysis_type == "political_sentiment":
            results = self.llm_client(text)
            sentiment_scores = {item['label']: item['score'] for item in results[0]}
            
            # Map HuggingFace labels to our political sentiment format
            political_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            
            # Determine uncertainty level based on confidence
            max_score = max(sentiment_scores.values())
            if max_score >= 0.8:
                uncertainty_level = "low"
            elif max_score >= 0.6:
                uncertainty_level = "medium"
            else:
                uncertainty_level = "high"
            
            return {
                "political_sentiment": political_sentiment.lower(),
                "sentiment_scores": sentiment_scores,
                "uncertainty_level": uncertainty_level,
                "confidence_score": max_score,
                "llm_provider": "huggingface",
                "model": "cardiffnlp/twitter-roberta-base-sentiment-latest"
            }
           # For other analysis types, return basic sentiment info (fix this pendin)
        return {
            "message": f"Analysis type '{analysis_type}' simplified to sentiment analysis",
            "risk_level": "medium",  # Default fallback
            "business_impact": "medium",  # Default fallback
            "llm_provider": "huggingface"
        }
    
    
    def _calculate_enhanced_score(self, traditional_political: Dict, 
                                sector_analysis: Dict, llm_insights: Dict) -> float:
        """
        Calculate enhanced political uncertainty score using LLM insights.
        """
        base_score = (
            traditional_political.get("political_score", 0) * 0.3 +
            sector_analysis.get("sector_risk_score", 0) * 0.4
        )
        
        # LLM adjustment (30% weight)
        llm_adjustment = 0
        llm_count = 0
        
        for article in llm_insights.get("articles", []):
            sentiment = article.get("sentiment_analysis", {})
            risk = article.get("risk_analysis", {})
            
            # Sentiment adjustment
            if sentiment.get("uncertainty_level") == "high":
                llm_adjustment += 20
            elif sentiment.get("uncertainty_level") == "medium":
                llm_adjustment += 10
            
            # Risk level adjustment
            if risk.get("risk_level") == "high":
                llm_adjustment += 25
            elif risk.get("risk_level") == "medium":
                llm_adjustment += 15
            
            llm_count += 1
        
        if llm_count > 0:
            llm_score = (llm_adjustment / llm_count) * 0.3
            enhanced_score = base_score + llm_score
        else:
            enhanced_score = base_score
        
        return min(100, max(0, round(enhanced_score, 2)))
    
    def _determine_confidence_level(self, llm_insights: Dict) -> str:
        """Determine confidence level based on LLM analysis consistency."""
        if not llm_insights.get("articles"):
            return "low"
        
        confidence_scores = []
        for article in llm_insights["articles"]:
            sentiment = article.get("sentiment_analysis", {})
            if "confidence" in sentiment or "confidence_score" in sentiment:
                confidence_scores.append(
                    sentiment.get("confidence", sentiment.get("confidence_score", 0.5))
                )
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            if avg_confidence >= 0.8:
                return "high"
            elif avg_confidence >= 0.6:
                return "medium"
        
        return "low"

    def enhanced_political_analysis(self, news_data: Dict, company_name: str) -> Dict:
        """
        Enhanced political analysis combining traditional keyword matching with HuggingFace LLM insights.
        
        Args:
            news_data: Dictionary with news articles: {company:[{},{}..]}
            company_name: Name of the company being analyzed
        
        Returns:
            Dict with enhanced analysis including LLM insights
        """
        # Traditional analysis
        traditional_analysis = self.analyze_news_political_content(company_name,news_data)
        sector_analysis = self.analyze_sector_specific_risks(company_name, news_data)
        
        # LLM Enhancement using HuggingFace
        llm_insights = {"articles": []}
        
        if self.use_llm:
            count=0
            for article in news_data[company_name][:3]:  # Analyze top 3 articles
                article_text = f"{article['title']} {article['summary']}"
                
                # HuggingFace sentiment analysis
                sentiment_analysis = self.analyze_with_llm(article_text, "political_sentiment")
                # Use sentiment analysis for risk and impact assessment too
                risk_analysis = self.analyze_with_llm(article_text, "risk_assessment")
                impact_analysis = self.analyze_with_llm(article_text, "impact_analysis")
                
                llm_insights["articles"].append({
                    "article_id": count,
                    "title": article['title'],
                    "sentiment_analysis": sentiment_analysis,
                    "risk_analysis": risk_analysis,
                    "impact_analysis": impact_analysis
                })
                count=count+1
           
        
        # Combine traditional and LLM results
        enhanced_result = {
            "company": company_name,
            #"llm_insights": llm_insights,
            "enhanced_score": 0,
            "confidence_level": "medium"
        }
        
        # Calculate enhanced score incorporating LLM insights
        if self.use_llm and llm_insights["articles"]:
            enhanced_result["enhanced_score"] = self._calculate_enhanced_score(
                traditional_analysis, sector_analysis, llm_insights
            )
            enhanced_result["confidence_level"] = self._determine_confidence_level(llm_insights)
        else:
            # Fallback to traditional scoring
            enhanced_result["enhanced_score"] = (
                traditional_analysis.get("political_score", 0) * 0.3 +
                sector_analysis.get("sector_risk_score", 0) * 0.7
            )
        
        return enhanced_result

    def analyze_sector_specific_risks(self, company_name: str, news_data: Dict) -> Dict:
        """
        Analyze sector-specific political risks for a company.
        
        Args:
            company_name: Name of the company
            news_data: Dictionary with news articles
        
        Returns:
            Dict with sector-specific risk analysis
        """
        sector = self.company_sectors.get(company_name)
        if not sector or not news_data:
            return {'sector_risk_score': 0, 'main_risks': [], 'risk_articles': []}
        
        sector_config = self.sector_risks[sector]
        sector_keywords = sector_config['keywords']
        sector_weight = sector_config['weight']
        
        risk_articles = []
        total_risk_score = 0
        detected_risks = set()
           
            
        count=0
        for article in news_data[company_name]:
            article_text=f"{article['title']}: {article['summary']}".lower()
            
            # Count sector-specific risk mentions
            risk_mentions = sum(1 for keyword in sector_keywords if keyword in article_text)
            
            if risk_mentions > 0:
                risk_articles.append({
                    'id': count,
                    'title': article.get('title', ''),
                    'risk_score': risk_mentions,
                    'provider': article.get('provider', 'Unknown')
                })
                count=count+1
                
                total_risk_score += risk_mentions
                
                # Identify specific risks
                for keyword in sector_keywords:
                    if keyword in article_text:
                        detected_risks.add(keyword)
        
        # Calculate weighted sector risk score (0-100)
        max_possible_score = len(news_data) * len(sector_keywords)
        base_risk_score = (total_risk_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        weighted_risk_score = min(100, base_risk_score * sector_weight)
        
        return {
            'sector': sector,
            'sector_risk_score': round(weighted_risk_score, 2),
            'main_risks': sector_config['main_risks'],
            'detected_risks': list(detected_risks),
            'risk_articles': len(risk_articles),
            'sector_weight': sector_weight,
            'risk_articles_detail': risk_articles[:3]  # Top 3 risk articles
        }
    def _analyze_with_ollama(self, text: str, analysis_type: str) -> Dict:
        """Analyze using Ollama (if available)."""
        try:
            import requests
            
            prompt = self._build_ollama_prompt(text, analysis_type)
            
            response = requests.post('http://localhost:11434/api/generate', 
                                json={
                                    'model': 'llama2:7b',
                                    'prompt': prompt,
                                    'stream': False
                                }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_ollama_response(result.get('response', ''), analysis_type)
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ollama not available: {e}")
            # Fallback to intelligent mapping
            if analysis_type == "risk_assessment":
                sentiment_result = self._analyze_with_huggingface(text, "political_sentiment")
                return self._map_sentiment_to_risk(sentiment_result, text)
            elif analysis_type == "impact_analysis":
                sentiment_result = self._analyze_with_huggingface(text, "political_sentiment")
                return self._map_sentiment_to_impact(sentiment_result, text)

    def _build_ollama_prompt(self, text: str, analysis_type: str) -> str:
        """Build prompt for Ollama analysis."""
        if analysis_type == "risk_assessment":
            return f"""
            Analyze this political news for business risk level:
            Text: {text[:500]}
            
            Rate the political risk as high, medium, or low.
            Provide brief reasoning.
            
            Format your response as:
            Risk: [high/medium/low]
            Reasoning: [brief explanation]
            """
        elif analysis_type == "impact_analysis":
            return f"""
            Analyze this political news for business impact:
            Text: {text[:500]}
            
            Rate the business impact as high, medium, or low.
            Provide brief reasoning.
            
            Format your response as:
            Impact: [high/medium/low]
            Reasoning: [brief explanation]
            """

    def _parse_ollama_response(self, response: str, analysis_type: str) -> Dict:
        """Parse Ollama response."""
        try:
            lines = response.strip().split('\n')
            level = "medium"  # default
            reasoning = "Analysis completed"
            
            for line in lines:
                if line.startswith('Risk:') or line.startswith('Impact:'):
                    level = line.split(':')[1].strip().lower()
                elif line.startswith('Reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            field_name = "risk_level" if analysis_type == "risk_assessment" else "business_impact"
            
            return {
                field_name: level,
                "reasoning": reasoning,
                "confidence_score": 0.8,
                "llm_provider": "ollama"
            }
        except:
            return {
                "risk_level": "medium",
                "business_impact": "medium",
                "reasoning": "Parsing error, using default",
                "llm_provider": "ollama_fallback"
            }


def main():
    politics=PoliticalUncertaintyAnalyzer()
    news_data=politics.get_news_data_using_thread()


    s=time.time()
    companies=["Microsoft", "Nvidia", "Apple", "Amazon", "Alphabet", "Tesla"]
    for company in companies:
        print(politics.enhanced_political_analysis(news_data,company))
       
    e=time.time()
    print(e-s)
    
main()