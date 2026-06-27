import os
import json
import requests
import feedparser
from datetime import datetime, timezone, timedelta
import random

BASE_DIR = "docs"
TZ_UTC_8 = timezone(timedelta(hours=8))

# 高阶英语词库池 (你可以随时在这里添加更多，或者改写代码去读取你的 EVP 词汇表文件)
WORD_LIST = [
    "ephemeral", "serendipity", "obfuscate", "sagacious", "cacophony", "alacrity", "ineffable", "sonder", 
    "luminous", "eloquent", "resilience", "mellifluous", "quintessential", "paradigm", "ebullient",
    "lethargic", "sycophant", "ubiquitous", "vicarious", "zealous", "aesthetic", "conundrum", "dichotomy",
    "epiphany", "facetious", "gregarious", "hubris", "idiosyncrasy", "juxtaposition", "kinetic",
    "labyrinth", "magnanimous", "nuance", "oxymoron", "panacea", "quixotic", "rhetoric", "stoic",
    "trepidation", "unilateral", "vindicate", "whimsical", "xenophobia", "yielding", "zenith"
]

def fetch_word_of_the_day():
    print("正在获取每日英语词汇...")
    try:
        word = random.choice(WORD_LIST)
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

def fetch_wiki_trending(now_utc):
    print("正在获取 Wikipedia 四大维度热门...")
    results = []
    
    # 维基百科 API 的 mostread 接口支持精确到某一天。
    # 我们利用时间偏移，精准获取这四个维度的数据。
    dates = [
        ("🔥 今日最热词条", now_utc - timedelta(days=1)),
        ("📅 昨日最热", now_utc - timedelta(days=2)),
        ("⏪ 一周最热 (上周同日)", now_utc - timedelta(days=7)),
        ("🕰️ 年度热门 (去年同日)", now_utc - timedelta(days=365))
    ]
    
    for label, d in dates:
        try:
            url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{d.year}/{d.month:02d}/{d.day:02d}"
            headers = {'User-Agent': 'DailyNexusBot/1.0'}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                most_read = data.get("mostread", {}).get("articles", [])
                
                # 提取当天的第一名，跳过无意义的 Main Page
                top_article = next((item for item in most_read if item.get("normalizedtitle") != "Main Page"), None)
                
                if top_article:
                    results.append({
                        "label": label,
                        "title": top_article.get("normalizedtitle", ""),
                        "extract": top_article.get("extract", ""),
                        "url": top_article.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "date_str": d.strftime("%Y-%m-%d")
                    })
        except Exception as e:
            print(f"Wiki获取失败 {label}: {e}")
            
    return results

def fetch_nasa_apod():
    print("正在获取 NASA 今日图片...")
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "title": data.get("title", "NASA Astronomy Picture"),
                "url": data.get("url", ""),
                "explanation": data.get("explanation", "No description available.")
            }
    except Exception as e:
        print(f"NASA获取失败: {e}")
    return None

def fetch_rss_feeds():
    print("正在聚合全球 RSS 新闻...")
    feeds = {
        "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "NHK World": "https://www3.nhk.or.jp/rss/news/cat00.xml",
        "TechCrunch": "https://techcrunch.com/feed/",
        "Wired": "https://www.wired.com/feed/rss"
    }
    results = {}
    for name, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            items = []
            for entry in parsed.entries[:4]:
                items.append({
                    "title": entry.title,
                    "link": entry.link
                })
            results[name] = items
        except Exception as e:
            print(f"RSS获取失败 {name}: {e}")
    return results

