import os
import json
import requests
import feedparser
from datetime import datetime, timezone, timedelta
import random

BASE_DIR = "docs"
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")
TZ_UTC_8 = timezone(timedelta(hours=8))

def fetch_word_of_the_day():
    print("正在获取每日英语词汇...")
    try:
        # 使用随机高阶词汇获取释义
        word_list = ["ephemeral", "serendipity", "obfuscate", "sagacious", "cacophony", "alacrity", "ineffable", "sonder"]
        word = random.choice(word_list)
        res = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
        if res.status_code == 200:
            data = res.json()[0]
            meanings = data.get("meanings", [])[0]
            definition = meanings.get("definitions", [])[0].get("definition", "")
            example = meanings.get("definitions", [])[0].get("example", "No example available.")
            synonyms = meanings.get("synonyms", [])[:3]
            antonyms = meanings.get("antonyms", [])[:3]
            
            return {
                "word": word,
                "definition": definition,
                "example": example,
                "synonyms": ", ".join(synonyms) if synonyms else "None",
                "antonyms": ", ".join(antonyms) if antonyms else "None"
            }
    except Exception as e:
        print(f"词汇获取失败: {e}")
    return None

def fetch_wiki_trending():
    print("正在获取 Wikipedia 每日热门...")
    try:
        now = datetime.now(timezone.utc)
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{now.year}/{now.month:02d}/{now.day:02d}"
        headers = {'User-Agent': 'DailyNexusBot/1.0'}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            most_read = data.get("mostread", {}).get("articles", [])[:3]
            results = []
            for item in most_read:
                results.append({
                    "title": item.get("normalizedtitle", ""),
                    "extract": item.get("extract", ""),
                    "url": item.get("content_urls", {}).get("desktop", {}).get("page", "")
                })
            return results
    except Exception as e:
        print(f"Wiki获取失败: {e}")
    return []

def fetch_nasa_apod():
    print("正在获取 NASA 每日一图...")
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "title": data.get("title", ""),
                "url": data.get("url", ""),
                "explanation": data.get("explanation", "")
            }
    except Exception as e:
        print(f"NASA获取失败: {e}")
    return None

def fetch_rss_feeds():
    print("正在聚合全球 RSS 新闻...")
    feeds = {
        "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "NHK World": "https://www3.nhk.or.jp/rss/news/cat00.xml"
    }
    results = {}
    for name, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            items = []
            for entry in parsed.entries[:3]:
                items.append({
                    "title": entry.title,
                    "link": entry.link
                })
            results[name] = items
        except Exception as e:
            print(f"RSS获取失败 {name}: {e}")
    return results

def generate_dashboard():
    os.makedirs(BASE_DIR, exist_ok=True)
    now_str = datetime.now(TZ_UTC_8).strftime("%Y-%m-%d %H:%M")
    
    word_data = fetch_word_of_the_day()
    wiki_data = fetch_wiki_trending()
    nasa_data = fetch_nasa_apod()
    rss_data = fetch_rss_feeds()

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daily Nexus - 全知仪表盘</title>
    <style>
        :root {{
            --bg: #f5f5f7;
            --card-bg: rgba(255, 255, 255, 0.9);
            --text-main: #1d1d1f;
            --text-muted: #86868b;
            --accent: #0066cc;
            --border: #e5e5ea;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 20px 15px;
            -webkit-font-smoothing: antialiased;
        }}
        /* 强制锁定横向宽度，适配移动端最佳阅读体验 */
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 2rem; color: #1a252f; }}
        .header p {{ margin: 0; color: var(--text-muted); font-size: 0.9rem; }}
        
        .section {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02);
            backdrop-filter: blur(10px);
        }}
        .section-title {{
            font-size: 1.2rem;
            color: var(--accent);
            margin: 0 0 15px 0;
            display: flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 10px;
        }}
        
        /* 英语学习区块 */
        .word-title {{ font-size: 2rem; margin: 0 0 10px 0; text-transform: capitalize; color: #d35400; }}
        .word-meta {{ display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem; }}
        .word-meta span {{ background: #f8f9fa; padding: 6px 12px; border-radius: 8px; border: 1px solid #eee; }}
        
        /* Wiki 区块 */
        .wiki-item {{ margin-bottom: 15px; }}
        .wiki-item:last-child {{ margin-bottom: 0; }}
        .wiki-item a {{ text-decoration: none; color: var(--text-main); font-size: 1.1rem; display: block; margin-bottom: 5px; }}
        .wiki-item a:hover {{ color: var(--accent); }}
        .wiki-extract {{ font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; }}
        
        /* NASA 区块 */
        .nasa-img {{ width: 100%; border-radius: 12px; margin-bottom: 15px; }}
        .nasa-desc {{ font-size: 0.9rem; color: var(--text-muted); line-height: 1.6; }}
        
        /* RSS 区块 */
        .rss-source {{ margin-bottom: 20px; }}
        .rss-source:last-child {{ margin-bottom: 0; }}
        .rss-name {{ font-size: 1rem; color: #2c3e50; margin: 0 0 10px 0; background: #ecf0f1; display: inline-block; padding: 4px 10px; border-radius: 6px; }}
        .rss-list {{ list-style: none; padding: 0; margin: 0; }}
        .rss-list li {{ margin-bottom: 8px; padding-left: 15px; position: relative; }}
        .rss-list li::before {{ content: "→"; position: absolute; left: 0; color: var(--accent); }}
        .rss-list a {{ text-decoration: none; color: var(--text-main); font-size: 0.95rem; }}
        .rss-list a:hover {{ color: var(--accent); text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Daily Nexus</h1>
            <p>全知仪表盘 / 自动同步于: {now_str}</p>
        </div>
"""

    if word_data:
        html += f"""
        <div class="section">
            <h2 class="section-title">📚 Word of the Day</h2>
            <h3 class="word-title">{word_data['word']}</h3>
            <div class="word-meta">
                <span>Def: {word_data['definition']}</span>
                <span>Ex: {word_data['example']}</span>
                <span>Synonyms: {word_data['synonyms']}</span>
                <span>Antonyms: {word_data['antonyms']}</span>
            </div>
        </div>
"""

    if wiki_data:
        html += """<div class="section"><h2 class="section-title">🔍 Wikipedia Trending</h2>"""
        for item in wiki_data:
            html += f"""
            <div class="wiki-item">
                <a href="{item['url']}" target="_blank">{item['title']}</a>
                <div class="wiki-extract">{item['extract']}</div>
            </div>"""
        html += "</div>"

    if nasa_data:
        html += f"""
        <div class="section">
            <h2 class="section-title">🌌 World Photo</h2>
            <img src="{nasa_data['url']}" class="nasa-img" alt="NASA Image">
            <div style="font-weight: 600; margin-bottom: 10px;">{nasa_data['title']}</div>
            <div class="nasa-desc">{nasa_data['explanation']}</div>
        </div>
"""

    if rss_data:
        html += """<div class="section"><h2 class="section-title">📡 Global RSS Radar</h2>"""
        for source, items in rss_data.items():
            html += f"""
            <div class="rss-source">
                <h4 class="rss-name">{source}</h4>
                <ul class="rss-list">
            """
            for item in items:
                html += f"""<li><a href="{item['link']}" target="_blank">{item['title']}</a></li>"""
            html += "</ul></div>"
        html += "</div>"

    html += """
    </div>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print("Daily Nexus 仪表盘生成完毕！")

if __name__ == "__main__":
    generate_dashboard()
