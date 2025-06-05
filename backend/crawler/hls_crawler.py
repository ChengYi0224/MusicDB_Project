# crawler/hls_crawler.py

import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm import tqdm
import time
import uuid
import subprocess # 用於 ffmpeg
import json
import shutil # 用於合併 .ts 檔案後的清理工作

from selenium import webdriver
from selenium.webdriver.common.by import By
# Edge WebDriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- ANSI 顏色代碼 ---
class AnsiColors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- 更新後的 Print 函數 ---
def print_warning(message):
    print(f"{AnsiColors.RED}{AnsiColors.BOLD}[警告]{AnsiColors.ENDC} {message}")

def print_error(message):
    print(f"{AnsiColors.RED}{AnsiColors.BOLD}[錯誤]{AnsiColors.ENDC} {message}")

def print_info(message):
    print(f"{AnsiColors.BLUE}{message}{AnsiColors.ENDC}")

def print_success(message):
    print(f"{AnsiColors.YELLOW}{message}{AnsiColors.ENDC}")
# --- Print 函數更新結束 ---


# --- 配置常數 ---
TARGET_SITE_DOMAIN = "https://streetvoice.com"
SONG_LIST_BROWSE_URL = f"{TARGET_SITE_DOMAIN}/music/browse/"

# TODO: 請使用瀏覽器開發者工具檢查並更新以下 selectors！
LOAD_MORE_BUTTON_SELECTOR = "button.btn-loadmore"
SONG_LINK_SELECTOR_ON_BROWSE_PAGE = "li.work-item div.work-item-info > h4 > a"
SONG_TITLE_SELECTOR = "h1.text-break.text-white"
ARTIST_NAME_SELECTOR = "div.page-user-block div.user-info h3 > a"
MAIN_PLAY_BUTTON_SELECTOR = "button.btn-play.btn-primary[data-type='song']"


REQUEST_DELAY_SECONDS = 2
SCROLL_PAUSE_TIME = 3
MAX_SCROLL_ATTEMPTS = 15
DOWNLOAD_BASE_DIR = "downloads_streetvoice_selenium_edge"
MSEDGEDRIVER_PATH = None
M3U8_WAIT_TIME_SECONDS = 3 # 稍微縮短一點，因為主要靠 API
PLAY_CLICK_WAIT_TIME_SECONDS = 3 # 點擊播放後等待 API 請求的時間 (可能不需要這麼長了)


