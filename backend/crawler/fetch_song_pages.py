import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def fetch_song_pages(max_count=100):
    base_list_url = "https://streetvoice.com/music/popular?page={}"
    song_urls = []
    page = 1

    while len(song_urls) < max_count:
        res = requests.get(base_list_url.format(page))
        soup = BeautifulSoup(res.text, "html.parser")
        # === 根據實際 HTML 結構改這一行 selector! ===
        # 假設每首歌的卡片 <a class="music-list-item" href="/music/fi/re/..."></a>
        for a in soup.select("a.music-list-item"):
            href = a.get("href")
            full = urljoin("https://streetvoice.com", href)
            if full not in song_urls:
                song_urls.append(full)
            if len(song_urls) >= max_count:
                break
        print(f"Page {page} → 累積 {len(song_urls)} 首")
        page += 1
        if page > 20:  # safety break
            break

    return song_urls[:max_count]

# 測試
song_pages = fetch_song_pages(100)
print("共蒐集到歌頁：", len(song_pages))
