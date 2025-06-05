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
import random # 用於隨機爬取
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By

# Edge WebDriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
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

# --- 定義日誌細節等級 ---
class LogLevel(Enum):
    ERROR = 0
    WARNING = 1
    SUCCESS = 2
    INFO = 3
    DEBUG = 4

CURRENT_LOG_LEVEL = LogLevel.INFO # 預設為 INFO 級別 (您可以調整這裡)

# --- Print 函數 ---
def print_error(message):
    if CURRENT_LOG_LEVEL.value >= LogLevel.ERROR.value:
        print(f"{AnsiColors.RED}{AnsiColors.BOLD}[錯誤] {message}{AnsiColors.ENDC}")

def print_warning(message):
    if CURRENT_LOG_LEVEL.value >= LogLevel.WARNING.value:
        print(f"{AnsiColors.RED}{AnsiColors.BOLD}[警告]{AnsiColors.ENDC} {message}")

def print_success(message):
    if CURRENT_LOG_LEVEL.value >= LogLevel.SUCCESS.value:
        print(f"{AnsiColors.YELLOW}[成功]{AnsiColors.ENDC} {message}")

def print_info(message):
    if CURRENT_LOG_LEVEL.value >= LogLevel.INFO.value:
        print(f"{AnsiColors.BLUE}{message}{AnsiColors.ENDC}")

def print_debug(message):
    if CURRENT_LOG_LEVEL.value >= LogLevel.DEBUG.value:
        print(f"{AnsiColors.GREEN}[除錯]{AnsiColors.ENDC} {message}")

# --- 網址 ---
TARGET_SITE_DOMAIN = "https://streetvoice.com"
SONG_LIST_BROWSE_URL = f"{TARGET_SITE_DOMAIN}/music/browse/"

# --- CSS Selectors ---
SONG_ITEM_SELECTOR = "ul.list-group-song > li.work-item.item_box"
SONG_TITLE_SELECTOR_IN_ITEM = "div.work-item-info > h4 > a"
ARTIST_NAME_SELECTOR_IN_ITEM = "div.work-item-info > h5 > a"
PLAY_BUTTON_SELECTOR_IN_ITEM = "div.text-right button.js-browse[data-id]"
LOAD_MORE_BUTTON_SELECTOR = "button.btn-loadmore"


REQUEST_DELAY_SECONDS = 2
SCROLL_PAUSE_TIME = 3
MAX_SCROLL_ATTEMPTS = 15
DOWNLOAD_BASE_DIR = "backend/crawler/downloads"
SONGS_OUTPUT_FILEPATH = "backend/crawler/crawled_songs.txt"
MSEDGEDRIVER_PATH = None
M3U8_WAIT_TIME_SECONDS = 3
PLAY_CLICK_WAIT_TIME_SECONDS = 3


# --- WebDriver 設定 ---
def setup_driver():
    edge_options = EdgeOptions()
    # edge_options.add_argument("--headless")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62")

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

# --- 輔助函數 ---
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