# --- WebDriver 設定 (改為 Edge) ---
def setup_driver():
    edge_options = EdgeOptions()
    # edge_options.add_argument("--headless")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62")
    # edge_options.add_argument('--blink-settings=imagesEnabled=false') # 如果不需要圖片，可以加速

    if MSEDGEDRIVER_PATH:
        service = EdgeService(executable_path=MSEDGEDRIVER_PATH)
        driver = webdriver.Edge(service=service, options=edge_options)
    else:
        try:
            driver = webdriver.Edge(options=edge_options)
        except WebDriverException as e:
            print_error(f"無法初始化 EdgeDriver: {e}")
            print_info("請確保已下載與您的 Microsoft Edge 瀏覽器版本匹配的 msedgedriver，")
            print_info("並將其路徑加入系統 PATH，或在腳本中設定 MSEDGEDRIVER_PATH。")
            print_info("Edge WebDriver 下載: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
            return None
        except Exception as e_other:
            print_error(f"初始化 EdgeDriver 時發生其他錯誤: {e_other}")
            return None
    driver.implicitly_wait(5)
    return driver

# --- 輔助函數 (sanitize_filename, get_song_duration_*, 等與先前版本相同) ---
def sanitize_filename(name):
    if not name: name = "unknown"
    name = re.sub(r'[\\/*?:"<>|]', "", name); name = name.replace(" ", "_")
    return name[:100]

def get_song_duration_ffmpeg(file_path):
    ffprobe_cmd = "ffprobe"
    if not os.path.exists(file_path): print_warning(f"時長分析 - 檔案不存在: {file_path}"); return None
    command = [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode != 0: print_warning(f"時長分析 - ffprobe 錯誤 (碼 {result.returncode}): {result.stderr.strip()}"); return None
        duration_str = result.stdout.strip()
        if not duration_str: print_warning(f"時長分析 - ffprobe 無輸出。"); return None
        return float(duration_str)
    except FileNotFoundError: print_error(f"時長分析 - ffprobe ('{ffprobe_cmd}') 找不到。"); return None
    except ValueError: print_warning(f"時長分析 - ffprobe 輸出 '{result.stdout.strip()}' 轉換數字失敗。"); return None
    except Exception as e: print_warning(f"時長分析 - 未知錯誤: {e}"); return None

def get_song_duration_from_m3u8(m3u8_content):
    total_duration = 0.0; found_extinf = False
    if not m3u8_content: return None
    for line in m3u8_content.splitlines():
        if line.startswith("#EXTINF:"):
            try: total_duration += float(line.split(":")[1].split(",")[0]); found_extinf = True
            except Exception: print_warning(f"解析 #EXTINF 行失敗: {line}")
    return total_duration if found_extinf else None

# --- Selenium 版本爬蟲核心函數 ---
def fetch_song_page_urls_selenium(driver, max_count=100):
    # (此函數與您提供的版本 v4 相同，此處為簡潔省略，實際使用時請包含完整函數)
    song_page_urls = set()
    print_info(f"開始使用 Selenium 從 {SONG_LIST_BROWSE_URL} 蒐集歌曲頁面 URL...")
    try:
        driver.get(SONG_LIST_BROWSE_URL)
        print_info(f"  已導覽至: {SONG_LIST_BROWSE_URL}")
        time.sleep(REQUEST_DELAY_SECONDS + 3)

        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, LOAD_MORE_BUTTON_SELECTOR))
            )
            print_info("  偵測到「點我看更多」按鈕，嘗試點擊...")
            driver.execute_script("arguments[0].click();", load_more_button) # 使用 JS 點擊
            print_info("    按鈕已點擊，等待內容載入...")
            time.sleep(SCROLL_PAUSE_TIME + 2)
        except TimeoutException:
            print_info("  未找到可點擊的「點我看更多」按鈕 (逾時)，或 selector 失效。將直接嘗試滾動。")
        except Exception as e: 
            print_warning(f"點擊「點我看更多」按鈕時發生錯誤: {e}")

        scroll_attempts = 0
        no_new_songs_streak = 0
        collected_this_session = 0

        while collected_this_session < max_count and scroll_attempts < MAX_SCROLL_ATTEMPTS:
            scroll_attempts += 1
            print_info(f"  嘗試滾動第 {scroll_attempts}/{MAX_SCROLL_ATTEMPTS} 次...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print_info(f"    已滾動到底部，等待 {SCROLL_PAUSE_TIME} 秒讓內容載入...")
            time.sleep(SCROLL_PAUSE_TIME)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            anchors = soup.select(SONG_LINK_SELECTOR_ON_BROWSE_PAGE)
            
            current_round_found_new = False
            for a in anchors:
                href = a.get("href")
                if not href: continue
                full_url = urljoin(TARGET_SITE_DOMAIN, href)
                if full_url not in song_page_urls:
                    song_page_urls.add(full_url)
                    collected_this_session +=1
                    current_round_found_new = True
                    print_info(f"    蒐集到 URL ({len(song_page_urls)}): {full_url}") 
                    if collected_this_session >= max_count: break
            
            if collected_this_session >= max_count:
                print_info("  已達到本次運行目標歌曲數量。")
                break

            new_height = driver.execute_script("return document.body.scrollHeight")
            if not current_round_found_new and new_height == last_height:
                no_new_songs_streak +=1
                print_info(f"    此次滾動未發現新歌曲且頁面高度未改變 (連續 {no_new_songs_streak} 次)。")
                if no_new_songs_streak >= 3:
                    print_info("    連續多次滾動未發現新內容，可能已達頁面底部。停止滾動。")
                    break
            else:
                no_new_songs_streak = 0
    except TimeoutException:
        print_error(f"頁面載入超時: {SONG_LIST_BROWSE_URL}")
    except Exception as e:
        print_error(f"抓取歌曲頁面 URL 時發生錯誤: {e}")
    
    final_urls = list(song_page_urls)
    print_info(f"總共從網站蒐集到 {len(final_urls)} 個不重複的歌曲頁面 URL。")
    return final_urls


def extract_song_metadata_selenium(driver, song_page_url):
    """
    使用 Selenium 導覽頁面，並透過模擬 API 請求來獲取 m3u8 URL。
    (更新版：即使 csrftoken 未找到，也嘗試請求 API)
    """
    metadata = {
        "song_page_url": song_page_url, "title": None, "artist_name": None, "m3u8_url": None,
    }
    print_info(f"  使用 Selenium 導覽至歌曲頁面: {song_page_url}")
    try:
        driver.get(song_page_url)
        print_info(f"    頁面已導覽，等待頁面元素...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SONG_TITLE_SELECTOR))
        )
        
        # 嘗試獲取 csrftoken，但不強制要求
        csrftoken = None
        print_info("      嘗試獲取 'csrftoken' cookie...")
        try:
            # 等待 cookie 或頁面某個指示 JS 已完成的元素
            time.sleep(2) # 給 JS 一點時間設定 cookie
            cookies_after_load = driver.get_cookies()
            for cookie in cookies_after_load:
                if cookie['name'] == 'csrftoken':
                    csrftoken = cookie['value']
                    print_success("      成功從 cookie 獲取到 'csrftoken'！")
                    break
            if not csrftoken: # 如果 cookie 中沒有，嘗試從 input (較不可能)
                try:
                    csrf_input = driver.find_element(By.NAME, "csrfmiddlewaretoken")
                    csrftoken = csrf_input.get_attribute("value")
                    if csrftoken: print_success("      成功從頁面 input 獲取到 'csrftoken'！")
                except NoSuchElementException:
                    pass # 找不到 input 就忽略
        except Exception as e_cookie:
            print_warning(f"獲取 csrftoken 時發生異常: {e_cookie}")

        if not csrftoken:
            print_warning("未能獲取到 'csrftoken'。將嘗試在沒有它的情況下發送 API 請求。")


        page_soup = BeautifulSoup(driver.page_source, "html.parser")
        title_element = page_soup.select_one(SONG_TITLE_SELECTOR)
        if title_element: metadata["title"] = title_element.text.strip()
        artist_element = page_soup.select_one(ARTIST_NAME_SELECTOR)
        if artist_element: metadata["artist_name"] = artist_element.text.strip()
        
        print_info("    準備模擬 API 請求以獲取 m3u8 URL...")
        song_id = None
        try:
            song_id = re.search(r'/songs/(\d+)/?$', song_page_url).group(1)
        except AttributeError:
            try:
                # 嘗試從多個可能的播放按鈕獲取 data-id
                possible_play_buttons_selectors = [
                    MAIN_PLAY_BUTTON_SELECTOR, # 主要的播放按鈕
                    "button.btn-play[data-id]" # 其他可能的播放按鈕
                ]
                for btn_selector in possible_play_buttons_selectors:
                    try:
                        play_button = driver.find_element(By.CSS_SELECTOR, btn_selector)
                        song_id = play_button.get_attribute("data-id")
                        if song_id: break
                    except NoSuchElementException:
                        continue
                if song_id: print_info(f"      從播放按鈕 data-id 中提取 Song ID: {song_id}")
                else: print_error(f"無法從 URL 或任何已知播放按鈕中找到 Song ID。")
            except Exception as e_btn_id:
                 print_error(f"從播放按鈕提取 Song ID 時出錯: {e_btn_id}")
                 return metadata

        if not song_id: print_error("Song ID 為空，無法發起 API 請求。"); return metadata

        # 獲取當前 Selenium session 的 cookies 以便 requests 使用
        current_driver_cookies = driver.get_cookies()
        session_requests_cookies = {cookie['name']: cookie['value'] for cookie in current_driver_cookies}

        api_url = f"https://streetvoice.com/api/v5/song/{song_id}/hls/file/"
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent;"),
            'Referer': song_page_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://streetvoice.com'
        }
        if csrftoken: # 只有在 csrftoken 存在時才加入到 header
            headers['X-Csrftoken'] = csrftoken
        
        print_info(f"    正在向 API ({api_url}) 發送 POST 請求 (X-Csrftoken: {'存在' if csrftoken else '不存在'})")
        try:
            # 注意：根據您提供的 `play/` 請求截圖，`Content-Length: 0`，所以不傳 `data` 或傳 `data={}`
            response = requests.post(api_url, headers=headers, cookies=session_requests_cookies, timeout=15)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data and "file" in response_data and response_data["file"]:
                metadata["m3u8_url"] = response_data["file"]
                print_success(f"    成功從 API 獲取 m3u8 URL: {metadata['m3u8_url']}")
            else:
                print_warning(f"API 回應成功，但 JSON 中沒有 'file' 鍵或其值為空。回應: {response_data}")
        except requests.exceptions.HTTPError as e_http:
            print_error(f"模擬 API 請求時發生 HTTP 錯誤: {e_http} - 回應內容: {e_http.response.text[:200] if e_http.response else '無回應內容'}")
        except requests.exceptions.RequestException as e_req:
            print_error(f"模擬 API 請求時發生網路錯誤: {e_req}")
        except json.JSONDecodeError:
            print_error(f"無法解析 API 回應的 JSON。收到的內容: {response.text[:200]}")

    except Exception as e:
        print_error(f"提取歌曲元資料時發生未知錯誤 ({song_page_url}): {e}")
    return metadata

