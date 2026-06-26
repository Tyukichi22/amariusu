#!/usr/bin/env python3
"""Build a personal static website for robotics-focused AI news."""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

DEFAULT_FEEDS = [
    "https://arxiv.org/rss/cs.RO",
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/cs.CV",
    "https://spectrum.ieee.org/rss/robotics/fulltext",
    "https://news.mit.edu/topic/mitrobotics-rss.xml",
    "https://www.sciencedaily.com/rss/computers_math/robotics.xml",
]

ROBOTICS_KEYWORDS = [
    "robot", "robotics", "humanoid", "manipulation", "locomotion", "mobile robot",
    "autonomous", "embodied", "embodiment", "actuator", "sensor", "control",
    "motion planning", "path planning", "slam", "navigation", "grasp", "grasping",
    "reinforcement learning", "sim-to-real", "simulation", "ros", "drone", "uav",
    "soft robotics", "mechatronics", "mechanical", "kinematics", "dynamics",
]

RESEARCH_KEYWORDS = [
    "arxiv", "paper", "research", "university", "dataset", "benchmark", "model",
    "machine learning", "deep learning", "evaluation", "vision", "multimodal",
    "scientific", "academic", "open source", "conference", "journal", "prototype",
]

NOISE_KEYWORDS = [
    "stock", "earnings", "ipo", "lawsuit", "acquisition", "marketing", "advertising",
    "celebrity", "crypto", "gaming", "smartphone",
]

@dataclass(frozen=True)
class Article:
    title: str
    link: str
    source: str
    summary: str
    published: datetime | None
    score: int


def getenv_list(name: str, default: Iterable[str]) -> list[str]:
    value = os.getenv(name, "").strip()
    if not value:
        return list(default)
    return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]


def parse_datetime(entry: dict) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc)
        except Exception:
            continue
    return None


def clean_text(text: str, limit: int = 360) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(" ".join(text.split()))
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def score_article(title: str, summary: str, source: str) -> int:
    haystack = f"{title} {summary} {source}".lower()
    score = 0
    for keyword in ROBOTICS_KEYWORDS:
        if keyword in haystack:
            score += 5
    for keyword in RESEARCH_KEYWORDS:
        if keyword in haystack:
            score += 3 if keyword in {"arxiv", "paper", "research", "university", "dataset", "benchmark"} else 1
    for keyword in NOISE_KEYWORDS:
        if keyword in haystack:
            score -= 3
    return score


def xml_text(element: ET.Element | None, path: str, default: str = "") -> str:
    found = element.find(path) if element is not None else None
    return found.text.strip() if found is not None and found.text else default


def entry_link(entry: ET.Element) -> str:
    atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None and atom_link.attrib.get("href"):
        return atom_link.attrib["href"].strip()
    return xml_text(entry, "link")


