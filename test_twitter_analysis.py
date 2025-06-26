from prueba import get_company_analysis
import bot 

# Example: Get Tesla analysis as a string
def test_tesla_analysis():
    """Test function to get Tesla analysis formatted for Twitter"""
    
    print("Getting Tesla analysis...")
    tesla_analysis = get_company_analysis('Tesla')
    
    print("=" * 80)
    print("TESLA ANALYSIS FOR TWITTER:")
    print("=" * 80)
    print(tesla_analysis)
    print("=" * 80)
    
    return tesla_analysis

# Example: Get any other company analysis
def test_company_analysis(company_name):
    """Test function to get analysis for any company"""
    
    print(f"Getting {company_name} analysis...")
    analysis = get_company_analysis(company_name)
    
    print("=" * 80)
    print(f"{company_name.upper()} ANALYSIS FOR TWITTER:")
    print("=" * 80)
    print(analysis)
    print("=" * 80)
    
    return analysis

if __name__ == "__main__":
    # Test Tesla
    tesla_result = test_tesla_analysis()
    
    print("\n" + "="*50 + "\n")
    
    # Test another company (Apple)
    apple_result = test_company_analysis('Apple')
    
    # You can now use tesla_result or apple_result as strings for Twitter posting
    # For example:
    bot.create_tweet(tesla_result)
