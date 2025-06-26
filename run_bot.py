"""
Simple example of how to use the Twitter bot with company analysis.
"""

from prueba import get_company_analysis
import bot

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
    # Available companies:
    # 'Microsoft', 'Nvidia', 'Apple', 'Amazon', 'Alphabet', 'Tesla'
    
    # Example: Post Tesla analysis
    post_company_analysis('Tesla')