def fetch_feed(feed_url: str) -> ET.Element:
    request = urllib.request.Request(feed_url, headers={"User-Agent": "robotics-ai-news-site/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return ET.fromstring(response.read())


def iter_feed_entries(root: ET.Element) -> tuple[str, list[ET.Element]]:
    if root.tag.endswith("rss") or root.find("channel") is not None:
        channel = root.find("channel")
        return xml_text(channel, "title", "RSS feed"), list(channel.findall("item")) if channel is not None else []
    atom = "{http://www.w3.org/2005/Atom}"
    return xml_text(root, f"{atom}title", "Atom feed"), list(root.findall(f"{atom}entry"))


def entry_value(entry: ET.Element, *names: str) -> str:
    atom = "{http://www.w3.org/2005/Atom}"
    for name in names:
        value = xml_text(entry, name) or xml_text(entry, f"{atom}{name}")
        if value:
            return value
    return ""


def collect_articles(feeds: list[str], hours: int = 36, limit: int = 20) -> list[Article]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: list[Article] = []
    seen: set[str] = set()
    for feed_url in feeds:
        try:
            root = fetch_feed(feed_url)
            source, entries = iter_feed_entries(root)
        except Exception as exc:
            print(f"Warning: failed to fetch {feed_url}: {exc}", file=sys.stderr)
            continue
        for entry in entries:
            link = entry_link(entry)
            title = clean_text(entry_value(entry, "title"), 180)
            if not link or not title or link in seen:
                continue
            published = parse_datetime({"published": entry_value(entry, "published", "pubDate"), "updated": entry_value(entry, "updated")})
            if published and published < cutoff:
                continue
            summary = clean_text(entry_value(entry, "summary", "description", "content"))
            score = score_article(title, summary, source)
            if score <= int(os.getenv("AI_NEWS_MIN_SCORE", "0")):
                continue
            articles.append(Article(
                title=title,
                link=link,
                source=clean_text(source, 120),
                summary=summary,
                published=published,
                score=score,
            ))
            seen.add(link)
    articles.sort(key=lambda item: (item.score, item.published or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return articles[:limit]


def format_date(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d") if value else "日付不明"


def render_html(articles: list[Article], generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    cards = []
    if not articles:
        cards.append('<section class="empty">条件に合うロボット・機械系AI研究ニュースは見つかりませんでした。</section>')
    for index, article in enumerate(articles, start=1):
        cards.append(f"""
        <article class="card">
          <div class="rank">#{index}</div>
          <div class="content">
            <h2><a href="{html.escape(article.link)}" target="_blank" rel="noopener noreferrer">{html.escape(article.title)}</a></h2>
            <p class="meta">{html.escape(article.source)} ・ {format_date(article.published)} ・ 関連度スコア {article.score}</p>
            <p>{html.escape(article.summary or '本文要約は取得できませんでした。リンク先を確認してください。')}</p>
            <p class="lens">研究で見る観点: ロボット本体・制御・認識・シミュレーション・実験評価に応用できるか。</p>
          </div>
        </article>
        """)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ロボットAI研究ニュース</title>
  <style>
    :root {{ color-scheme: light dark; --accent: #2563eb; --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; }}
    @media (prefers-color-scheme: dark) {{ :root {{ --bg: #020617; --card: #0f172a; --text: #e2e8f0; --muted: #94a3b8; }} }}
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }}
    header {{ padding: 40px 20px 24px; max-width: 960px; margin: auto; }}
    main {{ max-width: 960px; margin: auto; padding: 0 20px 48px; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 4vw, 3rem); }}
    .lead {{ color: var(--muted); margin: 0; }}
    .card, .empty {{ background: var(--card); border: 1px solid color-mix(in srgb, var(--muted) 24%, transparent); border-radius: 18px; padding: 20px; margin: 16px 0; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }}
    .card {{ display: grid; grid-template-columns: 56px 1fr; gap: 16px; }}
    .rank {{ width: 44px; height: 44px; border-radius: 999px; display: grid; place-items: center; background: var(--accent); color: white; font-weight: 700; }}
    h2 {{ margin: 0 0 8px; font-size: 1.25rem; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .meta, .lens, footer {{ color: var(--muted); font-size: 0.95rem; }}
    .lens {{ border-left: 4px solid var(--accent); padding-left: 12px; }}
    footer {{ max-width: 960px; margin: auto; padding: 0 20px 32px; }}
  </style>
</head>
<body>
  <header>
    <h1>ロボットAI研究ニュース</h1>
    <p class="lead">機械・ロボット研究に関連しやすいAIニュース / 論文情報を自動収集した個人用ページです。</p>
    <p class="lead">最終更新: {generated_at.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
  <footer>RSS記事のタイトル・要約・出典をキーワードでスコアリングしています。重要な研究判断では必ず一次情報を確認してください。</footer>
</body>
</html>
"""


def write_site(articles: list[Article], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.html"
    index_path.write_text(render_html(articles), encoding="utf-8")
    return index_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static robotics AI news website.")
    parser.add_argument("--output-dir", default=os.getenv("AI_NEWS_OUTPUT_DIR", "public"), help="Directory for generated site files.")
    parser.add_argument("--limit", type=int, default=int(os.getenv("AI_NEWS_LIMIT", "20")), help="Maximum number of articles to render.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    feeds = getenv_list("AI_NEWS_FEEDS", DEFAULT_FEEDS)
    hours = int(os.getenv("AI_NEWS_LOOKBACK_HOURS", "36"))
    articles = collect_articles(feeds, hours=hours, limit=args.limit)
    index_path = write_site(articles, Path(args.output_dir))
    print(f"Generated {index_path} with {len(articles)} article(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
