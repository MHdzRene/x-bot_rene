
import twitter_client as tc


t_client = tc.TwitterClient()
    # Opcional: Agrega tu propia cuenta como authorized para pruebas
t_client.authorized_users.add('StockP_Ai')  # O el username
t_client.monitor_and_respond_mentions()


"""
    def handle_mention(self,mention):
        
        Function to handle a mention (tweet that mentions @StockP_Ai)
        This would be called when a new mention is detected
        
        # Extract username from the mention tweet
        username = mention['author']['username']  # Adjust based on actual response structure
        # Load authorized users if needed (could call periodically outside)
        self.load_authorized(self.USER_ID)
        if self.is_authorized(username):
            # Process AI and respond
            response = self.generate_ai_analysis(mention['text'])
            try:
                self.client.create_tweet(
                    in_reply_to_tweet_id=mention['id'],
                    text=response
                )
                print(f"Replied to authorized user: @{username}")
            except tweepy.TweepyException as e:
                print(f"Error replying: {e}")
        else:
            # Deny access and prompt to subscribe
            deny_text = f"@{username} Access limited to subscribers. Subscribe now! #StockP_Ai"
            try:
                self.client.create_tweet(
                    in_reply_to_tweet_id=mention['id'],
                    text=deny_text
                )
                print(f"Denied access to: @{username}")
            except tweepy.TweepyException as e:
                print(f"Error denying: {e}")
"""





