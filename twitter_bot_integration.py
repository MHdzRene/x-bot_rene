"""
Simple usage examples for the Twitter-formatted company analysis.

This script shows how to use the prueba.py module to get formatted 
analysis strings that can be used directly for Twitter posting.
"""

from prueba import get_company_analysis
# Uncomment the next line if you want to integrate with your existing bot
# import bot

def create_twitter_ready_analysis(company_name):
    """
    Get a Twitter-ready analysis for a specific company.
    
    Args:
        company_name (str): Company name ('Tesla', 'Apple', 'Microsoft', etc.)
    
    Returns:
        str: Formatted string ready for Twitter posting
    """
    
    # Available companies:
    # 'Microsoft', 'Nvidia', 'Apple', 'Amazon', 'Alphabet', 'Tesla'
    
    analysis = get_company_analysis(company_name)
    return analysis

def main():
    """Example usage of the Twitter analysis system"""
    
    print("🚀 Twitter Analysis Generator")
    print("Available companies: Microsoft, Nvidia, Apple, Amazon, Alphabet, Tesla")
    
    # Example 1: Get Tesla analysis
    print("\n📊 Getting Tesla Analysis...")
    tesla_analysis = create_twitter_ready_analysis('Tesla')
    
    # This string is now ready to be posted to Twitter
    print("✅ Tesla analysis ready!")
    print(f"Length: {len(tesla_analysis)} characters")
    
    # Example 2: If you want to post to Twitter using your bot
    # Uncomment these lines to integrate with your existing bot.py:
    
    # print("📤 Posting to Twitter...")
    # bot.create_tweet(tesla_analysis)
    # print("✅ Posted to Twitter!")
    
    # Example 3: You can also split the analysis into multiple tweets if too long
    if len(tesla_analysis) > 280:  # Twitter character limit
        print("⚠️  Analysis is longer than Twitter limit, consider splitting into threads")
        
        # Simple way to split into chunks
        chunks = []
        words = tesla_analysis.split('\n')
        current_chunk = ""
        
        for line in words:
            if len(current_chunk + line + '\n') < 280:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        print(f"📝 Analysis split into {len(chunks)} tweets:")
        for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
            print(f"\n--- Tweet {i} ---")
            print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
    
    # Example 4: Get analysis for multiple companies
    print("\n📊 Getting analysis for multiple companies...")
    companies = ['Apple', 'Microsoft', 'Nvidia']
    
    for company in companies:
        analysis = create_twitter_ready_analysis(company)
        print(f"✅ {company} analysis ready! ({len(analysis)} chars)")
        
        # Here you could post each analysis to Twitter:
        # bot.create_tweet(analysis)

if __name__ == "__main__":
    main()
