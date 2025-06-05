# crawler/hls_crawler.py

import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm

def fetch_song_pages(max_count=100):
    """
    從 StreetVoice 的熱門歌曲列表（或最新歌曲列表）分頁，
    抓取前 max_count 首歌的「歌頁 URL」並回傳成 list。
    """
    base_list_url = "https://streetvoice.com/music/popular?page={}"  # 若要抓最新歌曲可改 https://streetvoice.com/music/newest?page={}
    song_urls = []
    page = 1

    while len(song_urls) < max_count:
        res = requests.get(base_list_url.format(page))
        if res.status_code != 200:
            print(f"第 {page} 頁請求失敗，狀態碼：{res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")

        # ─── 以下這行 selector 需要你到瀏覽器開發者工具辨識，再依實際 HTML 結構填寫 ───
        # 例如：如果每首歌的卡片是 <a class="music-list-item" href="/music/fi/re/…">…</a>
        # 那就可以用下面這個 selector：
        anchors = soup.select("a.music-list-item")

        # 如果你發現不是這個 class，就先用開發者工具看顯示在列表中的 <a> 標籤的 class 或 data-attribute，再改成「soup.select('a.實際class')」。
        # 例如：soup.select("div.song-card a") 或 soup.select("a[href^='/music/']") 等都可以。

        if not anchors:
            print(f"第 {page} 頁沒抓到歌曲連結，請檢查 selector 是否正確。")
            break

        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            full_url = urljoin("https://streetvoice.com", href)
            if full_url not in song_urls:
                song_urls.append(full_url)
            if len(song_urls) >= max_count:
                break

        print(f"已蒐集到 {len(song_urls)} 首歌頁 URL（從第 {page} 頁）")
        page += 1
        if page > 20:  # 為安全起見，最多只抓 20 頁，避免無限循環
            break

    return song_urls[:max_count]


def extract_m3u8_url(page_url):
    """
    從單一「歌頁」(page_url) 的 HTML 內容，用正規表達式或檢查 <script>、<audio> 標籤，
    找到第一條 .m3u8 播放清單的完整 URL 並回傳；若找不到就回 None。
    """
    try:
        r = requests.get(page_url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"無法請求 {page_url}：{e}")
        return None

    html = r.text

    # 最簡單的方法：用 regex 抓 "https://...m3u8"
    m = re.search(r'https://[^"\']+\.m3u8', html)
    if m:
        return m.group(0)

    # 如果 regex 找不到，你也可以改用 BeautifulSoup 去搜尋 <audio> 或 <source> 
    # 但通常街聲會把 .m3u8 連結寫在 <script> 裡，或者放在 <audio src="blob:…">，而真正的 URL 正如我們之前抓到的那樣。

    return None


def download_and_merge(m3u8_url, out_dir, song_name):
    """
    1) 下載 m3u8 清單
    2) 解析出所有 .ts 片段的相對/絕對 URL
    3) 依序下載每個 .ts 片段到 out_dir
    4) 合併成一個完整的 .ts 檔案，存成 out_dir/{song_name}.ts
    回傳合併後的 ts 檔案路徑。
    """
    os.makedirs(out_dir, exist_ok=True)
    merged_path = os.path.join(out_dir, f"{song_name}.ts")

    # 如果已經合併過，就直接回傳
    if os.path.exists(merged_path):
        return merged_path

    # 1) 下載 m3u8 清單
    try:
        m3u8_resp = requests.get(m3u8_url, timeout=10)
        m3u8_resp.raise_for_status()
    except Exception as e:
        print(f"下載 m3u8 失敗：{e} ({m3u8_url})")
        return None

    lines = m3u8_resp.text.splitlines()

    # 2) 解析出所有 .ts URL（忽略 #EXT-* 開頭的行）
    ts_urls = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 如果 line 已經是完整 URL，就直接用；如果是相對路徑，就用 urljoin 拼成完整 URL
        full_ts_url = urljoin(m3u8_url, line)
        ts_urls.append(full_ts_url)

    if not ts_urls:
        print(f"在 m3u8 內容中找不到任何 .ts 片段：{m3u8_url}")
        return None

    # 3) 依序下載 .ts
    ts_files = []
    print(f"開始下載「{song_name}」的 {len(ts_urls)} 片段…")
    for idx, ts_url in enumerate(tqdm(ts_urls, desc=song_name)):
        ts_filename = os.path.join(out_dir, f"part_{idx:04d}.ts")
        ts_files.append(ts_filename)

        # 如果已經下載過，就跳過
        if os.path.exists(ts_filename):
            continue

        try:
            r = requests.get(ts_url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            with open(ts_filename, "wb") as fp:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        fp.write(chunk)
        except Exception as e:
            print(f"下載片段失敗 ({ts_url})：{e}")
            # 若單一片段下載失敗，你可以選擇跳過或重試，這裡先跳過
            continue

    # 4) 合併成一個 ts 檔案
    print(f"開始合併 {song_name} 的所有片段 → {merged_path}")
    try:
        with open(merged_path, "wb") as wfp:
            for ts_file in ts_files:
                if os.path.exists(ts_file):
                    with open(ts_file, "rb") as rfp:
                        wfp.write(rfp.read())
    except Exception as e:
        print(f"合併 ts 失敗：{e}")
        return None

    return merged_path


def run_full_crawl(max_songs=100):
    """
    1) 先呼叫 fetch_song_pages(max_songs) 拿到最多 max_songs 首歌的 URL 列表
    2) 對每個歌頁 URL 執行 extract_m3u8_url，若取得 m3u8_url 就呼叫 download_and_merge
    3) 最後回傳 True 代表整個流程（包括所有歌曲）都跑完了
    """

    pages = fetch_song_pages(max_songs)
    if not pages:
        print("沒有抓到任何歌頁 URL，流程結束")
        return False

    for page_url in pages:
        # 從 URL 最後一段當作歌名（去掉 query 或 .html）
        # 例如 page_url = "https://streetvoice.com/music/fi/re/fireex168"
        # 則 song_name = "fireex168"
        raw = page_url.rstrip("/").split("/")[-1]
        song_name = raw.replace(".html", "")

        print(f"\n── 處理歌曲：{song_name} ({page_url}) ──")
        m3u8 = extract_m3u8_url(page_url)
        if not m3u8:
            print(f"找不到 .m3u8，跳過：{page_url}")
            continue

        merged = download_and_merge(m3u8, os.path.join("downloads", song_name), song_name)
        if merged:
            print(f"已完成：{merged}")
        else:
            print(f"下載或合併失敗：{song_name}")

    return True
