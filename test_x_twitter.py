import twitter_client as tc

def test_x_twitter():
    query = "Microsoft -is:retweet -is:reply lang:en"
    print(f"[TEST] Searching X/Twitter for query: {query}")
    try:
        client = tc.get_twitter_client()
        tweets = client.search_tweets(query, max_total=10)
        print(f"[TEST] Found {len(tweets) if tweets else 0} tweets for query '{query}'")
        if tweets:
            for tid, tweet in list(tweets.items())[:3]:
                print(f"- {tweet.get('summary', '')[:80]}")
        else:
            print("[TEST] No tweets found. Possible block, rate-limit, or credential issue.")
    except Exception as e:
        print(f"[TEST] Exception: {e}")

if __name__ == "__main__":
    test_x_twitter()
