# crawlers/base_crawler.py
import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm import tqdm
import time
import uuid
import subprocess
import json
import shutil
import random
from enum import Enum
from backend import config

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 日誌與顏色代碼 (保持不變) ---
class AnsiColors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class LogLevel(Enum):
    ERROR = 0
    WARNING = 1
    SUCCESS = 2
    INFO = 3
    DEBUG = 4

CURRENT_LOG_LEVEL = LogLevel.INFO

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

# --- 常數 ---
TARGET_SITE_DOMAIN = "https://streetvoice.com"
# DOWNLOAD_BASE_DIR = "backend/crawler/downloads"
# SONGS_OUTPUT_FILEPATH = "backend/crawler/crawled_songs.txt"
MSEDGEDRIVER_PATH = None
REQUEST_DELAY_SECONDS = 2
SCROLL_PAUSE_TIME = 3
MAX_SCROLL_ATTEMPTS = 15
M3U8_WAIT_TIME_SECONDS = 3
PLAY_CLICK_WAIT_TIME_SECONDS = 3

# --- 輔助函數 ---

def SetLogLevel(level):
    """
    專門用來設定全域日誌等級的函式。
    """
    global CURRENT_LOG_LEVEL
    if isinstance(level, LogLevel):
        CURRENT_LOG_LEVEL = level
    else:
        # 如果傳入的不是 LogLevel 型別，就印出錯誤
        print_error(f"嘗試設定無效的日誌等級: {level}")

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

def sanitize_filename(name):
    if not name: name = "unknown"
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
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

def get_m3u8_url_from_api(driver, song_info):
    song_id = song_info.get("song_id")
    song_page_url_for_referer = song_info.get("song_page_url", TARGET_SITE_DOMAIN)
    if not song_id:
        print_error("歌曲資訊中缺少 'song_id'。")
        return None
    print_debug(f"準備為 '{song_info.get('title', '未知')}' (ID: {song_id}) 模擬 API 請求...")
    csrf_token_value = None
    try:
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'csrf-token':
                csrf_token_value = cookie['value']
                print_debug("成功從 cookie 獲取到 'csrf-token'。")
                break
    except Exception as e_cookie:
        print_warning(f"獲取 csrf-token 時發生異常: {e_cookie}")
    
    session_requests_cookies = {c['name']: c['value'] for c in cookies}
    api_url = f"https://streetvoice.com/api/v5/song/{song_id}/hls/file/"
    headers = {
        'User-Agent': driver.execute_script("return navigator.userAgent;"),
        'Referer': song_page_url_for_referer,
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': TARGET_SITE_DOMAIN
    }
    if csrf_token_value:
        headers['X-Csrf-Token'] = csrf_token_value
    
    print_debug(f"正在向 API ({api_url}) 發送 POST 請求...")
    try:
        response = requests.post(api_url, headers=headers, cookies=session_requests_cookies, timeout=15)
        response.raise_for_status()
        response_data = response.json()
        if response_data and "file" in response_data and response_data["file"]:
            m3u8_url = response_data["file"]
            print_success(f"成功從 API 獲取 m3u8 URL")
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

def download_and_merge_song(m3u8_url, output_dir, output_filename_base):
    os.makedirs(output_dir, exist_ok=True)
    safe_filename_base = sanitize_filename(output_filename_base)
    merged_ts_path = os.path.join(output_dir, f"{safe_filename_base}.ts")
    if os.path.exists(merged_ts_path):
        print_debug(f"檔案已存在，跳過下載: {merged_ts_path}")
        return merged_ts_path, None
    
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
            return None, None
        
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

        if not ts_files_to_merge:
            print_error(f"'{safe_filename_base}' 沒有任何 .ts 片段成功下載。")
            return None, m3u8_content
        
        print_info(f"正在合併 '{safe_filename_base}' 的 {len(ts_files_to_merge)} 個 .ts 片段 -> {merged_ts_path}")
        with open(merged_ts_path, "wb") as wfp:
            for ts_file_path in ts_files_to_merge:
                if os.path.exists(ts_file_path):
                    with open(ts_file_path, "rb") as rfp:
                        shutil.copyfileobj(rfp, wfp)
        return merged_ts_path, m3u8_content
    except Exception as e:
        print_error(f"處理 '{safe_filename_base}' 過程中發生未預期錯誤: {e}")
        return None, None
    finally:
        if os.path.exists(temp_ts_dir):
            print_debug(f"執行清理程序，刪除臨時目錄: {temp_ts_dir}")
            try:
                shutil.rmtree(temp_ts_dir)
                print_debug(f"臨時目錄已成功刪除。")
            except Exception as e_rm:
                print_warning(f"清理臨時目錄時發生錯誤: {e_rm}")


