import pandas as pd
import working_wjson as wj

class SentimentAnalytics:
    """
    Statistical analysis class for multi-source sentiment data.
    Provides weighted probability calculations, statistical metrics, and analytics 
    for sentiment analysis across X (Twitter), Yahoo Finance, and Google News.
    """
    
    def __init__(self, companies_path='data/companies.json', data_path='data/data_total_analyze.json'):
        """
        Initialize the analytics engine with company data and sentiment data.
        
        Args:
            companies_path (str): Path to JSON file containing company information
            data_path (str): Path to JSON file containing sentiment analysis data
        """
        self.companies = wj.load_from_json(companies_path)
        self.data = wj.load_from_json(data_path)
        
        # Default reliability weights (can be customized)
        self.reliability_weights = {
            'X': 0.7,  # Lower weight for X due to potential noise
            'Y': 1.0,  # Higher weight for Yahoo Finance (curated financial content)
            'G': 0.9   # Slightly lower than Yahoo Finance but higher than X
        }
    
    def set_reliability_weights(self, x_weight=0.7, y_weight=1.0, g_weight=0.9):
        """
        Customize reliability weights for different data sources.
        
        Args:
            x_weight (float): Weight for X (Twitter) data
            y_weight (float): Weight for Yahoo Finance data
            g_weight (float): Weight for Google News data
        """
        self.reliability_weights = {
            'X': x_weight,
            'Y': y_weight,
            'G': g_weight
        }
    
    def combine_probabilities(self, x, y, g, sample_x, sample_y, sample_g, 
                            reliability_x, reliability_y, reliability_g):
        """
        Combine probabilities from multiple sources using weighted average.
        Weights are calculated based on sample size and source reliability.
        
        Args:
            p_x, p_y, p_g (float): Probability values from each source (0.0-1.0)
            sample_x, sample_y, sample_g (int): Sample sizes from each source
            reliability_x, reliability_y, reliability_g (float): Reliability weights
        
        Returns:
            float: Combined probability using weighted average
        """
        # Calculate weights based on sample size and reliability
        w_x = sample_x * reliability_x
        w_y = sample_y * reliability_y
        w_g = sample_g * reliability_g
        
        # Weighted average
        combined_prob = (w_x * x + w_y * y + w_g * g) / (w_x + w_y + w_g)
        result = round(combined_prob, 3)
        
        return result 
    
    def calculate_combined_sentiment_metrics(self):
        """
        Calculate combined sentiment probabilities for all companies.
        Processes positive sentiment data from all three sources.
        
        Returns:
            list: List of dictionaries containing company metrics and combined probabilities
        """
        results = {}
        
        for company in self.companies.keys():
            try:
                # Get probabilities and sample sizes
                p_x = self.data[company]['P_X']
                n_x=self.data[company]['N_X']
                p_y = self.data[company]['P_Y']
                n_y=self.data[company]['N_Y']
                p_g = self.data[company]['P_G']
                n_g=self.data[company]['N_G']
                sample_x = self.data[company]['sample_X']
                sample_y = self.data[company]['sample_Y']
                sample_g = self.data[company]['sample_G']
                
                # Combine probabilities positive
                combined_prob_positive = self.combine_probabilities(
                    p_x, p_y, p_g,
                    sample_x, sample_y, sample_g,
                    self.reliability_weights['X'], 
                    self.reliability_weights['Y'], 
                    self.reliability_weights['G']
                )
                # Combine probabilities negative
                combined_prob_negative = self.combine_probabilities(
                    n_x, n_y, n_g,
                    sample_x, sample_y, sample_g,
                    self.reliability_weights['X'], 
                    self.reliability_weights['Y'], 
                    self.reliability_weights['G']
                )

                neutral=1-(combined_prob_negative+combined_prob_positive)
                # 
                combined_prob_positive= combined_prob_positive + neutral/2
                combined_prob_positive=round(combined_prob_positive,4)
                combined_prob_negative= combined_prob_negative + neutral/2
                combined_prob_negative=round(combined_prob_negative,4)

                # Store results
                results[company.capitalize()]={
                    'Combined_Prob_positive': combined_prob_positive,
                    'Combined_Prob_negative': combined_prob_negative
                }
                wj.save_to_json(results,'data/Combined_Prob.json')
                
            except Exception as e:
                print(f"Error processing {company}: {e}")
                
        return results
    
    def print_sentiment_report(self):
        """
        Print detailed sentiment analysis report for all companies.
        Displays individual source probabilities, sample sizes, and combined metrics.
        """
        results = self.calculate_combined_sentiment_metrics()
        
        for result in results:
            print(f"\nCompany: {result['Company']}")
            print(f"Combined Probability of Positive Sentiment: {result['Combined_Prob_positiveability']:.3f}")
            print(f"Combined Probability of Negative Sentiment: {result['Combined_Prob_negativeability']:.3f}")
    
    def save_results_to_csv(self, filename='data/combined_sentiment_probabilities.csv'):
        """
        Save combined sentiment analysis results to CSV file.
        
        Args:
            filename (str): Output CSV filename
        """
        results = self.calculate_combined_sentiment_metrics()
        df_results = pd.DataFrame(results)
        df_results.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nSaved combined probabilities to {filename}")

# Example usage
def main():
    # Initialize analytics engine
    analytics = SentimentAnalytics()
    
    # Generate and print report
    analytics.calculate_combined_sentiment_metrics()
    
 

if __name__ == "__main__":
    main()
