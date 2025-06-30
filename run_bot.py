

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
    for i in company_a.companies.keys():
        post_company_analysis(i)
 



        
         
        
   