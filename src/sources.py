from dataclasses import dataclass

import feedparser


GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?"
    "q=%22Palermo+FC%22+calciomercato"
    "&hl=it&gl=IT&ceid=IT:it"
)


@dataclass
class NewsItem:
    item_id: str
    title: str
    link: str
    source: str
    published: str


def fetch_google_news(limit: int = 10) -> list[NewsItem]:
    feed = feedparser.parse(GOOGLE_NEWS_RSS)
    news: list[NewsItem] = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        published = entry.get("published", "").strip()

        if not title or not link:
            continue

        news.append(
            NewsItem(
                item_id=entry.get("id", link),
                title=title,
                link=link,
                source="Google News",
                published=published,
            )
        )

    return news