# --- 從 Browse 頁面獲取歌曲資訊 ---
def fetch_and_extract_song_infos(driver, max_count=100):
    """
    導覽至 browse 頁面，滾動直到獲取足夠數量的歌曲資訊。
    返回一個包含每首歌 metadata 的字典列表。
    """
    song_infos = []
    processed_song_ids = set() # 用 song_id 來判斷是否重複
    print_info(f"開始從 {SONG_LIST_BROWSE_URL} 蒐集歌曲資訊...")
    try:
        driver.get(SONG_LIST_BROWSE_URL)
        print_debug(f"已導覽至: {SONG_LIST_BROWSE_URL}")
        time.sleep(REQUEST_DELAY_SECONDS + 2)

        # 嘗試點擊一次 "LOAD MORE"
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, LOAD_MORE_BUTTON_SELECTOR))
            )
            print_debug("偵測到「點我看更多」按鈕，嘗試點擊...")
            driver.execute_script("arguments[0].click();", load_more_button)
            time.sleep(SCROLL_PAUSE_TIME)
        except TimeoutException:
            print_debug("未找到「點我看更多」按鈕，將直接滾動。")
        except Exception as e:
            print_warning(f"點擊「點我看更多」按鈕時發生錯誤: {e}")

        scroll_attempts = 0
        while len(song_infos) < max_count and scroll_attempts < MAX_SCROLL_ATTEMPTS:
            scroll_attempts += 1
            print_debug(f"嘗試滾動第 {scroll_attempts}/{MAX_SCROLL_ATTEMPTS} 次...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            song_items = soup.select(SONG_ITEM_SELECTOR)
            
            new_found_this_round = 0
            for item in song_items:
                try:
                    play_button = item.select_one(PLAY_BUTTON_SELECTOR_IN_ITEM)
                    song_id = play_button.get('data-id') if play_button else None

                    if not song_id or song_id in processed_song_ids:
                        continue # 如果沒有 song_id 或已處理過，則跳過

                    title_element = item.select_one(SONG_TITLE_SELECTOR_IN_ITEM)
                    artist_element = item.select_one(ARTIST_NAME_SELECTOR_IN_ITEM)
                    
                    title = title_element.text.strip() if title_element else "未知標題"
                    artist = artist_element.text.strip() if artist_element else "未知作者"
                    song_page_url = urljoin(TARGET_SITE_DOMAIN, title_element.get('href', ''))
                    
                    song_info_data = {
                        "song_id": song_id,
                        "title": title,
                        "artist_name": artist,
                        "song_page_url": song_page_url
                    }
                    song_infos.append(song_info_data)
                    processed_song_ids.add(song_id)
                    new_found_this_round += 1
                    print_debug(f"蒐集到資訊 ({len(song_infos)}): {title} - {artist} (ID: {song_id})")
                    
                    if len(song_infos) >= max_count:
                        break
                except Exception as e:
                    print_warning(f"解析某個歌曲項目時出錯: {e}")

            if len(song_infos) >= max_count:
                print_info("已達到目標歌曲數量。")
                break
            
            if new_found_this_round == 0:
                 print_debug("此次滾動未發現新歌曲，可能已達頁面底部。")
                 break

    except TimeoutException:
        print_error(f"頁面載入超時: {SONG_LIST_BROWSE_URL}")
    except Exception as e:
        print_error(f"抓取歌曲資訊時發生錯誤: {e}")
    
    print_info(f"總共蒐集到 {len(song_infos)} 首不重複的歌曲資訊。")
    return song_infos


# --- 模擬 API 請求 ---
def get_m3u8_url_from_api(driver, song_info):
    """
    使用從 browse 頁面獲取的 song_id，直接請求 API 以獲取 m3u8 URL。
    """
    song_id = song_info.get("song_id")
    song_page_url_for_referer = song_info.get("song_page_url", SONG_LIST_BROWSE_URL)

    if not song_id:
        print_error("歌曲資訊中缺少 'song_id'。")
        return None

    print_debug(f"準備為 '{song_info['title']}' (ID: {song_id}) 模擬 API 請求...")

    # 獲取 csrf-token
    csrf_token_value = None
    try:
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'csrf-token': # <-- 修改處
                csrf_token_value = cookie['value']
                print_debug("成功從 cookie 獲取到 'csrf-token'。")
                break
    except Exception as e_cookie:
        print_warning(f"獲取 csrf-token 時發生異常: {e_cookie}")
    
    if not csrf_token_value:
        print_warning("未能獲取到 'csrf-token'，將嘗試無 token 請求。")

    # 獲取 Selenium session 的 cookies 以便 requests 使用
    session_requests_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    api_url = f"https://streetvoice.com/api/v5/song/{song_id}/hls/file/"
    headers = {
        'User-Agent': driver.execute_script("return navigator.userAgent;"),
        'Referer': song_page_url_for_referer, # 使用歌曲頁面URL作為Referer
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': TARGET_SITE_DOMAIN
    }
    if csrf_token_value:
        headers['X-Csrf-Token'] = csrf_token_value # <-- 修改處 (通常 Header 名稱會是這樣)

    print_debug(f"正在向 API ({api_url}) 發送 POST 請求...")
    try:
        response = requests.post(api_url, headers=headers, cookies=session_requests_cookies, timeout=15)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data and "file" in response_data and response_data["file"]:
            m3u8_url = response_data["file"]
            print_success(f"成功從 API 獲取 m3u8 URL: {m3u8_url}")
            return m3u8_url
        else:
            print_warning(f"API 回應成功，但 JSON 中無 'file' 內容。回應: {response_data}")
            return None
    except requests.exceptions.HTTPError as e_http:
        print_error(f"模擬 API 請求時 HTTP 錯誤: {e_http} - 回應: {e_http.response.text[:200] if e_http.response else ''}")
    except requests.exceptions.RequestException as e_req:
        print_error(f"模擬 API 請求時網路錯誤: {e_req}")
    except json.JSONDecodeError:
        print_error(f"無法解析 API 的 JSON 回應。內容: {response.text[:200]}")
    return None

# --- 下載並合併歌曲 ---
def download_and_merge_song(m3u8_url, output_dir, output_filename_base):
    """
    下載並合併 HLS 串流，並確保臨時檔案在結束後被清理。
    (更新版：使用 try...finally 結構確保清理)
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_filename_base = sanitize_filename(output_filename_base)
    merged_ts_path = os.path.join(output_dir, f"{safe_filename_base}.ts")

    if os.path.exists(merged_ts_path):
        print_debug(f"檔案已存在，跳過下載: {merged_ts_path}")
        return merged_ts_path, None # 已存在，直接返回路徑

    # 為每個歌曲的 ts 片段建立獨立的臨時下載目錄
    temp_ts_dir = os.path.join(output_dir, f"{safe_filename_base}_temp_ts_parts")
    os.makedirs(temp_ts_dir, exist_ok=True)
    
    try:
        print_info(f"準備從 {m3u8_url} 下載歌曲...")
        m3u8_content = None
        try:
            m3u8_resp = requests.get(m3u8_url, timeout=15)
            m3u8_resp.raise_for_status()
            m3u8_content = m3u8_resp.text
        except requests.exceptions.RequestException as e:
            print_error(f"下載 m3u8 列表失敗 ({m3u8_url}): {e}")
            return None, None # m3u8 下載失敗，無法繼續

        lines = m3u8_content.splitlines()
        ts_urls = [urljoin(m3u8_url, line.strip()) for line in lines if line.strip() and not line.startswith("#")]
        
        if not ts_urls:
            print_error(f"在 m3u8 內容中找不到 .ts 片段: {m3u8_url}")
            return None, m3u8_content

        ts_files_to_merge = []
        print_debug(f"開始下載 '{safe_filename_base}' 的 {len(ts_urls)} 個 .ts 片段到 '{temp_ts_dir}'...")
        for idx, ts_url in enumerate(tqdm(ts_urls, desc=f"TS-{safe_filename_base[:20]}", unit="片段", ncols=100, leave=False)):
            ts_temp_filename = os.path.join(temp_ts_dir, f"part_{idx:04d}.ts")
            try:
                ts_resp = requests.get(ts_url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                ts_resp.raise_for_status()
                with open(ts_temp_filename, "wb") as fp:
                    shutil.copyfileobj(ts_resp.raw, fp)
                ts_files_to_merge.append(ts_temp_filename)
            except Exception as e:
                print_warning(f"下載片段 {idx+1} ({ts_url}) 失敗: {e}")
                # 即使有部分失敗，也繼續嘗試合併已下載的部分

        if not ts_files_to_merge:
            print_error(f"'{safe_filename_base}' 沒有任何 .ts 片段成功下載。")
            return None, m3u8_content

        print_info(f"正在合併 '{safe_filename_base}' 的 {len(ts_files_to_merge)} 個 .ts 片段 -> {merged_ts_path}")
        with open(merged_ts_path, "wb") as wfp:
            for ts_file_path in ts_files_to_merge:
                if os.path.exists(ts_file_path):
                    with open(ts_file_path, "rb") as rfp:
                        shutil.copyfileobj(rfp, wfp)
        
        # 如果程式成功走到這裡，返回合併後的路徑
        return merged_ts_path, m3u8_content

    except Exception as e:
        # 捕捉在 try 區塊中發生的任何其他錯誤
        print_error(f"處理 '{safe_filename_base}' 過程中發生未預期錯誤: {e}")
        return None, None # 返回 None 表示失敗

    finally:
        # --- 清理程序 ---
        # 這段程式碼無論 try 區塊是成功結束還是發生錯誤跳出，都一定會執行
        if os.path.exists(temp_ts_dir):
            print_debug(f"執行清理程序，刪除臨時目錄: {temp_ts_dir}")
            try:
                shutil.rmtree(temp_ts_dir)
                print_debug(f"臨時目錄已成功刪除。")
            except Exception as e_rm:
                print_warning(f"清理臨時目錄時發生錯誤: {e_rm}")


# --- 主執行函數 ---
def run_song_crawler(max_songs_to_crawl=10, 
                     songs_output_filepath=SONGS_OUTPUT_FILEPATH, 
                     crawl_in_order=True):
    """
    執行爬蟲的主函數。
    
    :param max_songs_to_crawl: 希望爬取的新歌曲數量。
    :param songs_output_filepath: 儲存歌曲 metadata 的檔案路徑。
    :param crawl_in_order: True 為循序爬取, False 為隨機順序爬取。
    """
    
    driver = setup_driver()
    if not driver:
        print_error("WebDriver 初始化失敗，爬蟲無法執行。")
        return []

    crawled_songs_data = []
    processed_song_identifiers_runtime = set()
    previously_crawled_song_ids_from_file = set()

    # 讀取已處理紀錄
    if os.path.exists(songs_output_filepath):
        try:
            with open(songs_output_filepath, "r", encoding="utf-8") as f_read:
                for line in f_read:
                    try:
                        song_data_dict = eval(line.strip())
                        if isinstance(song_data_dict, dict) and "song_id" in song_data_dict:
                            previously_crawled_song_ids_from_file.add(song_data_dict["song_id"])
                    except Exception: pass
            if previously_crawled_song_ids_from_file:
                print_info(f"從 {songs_output_filepath} 讀取到 {len(previously_crawled_song_ids_from_file)} 個已處理過的歌曲 ID。")
        except Exception as e:
            print_warning(f"讀取紀錄檔 {songs_output_filepath} 失敗: {e}")
    
    # 獲取歌曲資訊列表
    all_potential_songs = []
    try:
        # 計算最大抓取數量 = 用戶指定的數量 + 已處理過的歌曲數量 + 20 (額外緩衝)
        fetch_max_count = max_songs_to_crawl + len(previously_crawled_song_ids_from_file) + 20
        all_potential_songs = fetch_and_extract_song_infos(driver, max_count=fetch_max_count)
    except Exception as e:
        print_error(f"在 fetch_and_extract_song_infos 階段發生嚴重錯誤: {e}")
    
    if not all_potential_songs:
        print_info("未能獲取任何歌曲資訊，流程結束。")
        if driver: driver.quit()
        return []

    # 過濾掉已經處理過的歌曲
    actual_songs_to_process = [
        song for song in all_potential_songs if song.get("song_id") not in previously_crawled_song_ids_from_file
    ]
    
    # 根據選項決定爬取順序
    if not crawl_in_order:
        print_info("選項設定為「隨機順序」，正在打亂歌曲處理順序...")
        random.shuffle(actual_songs_to_process)

    # 截取到目標數量
    actual_songs_to_process = actual_songs_to_process[:max_songs_to_crawl]
    
    print_info(f"計畫處理 {len(actual_songs_to_process)} 首新的歌曲。")
    if not actual_songs_to_process and all_potential_songs:
         print_info("所有從網站獲取的歌曲似乎都已在先前處理過。")

    for i, song_info_item in enumerate(actual_songs_to_process):
        print_info(f"\n--- 正在處理新歌曲 {i+1}/{len(actual_songs_to_process)} ---")
        
        title = song_info_item.get("title")
        artist = song_info_item.get("artist_name")
        
        current_song_identifier = (title, artist)
        if current_song_identifier in processed_song_identifiers_runtime:
            print_info(f"歌曲 '{title}' (歌手: {artist}) 在本次運行中已處理過，跳過。")
            continue
        
        print_info(f"標題: {title}")
        print_info(f"歌手: {artist}")
        print_debug(f"Song ID: {song_info_item.get('song_id')}")
        print_debug(f"歌曲頁面: {song_info_item.get('song_page_url')}")

        m3u8_url_result = get_m3u8_url_from_api(driver, song_info_item)
        merged_file_path = None
        song_duration = None
        # m3u8_content_for_duration_calc = None # 此變數在 download_and_merge_song 內部處理

        if not m3u8_url_result:
            print_warning(f"歌曲 '{title}' 因無法獲取 m3u8 URL 而跳過下載。")
        else:
            artist_prefix_for_dir = sanitize_filename(artist)
            title_suffix_for_file = sanitize_filename(title)
            artist_specific_download_dir = os.path.join(DOWNLOAD_BASE_DIR, artist_prefix_for_dir)
            output_filename_base = f"{artist_prefix_for_dir}_{title_suffix_for_file}"

            merged_file_path, _ = download_and_merge_song( # m3u8_content 不再需要在外部使用
                m3u8_url_result, artist_specific_download_dir, output_filename_base
            )

            if merged_file_path:
                print_success(f"歌曲已合併到: {merged_file_path}")
                song_duration = get_song_duration_ffmpeg(merged_file_path)
                if song_duration: print_debug(f"ffprobe 分析時長: {song_duration:.2f} 秒")
                else: print_warning("無法獲取歌曲時長 (ffprobe)。")
            else:
                print_error(f"歌曲 '{title}' 下載或合併失敗。")

        song_db_entry = {
            "uuid": str(uuid.uuid4()), 
            "song_id": song_info_item.get("song_id"), "title": title, "artist_name": artist,
            "duration_seconds": round(song_duration) if song_duration is not None else None,
            "local_file_path": merged_file_path,
            "source_page_url": song_info_item.get("song_page_url"),
            "m3u8_url_found": m3u8_url_result, "is_public": True
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
    
    return crawled_songs_data

if __name__ == "__main__":
    # 設定您希望的日誌等級
    # CURRENT_LOG_LEVEL = LogLevel.DEBUG # 最詳細
    CURRENT_LOG_LEVEL = LogLevel.INFO # 只看資訊、成功、警告、錯誤
    # CURRENT_LOG_LEVEL = LogLevel.SUCCESS # 只看成功、警告、錯誤
    # CURRENT_LOG_LEVEL = LogLevel.WARNING # 只看警告、錯誤
    # CURRENT_LOG_LEVEL = LogLevel.ERROR # 只看錯誤

    print_info("StreetVoice HLS 歌曲爬蟲 v2.1")
    print_info("="*50)
    print_info(f"下載的檔案將儲存在 \"{DOWNLOAD_BASE_DIR}\" 目錄下。")
    print_info(f"爬取到的歌曲元資料將會附加到 \"{SONGS_OUTPUT_FILEPATH}\" 檔案中。")
    print_info(f"目前日誌等級設定為: {CURRENT_LOG_LEVEL.name}")
    print_info("="*50)
    
    # --- 執行 ---
    desired_song_count = 2 # 您希望爬取並下載的歌曲數量

    # True: 按照網頁順序從上到下爬取
    # False: 隨機順序爬取
    crawl_sequentially = True 

    print_info(f"\n準備開始爬取 {desired_song_count} 首歌 (順序爬取: {crawl_sequentially})...")
    crawled_data = run_song_crawler(
        max_songs_to_crawl=desired_song_count,
        crawl_in_order=crawl_sequentially
    )
    
    if crawled_data:
        print_info("\n--- 本次爬取到的新歌曲摘要 ---")
        for song_summary in crawled_data:
            print_info(f"標題: {song_summary['title']}, 歌手: {song_summary.get('artist_name', '未知')}, M3U8: {'有' if song_summary.get('m3u8_url_found') else '無'}, 本地: {song_summary.get('local_file_path', '無')}")
    
    print_info("\n爬蟲腳本主邏輯執行完畢。")