def save_daily_archive(word_data, wiki_data, nasa_data, rss_data, now_obj):
    year_str, month_str = str(now_obj.year), str(now_obj.month)
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"{now_obj.year}_{now_obj.month}_{now_obj.day}_{now_obj.strftime('%H%M')}.html"
    html_path = os.path.join(target_dir, filename)
    now_str = now_obj.strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Omni-Digest | {now_obj.strftime("%Y-%m-%d")}</title>
    <style>
        :root {{ --bg: #f5f5f7; --card-bg: #ffffff; --text-main: #1d1d1f; --text-muted: #86868b; --accent: #0066cc; --border: #e5e5ea; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .nav-back {{ padding: 15px; text-align: center; background: var(--card-bg); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }}
        .nav-back a {{ text-decoration: none; color: white; background: var(--accent); padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }}
        
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px 15px 50px 15px; box-sizing: border-box; }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 2rem; color: #1a252f; }}
        .header p {{ margin: 0; color: var(--text-muted); font-size: 0.95rem; font-weight: 500; }}
        
        .section {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }}
        .section-title {{ font-size: 1.15rem; color: var(--accent); margin: 0 0 15px 0; display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px dashed var(--border); padding-bottom: 10px; }}
        
        /* Word */
        .word-title {{ font-size: 2.2rem; margin: 0 0 10px 0; text-transform: capitalize; color: #d35400; font-family: Georgia, serif; }}
        .word-meta {{ display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem; }}
        .word-meta span {{ background: #f8f9fa; padding: 8px 12px; border-radius: 8px; border: 1px solid #eee; line-height: 1.4; }}
        
        /* Wiki */
        .wiki-item {{ margin-bottom: 22px; background: #fafafa; padding: 15px; border-radius: 10px; border-left: 4px solid var(--accent); }}
        .wiki-item:last-child {{ margin-bottom: 0; }}
        .wiki-label {{ font-size: 0.85rem; font-weight: bold; color: var(--accent); margin-bottom: 6px; display: block; text-transform: uppercase; letter-spacing: 0.5px; }}
        .wiki-item a {{ text-decoration: none; color: var(--text-main); font-size: 1.15rem; font-weight: 600; display: block; margin-bottom: 8px; }}
        .wiki-item a:hover {{ color: var(--accent); }}
        .wiki-extract {{ font-size: 0.95rem; color: var(--text-muted); line-height: 1.6; text-align: justify; }}
        
        /* NASA */
        .nasa-img {{ width: 100%; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .nasa-desc {{ font-size: 0.95rem; color: var(--text-muted); line-height: 1.6; text-align: justify; }}
        
        /* RSS */
        .rss-source {{ margin-bottom: 20px; }}
        .rss-source:last-child {{ margin-bottom: 0; }}
        .rss-name {{ font-size: 1rem; color: #2c3e50; margin: 0 0 10px 0; background: #ecf0f1; display: inline-block; padding: 4px 10px; border-radius: 6px; }}
        .rss-list {{ list-style: none; padding: 0; margin: 0; }}
        .rss-list li {{ margin-bottom: 10px; padding-left: 18px; position: relative; }}
        .rss-list li::before {{ content: "👉"; position: absolute; left: 0; color: var(--accent); font-size: 0.9rem; top: 2px; }}
        .rss-list a {{ text-decoration: none; color: var(--text-main); font-size: 0.95rem; line-height: 1.4; display: block; }}
        .rss-list a:hover {{ color: var(--accent); }}
    </style>
</head>
<body>
    <div class="nav-back"><a href="../../index.html">🔙 返回日历枢纽</a></div>
    <div class="container">
        <div class="header">
            <h1>Daily Nexus Archive</h1>
            <p>归档日期: {now_str}</p>
        </div>
"""

    if word_data:
        html += f"""
        <div class="section">
            <h2 class="section-title">📚 Word of the Day</h2>
            <h3 class="word-title">{word_data['word']}</h3>
            <div class="word-meta">
                <span>Definition: {word_data['definition']}</span>
                <span>Example: <i>"{word_data['example']}"</i></span>
                <span>Synonyms: {word_data['synonyms']}</span>
                <span>Antonyms: {word_data['antonyms']}</span>
            </div>
        </div>
"""

    if wiki_data:
        html += """<div class="section"><h2 class="section-title">🔍 Wikipedia Hall of Fame</h2>"""
        for item in wiki_data:
            html += f"""
            <div class="wiki-item">
                <span class="wiki-label">{item['label']} (记录于 {item['date_str']})</span>
                <a href="{item['url']}" target="_blank">{item['title']}</a>
                <div class="wiki-extract">{item['extract']}</div>
            </div>"""
        html += "</div>"

    if nasa_data:
        html += f"""
        <div class="section">
            <h2 class="section-title">🌌 Astronomy Picture</h2>
            <img src="{nasa_data['url']}" class="nasa-img" alt="NASA Image" loading="lazy">
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 10px; color:#1a252f;">{nasa_data['title']}</div>
            <div class="nasa-desc">{nasa_data['explanation']}</div>
        </div>
"""

    if rss_data:
        html += """<div class="section"><h2 class="section-title">📡 Global News Aggregator</h2>"""
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

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"每日数据已封印入库: {html_path}")


def generate_index():
    print("正在重新编译全知日历枢纽...")
    archive_data = {}
    if os.path.exists(BASE_DIR):
        years = [d for d in os.listdir(BASE_DIR) if d.isdigit()]
        for year in years:
            archive_data[year] = {}
            months = [d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()]
            for month in months:
                archive_data[year][month] = {}
                files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
                for file in files:
                    try:
                        parts = file.replace(".html", "").split('_')
                        if len(parts) >= 4:
                            day = parts[2]
                            time_str = f"{parts[3][:2]}:{parts[3][2:]}"
                            file_path = f"{year}/{month}/{file}"
                            
                            if day not in archive_data[year][month]:
                                archive_data[year][month][day] = []
                                
                            archive_data[year][month][day].append({
                                "time": time_str,
                                "path": file_path,
                                "title": "🌍 全知日报已送达"
                            })
                    except:
                        pass
                        
    json_data = json.dumps(archive_data)

    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daily Nexus - 全知日历枢纽</title>
    <style>
        :root { --bg: #f5f5f7; --text: #333; --muted: #888; --primary: #0066cc; --border: #e0e0e0; --card: #fff; }
        body, html { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); margin: 0; padding: 0; color: var(--text); height: 100%; }
        .container { max-width: 800px; margin: 0 auto; padding-bottom: 20px; box-sizing: border-box;}
        
        .header-panel { text-align: center; padding: 35px 20px 20px 20px; border-bottom: 1px solid var(--border); background: var(--card); margin-bottom: 20px;}
        .header-panel h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 8px 0; color: #1a252f; }
        .header-panel p { margin: 0; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); font-weight: 600;}
        
        .controls { background: var(--bg); padding: 0 20px 15px 20px; display: flex; justify-content: center; align-items: center; gap: 10px; }
        .control-btn { background: var(--primary); color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 14px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
        .control-btn:active { opacity: 0.8; transform: scale(0.95); }
        .select-box { padding: 6px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 15px; background: #fff; outline: none; font-weight: bold; cursor: pointer; }
        
        .calendar-wrapper { background: var(--card); padding: 20px; margin: 0 15px 20px 15px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
        .weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; font-size: 13px; color: var(--muted); margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
        .days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
        .day-cell { aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 600; border-radius: 10px; cursor: pointer; position: relative; transition: all 0.2s; }
        .day-cell.empty { visibility: hidden; }
        .day-cell.has-news { color: var(--text); }
        .day-cell.no-news { color: #ccc; }
        .day-cell.selected { background: #eef5ff; border: 1px solid var(--primary); color: var(--primary); }
        .day-cell.today { background: #f0f0f0; border: 1px solid #ddd; }
        .dot { width: 5px; height: 5px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 6px; display: none; }
        .day-cell.has-news .dot { display: block; }
        
        .feed-list { padding: 0 15px; display: flex; flex-direction: column; gap: 12px; }
        .feed-item { background: var(--card); border-radius: 14px; padding: 18px; display: flex; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); border-left: 4px solid var(--primary); transition: all 0.2s; }
        .feed-item:active { transform: scale(0.98); background: #fafafa; }
        .feed-time { font-size: 15px; font-weight: bold; color: var(--primary); font-family: monospace; }
        .feed-title { font-size: 15px; font-weight: bold; color: #333; margin-left: 15px; flex: 1; }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; background: var(--card); border-radius: 14px; border: 1px dashed #ccc;}
    </style>
</head>
<body>
    <div class="header-panel">
        <h1>Daily Nexus</h1>
        <p>全知日历枢纽</p>
    </div>
    
    <div class="container">
        <div class="controls">
            <button class="control-btn" id="prevBtn">&lt;</button>
            <select class="select-box" id="yearSelect"></select>
            <select class="select-box" id="monthSelect">
                <option value="1">01月</option><option value="2">02月</option><option value="3">03月</option>
                <option value="4">04月</option><option value="5">05月</option><option value="6">06月</option>
                <option value="7">07月</option><option value="8">08月</option><option value="9">09月</option>
                <option value="10">10月</option><option value="11">11月</option><option value="12">12月</option>
            </select>
            <button class="control-btn" id="nextBtn">&gt;</button>
            <button class="control-btn" id="todayBtn">今日</button>
        </div>

        <div class="calendar-wrapper">
            <div class="weekdays"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>
            <div class="days-grid" id="daysGrid"></div>
        </div>

        <div class="feed-list" id="feedList"></div>
    </div>

    <script>
        const archiveData = {REPLACEME_JSON_DATA};
        const today = new Date();
        let selectedYear = today.getFullYear();
        let selectedMonth = today.getMonth() + 1;
        let selectedDay = today.getDate();

        const yearSelect = document.getElementById('yearSelect');
        const monthSelect = document.getElementById('monthSelect');
        const daysGrid = document.getElementById('daysGrid');
        const feedList = document.getElementById('feedList');

        function initDropdowns() {
            const years = Object.keys(archiveData).map(Number).sort((a, b) => b - a);
            if (!years.includes(selectedYear)) years.unshift(selectedYear);
            years.forEach(y => {
                const opt = document.createElement('option'); opt.value = y; opt.textContent = y + ' 年';
                yearSelect.appendChild(opt);
            });
            yearSelect.value = selectedYear; monthSelect.value = selectedMonth;
        }

        function renderCalendar(year, month) {
            daysGrid.innerHTML = '';
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            const daysInMonth = new Date(year, month, 0).getDate();
            
            for (let i = 1; i < startDay; i++) {
                const empty = document.createElement('div'); empty.className = 'day-cell empty';
                daysGrid.appendChild(empty);
            }
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {};
            
            for (let day = 1; day <= daysInMonth; day++) {
                const cell = document.createElement('div'); cell.className = 'day-cell'; cell.textContent = day;
                const dot = document.createElement('div'); dot.className = 'dot'; cell.appendChild(dot);
                
                if (monthData[day] && monthData[day].length > 0) cell.classList.add('has-news'); else cell.classList.add('no-news');
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) cell.classList.add('today');
                if (year === selectedYear && month === selectedMonth && day === selectedDay) cell.classList.add('selected');
                
                cell.addEventListener('click', () => {
                    selectedYear = year; selectedMonth = month; selectedDay = day;
                    renderCalendar(year, month); renderFeedList(year, month, day);
                });
                daysGrid.appendChild(cell);
            }
        }

        function renderFeedList(year, month, day) {
            feedList.innerHTML = '';
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : null;
            
            if (dayData && dayData.length > 0) {
                dayData.forEach(item => {
                    const a = document.createElement('a'); a.href = item.path; a.className = 'feed-item';
                    a.innerHTML = `<span class="feed-time">${item.time}</span><span class="feed-title">${item.title}</span> ➔`;
                    feedList.appendChild(a);
                });
            } else {
                feedList.innerHTML = '<div class="empty-state">当日档案空空如也</div>';
            }
        }

        yearSelect.addEventListener('change', (e) => { selectedYear = parseInt(e.target.value); renderCalendar(selectedYear, selectedMonth); });
        monthSelect.addEventListener('change', (e) => { selectedMonth = parseInt(e.target.value); renderCalendar(selectedYear, selectedMonth); });
        document.getElementById('prevBtn').addEventListener('click', () => { selectedMonth--; if (selectedMonth < 1) { selectedMonth = 12; selectedYear--; yearSelect.value = selectedYear; } monthSelect.value = selectedMonth; renderCalendar(selectedYear, selectedMonth); });
        document.getElementById('nextBtn').addEventListener('click', () => { selectedMonth++; if (selectedMonth > 12) { selectedMonth = 1; selectedYear++; yearSelect.value = selectedYear; } monthSelect.value = selectedMonth; renderCalendar(selectedYear, selectedMonth); });
        document.getElementById('todayBtn').addEventListener('click', () => { selectedYear = today.getFullYear(); selectedMonth = today.getMonth() + 1; selectedDay = today.getDate(); yearSelect.value = selectedYear; monthSelect.value = selectedMonth; renderCalendar(selectedYear, selectedMonth); renderFeedList(selectedYear, selectedMonth, selectedDay); });

        initDropdowns(); renderCalendar(selectedYear, selectedMonth); renderFeedList(selectedYear, selectedMonth, selectedDay);
    </script>
</body>
</html>"""

    final_html = html_template.replace("{REPLACEME_JSON_DATA}", json_data)
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    print("主页日历枢纽 index.html 编译同步完成！")

if __name__ == "__main__":
    now_utc = datetime.now(timezone.utc)
    now_obj = datetime.now(TZ_UTC_8)
    
    word_data = fetch_word_of_the_day()
    wiki_data = fetch_wiki_trending(now_utc)
    nasa_data = fetch_nasa_apod()
    rss_data = fetch_rss_feeds()
    
    save_daily_archive(word_data, wiki_data, nasa_data, rss_data, now_obj)
    generate_index()
