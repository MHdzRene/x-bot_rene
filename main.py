#updatear lo que tenga que updatear
#correr el bot
import company_analyzer
import sentiment_analytics
import news
import politics 
import datetime 


def main():
    # Initialize news extractor
    news_extractor= news.NewsExtractor()
    # update each news file (yf_news, google_news, x_tweets)
    news_extractor.save_news()

    # Initialize company analyzer
    company_a=company_analyzer.CompanyAnalyzer()
    # update each news file data_total_analyze_file
    company_a.get_multi_source_sentiment_analysis()

   
    # update uncertity_per_company and politics news(it will take a while so go back to sleep jaja)
    politics.main()
 
    # Initialize analytics engine
    analytics = sentiment_analytics.SentimentAnalytics()
    # update combined prob file
    analytics.calculate_combined_sentiment_metrics()

    #now run bot for post completed updated analysis
    #analysis of all companies saved in the class CompanyAnalyzer
    for i in company_a.companies.keys():
        company_analyzer.post_company_analysis(i)
    
 

#main()
#politics.main()
#print(company_analyzer.get_company_analysis(company_name="StarBucks", ticker='SBUX'))

   




