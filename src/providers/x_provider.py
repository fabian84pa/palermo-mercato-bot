from pathlib import Path
import hashlib
import json
import re
from urllib.parse import quote
from playwright.sync_api import Locator, Page, sync_playwright
from core.news import NewsItem
from core.provider import Provider

class XProvider(Provider):
    SOURCES = ("FabrizioRomano", "MatteMoretto", "DiMarzio", "NicoSchira", "Palermofficial")
    KEYWORDS_FILE = Path("data/palermo_keywords.json")
    MAX_POSTS_PER_SOURCE = 50
    MAX_SEARCH_RESULTS = 10
    SEARCH_TERMS = ("Palermo", '"Palermo FC"', "rosanero", "rosaneri", "Almena", "Osti", "Inzaghi", "Strefezza", "Pohjanpalo")
    MARKET_CONTEXT = ("palermo", "palermofficial", "rosanero", "rosaneri", "almena", "al-qadisiyya", "al-qadisiyah", "osti", "inzaghi", "strefezza", "pohjanpalo")
    OFFICIAL_MARKET_WORDS = ("benvenuto", "welcome", "ufficiale", "annuncia", "annunciato", "firma", "firmato", "contratto", "rinnovo", "prolungamento", "acquisto", "acquista", "ingaggiato", "ceduto", "cessione", "prestito", "transfer", "signing", "signed")
    OFFICIAL_EXCLUDED = ("match day", "trophy", "allenamento", "training", "partita", "gara", "diretta", "streaming", "live", "amichevole", "risveglio", "perth")

    @property
    def name(self): return "X Calciomercato"

    def load_keywords(self):
        try:
            data = json.loads(self.KEYWORDS_FILE.read_text(encoding="utf-8"))
            return tuple(str(k).casefold().strip() for k in data.get("keywords", []) if str(k).strip())
        except (OSError, json.JSONDecodeError, AttributeError):
            return ()

    @staticmethod
    def normalize_text(text):
        text = (text or "").casefold()
        text = re.sub(r"\b\d+\s*(?:m|h|d|w)\b", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def generate_id(self, source, text, link=""):
        match = re.search(r"/status/(\d+)", link or "")
        if match: return f"x-{source}-{match.group(1)}"
        digest = hashlib.sha256(f"{source.casefold()}::{self.normalize_text(text)}".encode()).hexdigest()
        return f"x-{source}-{digest[:20]}"

    def is_relevant(self, text, source):
        normalized = self.normalize_text(text)
        if source == "Palermofficial":
            return not any(x in normalized for x in self.OFFICIAL_EXCLUDED) and any(x in normalized for x in self.OFFICIAL_MARKET_WORDS)
        return any(k in normalized for k in self.load_keywords()) or any(x in normalized for x in self.MARKET_CONTEXT)

    def extract_post(self, article: Locator):
        try:
            box = article.locator('[data-testid="tweetText"]')
            text = box.first.inner_text() if box.count() else article.inner_text()
            text = (text or "").strip()
            if not text: return None
            published, link = "", ""
            time = article.locator("time")
            if time.count():
                published = time.first.get_attribute("datetime") or ""
                for parent in (time.first.locator("xpath=.."), time.first.locator("xpath=../..")):
                    href = parent.get_attribute("href")
                    if href and "/status/" in href:
                        link = href if href.startswith("http") else "https://x.com" + href
                        break
            return text, link, published
        except Exception as exc:
            print(f"Errore estrazione tweet: {exc}")
            return None

    def collect_posts(self, page: Page, source, max_scrolls=8):
        out, seen = [], set()
        for scroll in range(max_scrolls):
            articles = page.locator("article")
            for i in range(articles.count()):
                post = self.extract_post(articles.nth(i))
                if not post: continue
                text, link, published = post
                key = link or self.normalize_text(text)
                if not key or key in seen: continue
                seen.add(key); out.append(post)
                if len(out) >= self.MAX_POSTS_PER_SOURCE: return out
            page.mouse.wheel(0, 5000); page.wait_for_timeout(2200)
        return out

    def search_x_posts(self, page: Page, query):
        out = []
        try:
            url = f"https://x.com/search?q={quote(query, safe='')}&f=live&src=typed_query"
            print(f"CONTROLLO SEARCH X: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            articles = page.locator("article")
            for i in range(min(articles.count(), self.MAX_SEARCH_RESULTS)):
                post = self.extract_post(articles.nth(i))
                if post: out.append(post)
        except Exception as exc:
            print(f"Errore ricerca X '{query}': {exc}")
        return out

    @staticmethod
    def merge_posts(posts):
        out, seen = [], set()
        for post in posts:
            text, link, published = post
            key = link or re.sub(r"\s+", " ", text.casefold()).strip()
            if key in seen: continue
            seen.add(key); out.append(post)
        return out

    def fetch(self):
        items, global_seen = [], set()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 1800}, locale="it-IT")
            for source in self.SOURCES:
                try:
                    profile_url = f"https://x.com/{source}"
                    page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(5000)
                    posts = self.collect_posts(page, source)
                    if source != "Palermofficial":
                        for query in self.SEARCH_TERMS: posts.extend(self.search_x_posts(page, query))
                    for text, link, published in self.merge_posts(posts):
                        if not self.is_relevant(text, source): continue
                        item_id = self.generate_id(source, text, link)
                        if item_id in global_seen: continue
                        global_seen.add(item_id)
                        clean = re.sub(r"\s+", " ", text).strip()
                        items.append(NewsItem(id=item_id, title=clean[:180], link=link or profile_url, source=self.name, published=published, summary=clean))
                except Exception as exc:
                    print(f"Errore @{source}: {exc}")
            browser.close()
        print(f"X: notizie pertinenti raccolte = {len(items)}")
        return items
