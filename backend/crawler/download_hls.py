import os
import requests
from urllib.parse import urljoin
from tqdm import tqdm
import re

def extract_m3u8_url(page_url):
    """從歌頁 HTML 找到第一條 .m3u8 連結"""
    r = requests.get(page_url)
    # 簡單用 regex 抓 https://…m3u8
    m = re.search(r'https://[^"\']+\.m3u8', r.text)
    return m.group(0) if m else None

def download_and_merge(m3u8_url, out_dir, song_name):
    os.makedirs(out_dir, exist_ok=True)
    # 1) 下載 m3u8
    lines = requests.get(m3u8_url).text.splitlines()
    # 2) 提取 .ts 完整 URL
    ts_urls = [urljoin(m3u8_url, l) for l in lines if l and not l.startswith("#")]
    ts_files = []
    # 3) 下載每個 .ts
    for i, ts_url in enumerate(tqdm(ts_urls, desc=song_name)):
        fn = os.path.join(out_dir, f"part{i:04d}.ts")
        ts_files.append(fn)
        if not os.path.exists(fn):
            r = requests.get(ts_url, stream=True, headers={"User-Agent":"MyBot"})
            with open(fn, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
    # 4) 合併
    merged = os.path.join(out_dir, f"{song_name}.ts")
    with open(merged, "wb") as out:
        for fn in ts_files:
            with open(fn, "rb") as inp:
                out.write(inp.read())
    return merged

# ==== 主流程 ====
all_song_pages = fetch_song_pages(100)

for url in all_song_pages:
    # 取最後一段當歌名
    name = os.path.basename(url.rstrip("/")).replace(".html","")
    print(f"\n>> 處理 {name}")
    m3u8 = extract_m3u8_url(url)
    if not m3u8:
        print("  ⚠️ 無法找到 m3u8，跳過")
        continue
    out = download_and_merge(m3u8, os.path.join("downloads", name), name)
    print(f"  完成：{out}")