# ============================================================
#                     Base Crawler Class
# ============================================================
class BaseCrawler:
    def __init__(self, 
                 output_filepath=None, 
                 download_base_dir=config.DOWNLOAD_BASE_DIR):
        self.driver = None
        self.output_filepath = output_filepath
        self.download_base_dir = download_base_dir
        self.processed_identifiers_runtime = set()
        self.previously_crawled_ids = set()

    def _initialize_driver(self):
        if not self.driver:
            self.driver = setup_driver()
            if not self.driver:
                print_error("WebDriver 初始化失敗。")
                return False
        return True

    def _load_previously_crawled_data(self):
        if os.path.exists(self.output_filepath):
            try:
                with open(self.output_filepath, "r", encoding="utf-8") as f_read:
                    for line in f_read:
                        try:
                            song_data_dict = eval(line.strip())
                            if isinstance(song_data_dict, dict) and "song_id" in song_data_dict:
                                self.previously_crawled_ids.add(song_data_dict["song_id"])
                        except Exception as e:
                            print_warning(f"解析紀錄檔中的某一行時失敗: {line.strip()} - 錯誤: {e}")
                if self.previously_crawled_ids:
                    print_info(f"從 {self.output_filepath} 讀取到 {len(self.previously_crawled_ids)} 個已處理過的項目 ID。")
            except Exception as e:
                print_warning(f"讀取紀錄檔 {self.output_filepath} 失敗: {e}")

    def _save_crawled_data(self, data_entry):
        if self.output_filepath:
            try:
                with open(self.output_filepath, "a", encoding="utf-8") as f:
                    entry_to_write = data_entry.copy()
                    entry_to_write["uuid"] = str(uuid.uuid4())
                    entry_to_write["is_public"] = True
                    f.write(str(entry_to_write) + "\n")
            except Exception as e:
                print_error(f"無法將資料附加到檔案 {self.output_filepath}: {e}")

    def _process_single_song_download(self, song_info_item):
        title = song_info_item.get("title")
        artist = song_info_item.get("artist_name")
        print_info(f"正在處理: {title} - {artist}")
        m3u8_url_result = get_m3u8_url_from_api(self.driver, song_info_item)
        merged_file_path = None
        song_duration = None
        if m3u8_url_result:
            artist_prefix_for_dir = sanitize_filename(artist)
            title_suffix_for_file = sanitize_filename(title)
            artist_specific_download_dir = os.path.join(self.download_base_dir, artist_prefix_for_dir)
            output_filename_base = f"{artist_prefix_for_dir}_{title_suffix_for_file}"
            merged_file_path, _ = download_and_merge_song(
                m3u8_url_result, artist_specific_download_dir, output_filename_base
            )
            if merged_file_path:
                print_success(f"歌曲已合併到: {merged_file_path}")
                song_duration = get_song_duration_ffmpeg(merged_file_path)
            else:
                print_error(f"歌曲 '{title}' 下載或合併失敗。")
        else:
            print_warning(f"歌曲 '{title}' 因無法獲取 m3u8 URL 而跳過下載。")
        song_db_entry = {
            "song_id": song_info_item.get("song_id"), 
            "title": title, 
            "artist_name": artist,
            "duration_seconds": round(song_duration) if song_duration is not None else None,
            "local_file_path": merged_file_path,
            "source_page_url": song_info_item.get("song_page_url"),
            "m3u8_url_found": m3u8_url_result,
        }
        return song_db_entry

    def crawl(self, max_songs_to_crawl=10, crawl_in_order=True, perform_download_and_save=True):
        if not self._initialize_driver():
            return []

        self._load_previously_crawled_data()
        crawled_data_this_run = []

        fetch_limit = None
        if max_songs_to_crawl is not None:
            # 為了過濾掉已爬取項目，預先多抓取一些
            fetch_limit = max_songs_to_crawl + len(self.previously_crawled_ids) + 20
        
        all_potential_items = self._fetch_all_items(fetch_limit)
        
        if not all_potential_items:
            print_info("未能獲取任何項目資訊，流程結束。")
            if self.driver: self.driver.quit()
            return []

        actual_items_to_process = [
            item for item in all_potential_items if item.get("song_id") not in self.previously_crawled_ids
        ]
        if not crawl_in_order:
            print_info("選項設定為「隨機順序」，正在打亂項目處理順序...")
            random.shuffle(actual_items_to_process)
        
        if max_songs_to_crawl is not None:
            actual_items_to_process = actual_items_to_process[:max_songs_to_crawl]
        
        print_info(f"計畫處理 {len(actual_items_to_process)} 個新的項目。")

        for i, item_info in enumerate(actual_items_to_process):
            print_info(f"\n--- 正在處理新項目 {i+1}/{len(actual_items_to_process)} ---")
            current_identifier = item_info.get("song_id")
            if current_identifier in self.processed_identifiers_runtime:
                print_info(f"項目 '{current_identifier}' 在本次運行中已處理過，跳過。")
                continue
            
            processed_entry = self._process_single_song_download(item_info)
            
            if processed_entry:
                crawled_data_this_run.append(processed_entry)
                self.processed_identifiers_runtime.add(current_identifier)
                if perform_download_and_save:
                    self._save_crawled_data(processed_entry)
            
            print_info("--- 處理完畢 ---")
        
        if self.driver:
            print_info("正在關閉 WebDriver...")
            self.driver.quit()
            self.driver = None

        print_info(f"\n爬取流程完成。本次運行實際處理並記錄了 {len(crawled_data_this_run)} 個新的項目資訊。")
        if perform_download_and_save and crawled_data_this_run:
            print_success(f"詳細資訊已附加到檔案: {self.output_filepath}")
        
        return crawled_data_this_run

    def _fetch_all_items(self, max_count):
        raise NotImplementedError("子類必須實現 _fetch_all_items 方法。")