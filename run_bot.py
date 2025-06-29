

import bot
import company_analyzer as ca

def post_company_analysis(company_name):
    """Get analysis for a company and post it to Twitter"""
    
    print(f"📊 Getting analysis for {company_name}...")
    
    # Get the formatted analysis
    analysis = ca.get_company_analysis(company_name)
    
    # Post to Twitter
    print("📤 Posting to Twitter...")
    bot.create_tweet(analysis)
    
    print("✅ Done!")
    return analysis

if __name__ == "__main__":
    # 'Microsoft', 'Nvidia', 'Apple', 'Amazon', 'Alphabet', 'Tesla'
    #in this part i can create the tweets we have been creating
    company_a=ca.CompanyAnalyzer()
    #analysis of all companies saved in the class CompanyAnalyzer
    # for i in company_a.companies.keys():
    #     post_company_analysis(i)
 


 #this part is for check the search of tweets and sentments 
    query_tesla = 'Tesla OR TSLA OR "Model 3" OR "Model Y" OR Cybertruck -is:retweet  -from:teslapromo -discount -sale lang:en ' 

    tweets=bot.search_tweets(query_tesla,100,bot.client)
    ex=company_a.get_news_sentiment(tweets)

    print('sentiment')
    print(ex['sentiment'])
    print('positive %')
    print(str(ex['positive_porcent']) + '%')
    print('negative %')
    print(str(ex['negative_porcent'] )+ '%')
        
         
        
   