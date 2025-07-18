import feedparser
from datetime import datetime

def fetch_rss_articles(feeds, keywords=None, max_articles=20):
    """
    Descarga y filtra artículos de múltiples RSS feeds.
    feeds: lista de URLs RSS
    keywords: lista de palabras clave (ej: nombre empresa, ticker)
    max_articles: máximo de artículos por feed
    Devuelve lista de dicts: {title, summary, link, published, source}
    """
    all_articles = []
    for url in feeds:
        d = feedparser.parse(url)
        for entry in d.entries[:max_articles]:
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            link = entry.get('link', '')
            published = entry.get('published', '')
            source = d.feed.get('title', url)
            # Filtrar por keywords si se proveen
            if keywords:
                text = (title + ' ' + summary).lower()
                if not any(k.lower() in text for k in keywords):
                    continue
            all_articles.append({
                'title': title,
                'summary': summary,
                'link': link,
                'published': published,
                'source': source
            })
    return all_articles

# Ejemplo de uso:
if __name__ == "__main__":
    feeds = [
        'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'http://feeds.reuters.com/reuters/businessNews',
        'https://finance.yahoo.com/news/rssindex',
        'https://www.ft.com/?format=rss',
    ]
    articles = fetch_rss_articles(feeds, keywords=['Apple', 'AAPL'])
    for art in articles:
        print(f"{art['published']} | {art['title']} | {art['source']}")
        print(art['link'])
        print()