def download_and_merge_song(m3u8_url, output_dir, output_filename_base):
    """
    下載並合併 HLS 串流，儲存為 .ts 檔案。
    (更新版：使用 shutil.rmtree() 進行清理，更穩定)
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_filename_base = sanitize_filename(output_filename_base)
    merged_ts_path = os.path.join(output_dir, f"{safe_filename_base}.ts")

    if os.path.exists(merged_ts_path):
        print_info(f"    檔案已存在: {merged_ts_path}")
        m3u8_content_for_existing = None
        try:
            m3u8_resp_existing = requests.get(m3u8_url, timeout=10)
            m3u8_resp_existing.raise_for_status()
            m3u8_content_for_existing = m3u8_resp_existing.text
        except Exception: pass
        return merged_ts_path, m3u8_content_for_existing

    print_info(f"    準備從 {m3u8_url} 下載歌曲...")
    m3u8_content = None
    try:
        m3u8_resp = requests.get(m3u8_url, timeout=15)
        m3u8_resp.raise_for_status()
        m3u8_content = m3u8_resp.text
    except requests.exceptions.RequestException as e:
        print_error(f"下載 m3u8 列表失敗 ({m3u8_url}): {e}")
        return None, None

    lines = m3u8_content.splitlines()
    ts_urls = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        full_ts_url = urljoin(m3u8_url, line)
        ts_urls.append(full_ts_url)

    if not ts_urls:
        print_error(f"在 m3u8 內容中找不到 .ts 片段: {m3u8_url}")
        return None, m3u8_content

    # 為每個歌曲的 ts 片段建立獨立的臨時下載目錄
    temp_ts_dir = os.path.join(output_dir, f"{safe_filename_base}_temp_ts_parts")
    os.makedirs(temp_ts_dir, exist_ok=True)

    ts_files_to_merge = []
    print_info(f"    開始下載 '{safe_filename_base}' 的 {len(ts_urls)} 個 .ts 片段到 '{temp_ts_dir}'...")
    for idx, ts_url in enumerate(tqdm(ts_urls, desc=f"TS-{safe_filename_base[:20]}", unit="片段", ncols=100, leave=False)):
        ts_temp_filename = os.path.join(temp_ts_dir, f"part_{idx:04d}.ts")
        if os.path.exists(ts_temp_filename) and os.path.getsize(ts_temp_filename) > 0:
            ts_files_to_merge.append(ts_temp_filename)
            continue
        try:
            ts_resp = requests.get(ts_url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            ts_resp.raise_for_status()
            with open(ts_temp_filename, "wb") as fp:
                for chunk in ts_resp.iter_content(chunk_size=8192):
                    if chunk: fp.write(chunk)
            ts_files_to_merge.append(ts_temp_filename)
        except Exception as e:
            print_warning(f"下載片段 {idx+1} ({ts_url}) 失敗: {e}")

    if not ts_files_to_merge:
        print_error(f"'{safe_filename_base}' 沒有任何 .ts 片段成功下載。")
        if os.path.exists(temp_ts_dir):
            try: shutil.rmtree(temp_ts_dir) # 如果目錄存在但下載失敗，也用 rmtree 清理
            except Exception as e_rm: print_warning(f"清理失敗的臨時目錄時出錯: {e_rm}")
        return None, m3u8_content

    print_info(f"    正在合併 '{safe_filename_base}' 的 {len(ts_files_to_merge)} 個 .ts 片段 -> {merged_ts_path}")
    try:
        with open(merged_ts_path, "wb") as wfp:
            for ts_file_path in ts_files_to_merge:
                if os.path.exists(ts_file_path):
                    with open(ts_file_path, "rb") as rfp:
                        wfp.write(rfp.read())

        # --- ★★★ 修改在這裡 ★★★ ---
        # 合併完成後，使用 shutil.rmtree() 刪除整個臨時目錄及其所有內容
        if os.path.exists(temp_ts_dir):
            print_info(f"    正在清理臨時目錄: {temp_ts_dir}")
            shutil.rmtree(temp_ts_dir)
        # --- 修改結束 ---

    except Exception as e:
        print_error(f"合併 .ts 檔案失敗: {e}")
        return None, m3u8_content

    return merged_ts_path, m3u8_content

def run_song_crawler(max_songs_to_crawl=10, songs_output_filepath="crawled_songs_metadata_selenium_edge.txt"):
    if not all([LOAD_MORE_BUTTON_SELECTOR, SONG_LINK_SELECTOR_ON_BROWSE_PAGE, SONG_TITLE_SELECTOR, ARTIST_NAME_SELECTOR, MAIN_PLAY_BUTTON_SELECTOR]):
        print_error("必要的 CSS Selectors (包含 MAIN_PLAY_BUTTON_SELECTOR) 未在腳本頂部完整設定。請更新後再執行。")
        return []

    driver = setup_driver()
    if not driver:
        print_error("WebDriver 初始化失敗，爬蟲無法執行。")
        return []

    crawled_songs_data = []
    processed_song_identifiers_runtime = set()
    previously_crawled_page_urls_from_file = set()

    if os.path.exists(songs_output_filepath):
        try:
            with open(songs_output_filepath, "r", encoding="utf-8") as f_read:
                for line in f_read:
                    try:
                        song_data_dict = eval(line.strip())
                        if isinstance(song_data_dict, dict) and "source_page_url" in song_data_dict:
                            previously_crawled_page_urls_from_file.add(song_data_dict["source_page_url"])
                    except Exception: pass
            if previously_crawled_page_urls_from_file:
                print_info(f"從 {songs_output_filepath} 讀取到 {len(previously_crawled_page_urls_from_file)} 個已處理過的歌曲頁面 URL。")
        except Exception as e:
            print_warning(f"讀取已處理歌曲紀錄檔 {songs_output_filepath} 失敗: {e}")
    
    all_potential_song_urls = []
    try:
        fetch_max_count = max_songs_to_crawl + len(previously_crawled_page_urls_from_file) + 10
        all_potential_song_urls = fetch_song_page_urls_selenium(driver, max_count=fetch_max_count)
    except Exception as e:
        print_error(f"在 fetch_song_page_urls_selenium 階段發生嚴重錯誤: {e}")
    
    if not all_potential_song_urls:
        print_info("未能獲取任何歌曲頁面 URL，流程結束。")
        if driver: driver.quit()
        return []
    
    actual_urls_to_process = [
        url for url in all_potential_song_urls if url not in previously_crawled_page_urls_from_file
    ][:max_songs_to_crawl]
    
    print_info(f"計畫處理 {len(actual_urls_to_process)} 個新的歌曲頁面 URL。")
    if not actual_urls_to_process and all_potential_song_urls:
         print_info("所有從網站獲取的歌曲似乎都已在先前處理過 (根據紀錄檔)。")

    for i, page_url in enumerate(actual_urls_to_process):
        print_info(f"\n--- 正在處理新歌曲 {i+1}/{len(actual_urls_to_process)} ---")
        song_metadata = extract_song_metadata_selenium(driver, page_url)
        
        title = song_metadata.get("title")
        artist = song_metadata.get("artist_name")

        if not title:
            print_warning(f"未能提取歌曲標題，跳過: {page_url}")
            continue
        
        current_song_identifier = (title, artist if artist else "未知歌手")
        if current_song_identifier in processed_song_identifiers_runtime:
            print_info(f"歌曲 '{title}' (歌手: {artist if artist else '未知'}) 在本次運行中已處理過，跳過。")
            continue
        
        print_info(f"  歌曲頁面: {song_metadata['song_page_url']}")
        print_info(f"  標題: {title}")
        print_info(f"  歌手: {artist if artist else '未知'}")

        m3u8_url_from_meta = song_metadata.get("m3u8_url")
        merged_file_path = None
        song_duration = None
        m3u8_content_for_duration_calc = None

        if not m3u8_url_from_meta:
            print_warning(f"歌曲 '{title}' 因無 m3u8 URL 而無法下載。")
        else:
            print_info(f"  M3U8 URL: {m3u8_url_from_meta}")
            artist_prefix_for_dir = sanitize_filename(artist if artist else "UnknownArtist")
            title_suffix_for_file = sanitize_filename(title)
            artist_specific_download_dir = os.path.join(DOWNLOAD_BASE_DIR, artist_prefix_for_dir)
            output_filename_base = f"{artist_prefix_for_dir}_{title_suffix_for_file}" if artist else title_suffix_for_file

            merged_file_path, m3u8_content_for_duration_calc = download_and_merge_song(
                m3u8_url_from_meta, artist_specific_download_dir, output_filename_base
            )

            if merged_file_path:
                print_success(f"  歌曲已合併到: {merged_file_path}")
                print_info(f"    正在分析歌曲時長...")
                song_duration = get_song_duration_ffmpeg(merged_file_path)
                if song_duration: print_info(f"    使用 ffprobe 獲取時長: {song_duration:.2f} 秒")
                
                if not song_duration and m3u8_content_for_duration_calc:
                    print_info(f"    [提示] ffprobe 分析失敗或未執行。嘗試從 m3u8 估算...")
                    song_duration = get_song_duration_from_m3u8(m3u8_content_for_duration_calc)
                    if song_duration: print_info(f"    從 m3u8 估算時長: {song_duration:.2f} 秒 (不精確)")
                    else: print_warning(f"無法從 m3u8 估算時長。")
                elif not song_duration: print_warning(f"未能獲取歌曲時長。")
            else:
                print_error(f"歌曲 '{title}' 下載或合併失敗。")

        song_db_entry = {
            "song_id": str(uuid.uuid4()), "title": title, "artist_name": artist,
            "duration_seconds": round(song_duration) if song_duration is not None else None,
            "local_file_path": merged_file_path,
            "source_page_url": song_metadata["song_page_url"],
            "m3u8_url_found": m3u8_url_from_meta, "is_public": True
        }
        crawled_songs_data.append(song_db_entry)
        processed_song_identifiers_runtime.add(current_song_identifier) 

        if songs_output_filepath:
            try:
                with open(songs_output_filepath, "a", encoding="utf-8") as f:
                    f.write(str(song_db_entry) + "\n")
            except Exception as e:
                print_error(f"無法將歌曲資訊附加到檔案 {songs_output_filepath}: {e}")
        print_info("--- 處理完畢 ---")
    
    if driver:
        print_info("正在關閉 WebDriver...")
        driver.quit()

    print_info(f"\n歌曲爬取流程完成。本次運行實際處理並記錄了 {len(crawled_songs_data)} 首新的歌曲資訊。")
    if songs_output_filepath and crawled_songs_data:
        print_success(f"詳細歌曲資訊已附加到檔案: {songs_output_filepath}")
    elif songs_output_filepath:
        print_info(f"本次運行未產生新的歌曲資料可寫入 {songs_output_filepath}。")
    return crawled_songs_data

if __name__ == "__main__":
    print_info("StreetVoice HLS 歌曲爬蟲 (Selenium Edge 版本)")
    print_info("="*40)
    # print_warning(f"重要提示：請務必檢查並更新腳本頂部的 CSS Selectors 以符合 StreetVoice 目前的網頁結構！")
    """
    print_info(f"SONG_LINK_SELECTOR_ON_BROWSE_PAGE: '{SONG_LINK_SELECTOR_ON_BROWSE_PAGE}'")
    print_info(f"SONG_TITLE_SELECTOR : '{SONG_TITLE_SELECTOR}'")
    print_info(f"ARTIST_NAME_SELECTOR: '{ARTIST_NAME_SELECTOR}'")
    print_info(f"LOAD_MORE_BUTTON_SELECTOR: '{LOAD_MORE_BUTTON_SELECTOR}'")
    print_info(f"MAIN_PLAY_BUTTON_SELECTOR: '{MAIN_PLAY_BUTTON_SELECTOR}'")
    """
    print_info(f"下載的檔案將會儲存在 '{DOWNLOAD_BASE_DIR}' 目錄下。")
    print_info(f"爬取到的歌曲元資料將會附加到 'crawled_songs_metadata_selenium_edge.txt' 檔案中。")
    print_info("="*40)
    
    # --- 執行範例 (已解除註解) ---
    desired_song_count = 3 # 您希望爬取的歌曲數量 (可調整)
    print_info(f"\n準備開始爬取 {desired_song_count} 首歌...")
    crawled_data = run_song_crawler(max_songs_to_crawl=desired_song_count)
    
    if crawled_data:
        print_info("\n--- 本次爬取到的新歌曲摘要 ---")
        for song_info in crawled_data:
            print_info(f"  標題: {song_info['title']}, 歌手: {song_info.get('artist_name', '未知')}, M3U8: {'有' if song_info.get('m3u8_url_found') else '無'}, 本地: {song_info.get('local_file_path', '無')}")
    
    print_info("\n爬蟲腳本主邏輯執行完畢。")

