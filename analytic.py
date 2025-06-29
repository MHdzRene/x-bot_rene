import pandas as pd

# Define companies
companies = ['microsoft', 'nvidia', 'apple', 'amazon', 'alphabet']

# Example data: probabilities and sample sizes (replace with your actual data)
# P(X): Proportion of Positive tweets from sentiment analysis
# P(Y): Proportion of positive Yahoo Finance articles
# P(G): Proportion of positive Google News articles
# sample_sizes: Number of tweets/articles for each source
data = {
    'microsoft': {
        'P_X': 0.60,  # Example: 60% of tweets are Positive
        'P_Y': 0.70,  # Example: 70% of Yahoo Finance articles are positive
        'P_G': 0.65,  # Example: 65% of Google News articles are positive
        'sample_X': 1000,  # Number of tweets
        'sample_Y': 50,    # Number of Yahoo Finance articles
        'sample_G': 20     # Number of Google News articles
    },
    'nvidia': {
        'P_X': 0.75,
        'P_Y': 0.80,
        'P_G': 0.70,
        'sample_X': 800,
        'sample_Y': 40,
        'sample_G': 15
    },
    'apple': {
        'P_X': 0.55,
        'P_Y': 0.65,
        'P_G': 0.60,
        'sample_X': 1200,
        'sample_Y': 60,
        'sample_G': 25
    },
    'amazon': {
        'P_X': 0.50,
        'P_Y': 0.60,
        'P_G': 0.55,
        'sample_X': 900,
        'sample_Y': 45,
        'sample_G': 18
    },
    'alphabet': {
        'P_X': 0.65,
        'P_Y': 0.75,
        'P_G': 0.70,
        'sample_X': 1100,
        'sample_Y': 55,
        'sample_G': 22
    }
}

# Reliability weights (subjective, adjust based on source quality)
reliability_weights = {
    'X': 0.7,  # Lower weight for X due to potential noise
    'Y': 1.0,  # Higher weight for Yahoo Finance (curated financial content)
    'G': 0.9   # Slightly lower than Yahoo Finance but higher than X
}

# Function to combine probabilities
def combine_probabilities(p_x, p_y, p_g, sample_x, sample_y, sample_g, reliability_x, reliability_y, reliability_g):
    # Calculate weights based on sample size and reliability
    w_x = sample_x * reliability_x
    w_y = sample_y * reliability_y
    w_g = sample_g * reliability_g
    
    # Weighted average
    combined_prob = (w_x * p_x + w_y * p_y + w_g * p_g) / (w_x + w_y + w_g)
    return combined_prob

# Calculate combined probabilities for each company
results = []
for company in companies:
    try:
        # Get probabilities and sample sizes
        p_x = data[company]['P_X']
        p_y = data[company]['P_Y']
        p_g = data[company]['P_G']
        sample_x = data[company]['sample_X']
        sample_y = data[company]['sample_Y']
        sample_g = data[company]['sample_G']
        
        # Combine probabilities
        combined_prob = combine_probabilities(
            p_x, p_y, p_g,
            sample_x, sample_y, sample_g,
            reliability_weights['X'], reliability_weights['Y'], reliability_weights['G']
        )
        
        # Store results
        results.append({
            'Company': company.capitalize(),
            'P_X': p_x,
            'P_Y': p_y,
            'P_G': p_g,
            'Sample_X': sample_x,
            'Sample_Y': sample_y,
            'Sample_G': sample_g,
            'Combined_Probability': combined_prob
        })
        
        print(f"\nCompany: {company.capitalize()}")
        print(f"P(X): {p_x:.3f}, P(Y): {p_y:.3f}, P(G): {p_g:.3f}")
        print(f"Sample Sizes: X={sample_x}, Y={sample_y}, G={sample_g}")
        print(f"Combined Probability of Positive Sentiment: {combined_prob:.3f}")
        
    except Exception as e:
        print(f"Error processing {company}: {e}")

# Save results to CSV
df_results = pd.DataFrame(results)
df_results.to_csv('combined_sentiment_probabilities.csv', index=False, encoding='utf-8')
print("\nSaved combined probabilities to combined_sentiment_probabilities.csv")