from pygooglenews import GoogleNews

def test_google_news():
    topic = "Microsoft"
    print(f"[TEST] Searching Google News for topic: {topic}")
    gn = GoogleNews(lang='en', country='US')
    try:
        result = gn.search(topic)
        entries = result.get('entries', [])
        print(f"[TEST] Found {len(entries)} entries for topic '{topic}'")
        if entries:
            for entry in entries[:3]:
                print(f"- {entry.get('title', 'No title')}")
        else:
            print("[TEST] No news found. Possible block, rate-limit, or network issue.")
    except Exception as e:
        print(f"[TEST] Exception: {e}")

if __name__ == "__main__":
    test_google_news()
