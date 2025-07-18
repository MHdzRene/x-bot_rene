import working_wjson as wj
import news 
import sentiment_analytics as sa
import company_analyzer as ca

class updater_data():
    def __init__(self):
        self.companies_address= 'data/companies.json'
        self.companies= wj.load_from_json(self.companies_address)
        self.data_total_analyze_address='data/data_total_analyze.json'
        self.data_total_analyze= wj.load_from_json(self.data_total_analyze_address)
        #leve this for later
        self.political_news_querie_address='data/political_news_queries.json'
        self.political_news= wj.load_from_json(self.political_news_querie_address)

        self.news_extractor=news.NewsExtractor()
        self.company_analitics=sa.SentimentAnalytics()
        self.company_analizer= ca.CompanyAnalyzer()

    def add_company_to_companies(self, new_company, new_ticker):
        self.companies[new_company]= new_ticker
        wj.save_to_json(self.companies, self.companies_address)
    
    def delete_company_from_companies(self):
        pass

    def update_company(self):
        pass
#new line

    def update_news(self,company_name):
        """
        updating yf_news, google_news and x_tweets, try first update the companies if not is for nothing probably
        """
        self.news_extractor.save_single_company_news(company_name)

    def update_data_analyze(self):
        """
        Preferible do first update news
        this going to update total_data_analizer
        """
        self.company_analizer.get_multi_source_sentiment_analysis() 

    def update_combine_prob(self):
        self.company_analitics.calculate_combined_sentiment_metrics()

    def update_all_json(self,new_company,new_ticker):
        self.add_company_to_companies(new_company,new_ticker)
        self.update_news(new_company)
        self.update_data_analyze()
        self.update_combine_prob
        
    # Optimizar para procesar múltiples empresas en una sola sesión
    def update_multiple_companies(self, companies_list):
        # Una sola instancia de TwitterClient para todas las empresas
        for company in companies_list:
            self.update_news(company)






        
    