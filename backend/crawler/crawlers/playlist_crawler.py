# crawler/playlist_crawler.py
from backend.crawler.crawlers import (
    BaseCrawler,LogLevel, 
    print_info, print_debug, print_warning, print_error, 
    TARGET_SITE_DOMAIN, REQUEST_DELAY_SECONDS, SCROLL_PAUSE_TIME, MAX_SCROLL_ATTEMPTS
    )
from backend import config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# ============================================================
# CSS Selectors for Playlist Page ---
# ============================================================
PLAYLIST_BROWSE_URL = f"{TARGET_SITE_DOMAIN}/music/playlists/all/most_liked/"

# ----------- 歌單 ---------------
PLAYLIST_ITEM_SELECTOR = "div.work-item.border-block" 
PLAYLIST_TITLE_SELECTOR_IN_ITEM = "h3.text-truncate > a" 

# --- 歌單内歌曲 ---
# 「歌曲」的容器 <li> 標籤
PLAYLIST_SONG_ITEM_SELECTOR = "li.work-item.item_box" 
# 歌曲標題的 <a> 標籤
PLAYLIST_SONG_TITLE_SELECTOR_IN_ITEM = "div.work-item-info > h4 > a"
# 作者名字的 <a> 標籤
PLAYLIST_ARTIST_NAME_SELECTOR_IN_ITEM = "div.work-item-info > h5 > a"
# 播放按鈕 <button> 標籤
PLAYLIST_SONG_PLAY_BUTTON_SELECTOR_IN_ITEM = "button.js-playlist[data-id]"
# 歌曲編號  <h4> 標籤
PLAYLIST_TRACK_NUM_SELECTOR_IN_ITEM = "div.work-item-number > h4"
# ============================================================

class PlaylistCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(output_filepath = config.PLAYLIST_CRAWLER_OUTPUT_FILE, 
                         download_base_dir = config.DOWNLOAD_BASE_DIR)
        self.start_url = PLAYLIST_BROWSE_URL
        self.max_playlists_to_crawl = None # 初始化變數

    def crawl(self, max_songs_to_crawl=None, max_playlists=5, crawl_in_order=True, perform_download_and_save=True):
        """
        覆寫 crawl 方法以接收 max_playlists 參數。
        - max_songs_to_crawl (int or None): 要爬取的歌曲總數上限。None 表示爬完指定歌單內的所有歌曲。
        - max_playlists (int or None): 要爬取的歌單數量上限。None 表示爬取所有找到的歌單。
        """
        self.max_playlists_to_crawl = max_playlists
        return super().crawl(
            max_songs_to_crawl=max_songs_to_crawl,
            crawl_in_order=crawl_in_order,
            perform_download_and_save=perform_download_and_save
        )

    def _fetch_all_items(self, max_count):
        # max_count 對應 max_songs_to_crawl，可以為 None
        all_playlist_infos = []
        processed_playlist_urls = set()

        # 如果 max_playlists_to_crawl 為 0 或負數，則不處理任何歌單
        if (self.max_playlists_to_crawl is not None and 
            self.max_playlists_to_crawl <= 0):
            print_info(f"設定的 max_playlists_to_crawl 為 {self.max_playlists_to_crawl}，將不處理任何歌單。")
            return all_playlist_infos
            
        if max_count is not None and max_count <= 0:
            print_info(f"設定的 max_count 為 {max_count}，將不處理任何歌單。")
            return all_playlist_infos

        print_info(f"開始從 {self.start_url} 蒐集歌單資訊...")
        try:
            self.driver.get(self.start_url)
            print_debug(f"已導覽至歌單列表頁面: {self.start_url}")
            time.sleep(REQUEST_DELAY_SECONDS + 2)

            scroll_attempts = 0
            while scroll_attempts < MAX_SCROLL_ATTEMPTS: 
                scroll_attempts += 1
                print_debug(f"嘗試滾動歌單頁面第 {scroll_attempts}/{MAX_SCROLL_ATTEMPTS} 次...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                playlist_items = soup.select(PLAYLIST_ITEM_SELECTOR)
                new_found_this_round = 0

                for item in playlist_items:
                    try:
                        playlist_title_element = item.select_one(PLAYLIST_TITLE_SELECTOR_IN_ITEM)
                        if playlist_title_element:
                            playlist_url = urljoin(TARGET_SITE_DOMAIN, playlist_title_element.get('href', ''))
                            playlist_title = playlist_title_element.text.strip()
                            if playlist_url and playlist_url not in processed_playlist_urls:
                                all_playlist_infos.append({"title": playlist_title, "url": playlist_url})
                                processed_playlist_urls.add(playlist_url)
                                new_found_this_round += 1
                                print_debug(f"蒐集到歌單: {playlist_title}")
                    except Exception as e:
                        print_warning(f"解析歌單列表頁面中的某個歌單項目時出錯: {e}")
                
                if new_found_this_round == 0 and scroll_attempts > 1:
                    print_debug("此次滾動未發現新歌單，可能已達頁面底部。")
                    break

            print_info(f"總共蒐集到 {len(all_playlist_infos)} 個不重複的歌單 URL。")

            # ============ 根據設定選擇要處理的歌單 ============
            playlists_to_process = [] # 先初始化一個空列表
            if self.max_playlists_to_crawl is None:
                # 如果是 None，代表要處理全部
                playlists_to_process = all_playlist_infos
                print_info(f"根據設定 (None)，將處理所有 {len(playlists_to_process)} 個歌單。")
            elif self.max_playlists_to_crawl > 0:
                # 如果大於 0，就取出對應數量
                playlists_to_process = all_playlist_infos[:self.max_playlists_to_crawl]
                print_info(f"根據設定 ({self.max_playlists_to_crawl})，將處理 {len(playlists_to_process)} 個歌單。")
            else:
                # 其他情況 (例如 0 或負數)，playlists_to_process 保持為空列表
                print_info(f"根據設定 ({self.max_playlists_to_crawl})，將處理 0 個歌單。")

            # ============ 開始處理每個歌單 ============
            all_songs_from_playlists = []
            for idx, playlist in enumerate(playlists_to_process):
                if max_count is not None and len(all_songs_from_playlists) >= max_count:
                    print_info(f"已達到目標歌曲總數量 ({max_count})，停止處理更多歌單。")
                    break

                print_info(f"\n--- 進入歌單頁面: {playlist['title']} ({idx+1}/{len(playlists_to_process)}) ---")
                try:
                    self.driver.get(playlist['url'])
                    print_debug(f"已導覽至歌單: {playlist['url']}")
                    time.sleep(REQUEST_DELAY_SECONDS)

                    playlist_scroll_attempts = 0

                    # 獨立紀錄已處理的歌曲
                    processed_song_ids_this_playlist = set()

                    while playlist_scroll_attempts < MAX_SCROLL_ATTEMPTS:
                        playlist_scroll_attempts += 1
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(SCROLL_PAUSE_TIME / 2)

                        playlist_soup = BeautifulSoup(self.driver.page_source, "html.parser")
                        song_items_in_playlist = playlist_soup.select(PLAYLIST_SONG_ITEM_SELECTOR)
                        
                        initial_song_count = len(self.processed_identifiers_runtime)

                        for song_item in song_items_in_playlist:
                            try:
                                play_button = song_item.select_one(PLAYLIST_SONG_PLAY_BUTTON_SELECTOR_IN_ITEM)
                                song_id = play_button.get('data-id') if play_button else None
                                
                                if not song_id or song_id in self.previously_crawled_ids or song_id in processed_song_ids_this_playlist:
                                    continue

                                title_element = song_item.select_one(PLAYLIST_SONG_TITLE_SELECTOR_IN_ITEM)
                                artist_element = song_item.select_one(PLAYLIST_ARTIST_NAME_SELECTOR_IN_ITEM)
                                track_num_element = song_item.select_one(PLAYLIST_TRACK_NUM_SELECTOR_IN_ITEM)
                                title = title_element.text.strip() if title_element else "未知標題"
                                artist = artist_element.text.strip() if artist_element else "未知作者"
                                song_page_url = urljoin(TARGET_SITE_DOMAIN, title_element.get('href', ''))
                                track_num = int(track_num_element.text.strip()) if track_num_element and track_num_element.text.strip().isdigit() else None

                                song_info_data = {
                                    "song_id": song_id, "title": title, "artist_name": artist,
                                    "song_page_url": song_page_url, "playlist_title": playlist['title'],
                                    "playlist_url": playlist['url'], "track_num": track_num
                                }
                                
                                all_songs_from_playlists.append(song_info_data)

                                # 加入獨立紀錄
                                processed_song_ids_this_playlist.add(song_id)

                                print_debug(f"蒐集到歌單 '{playlist['title']}' 內歌曲 ({track_num}. {title} - {artist})")
                                
                                if max_count is not None and len(all_songs_from_playlists) >= max_count:
                                    break
                        
                            except Exception as e:
                                print_warning(f"解析歌單 '{playlist['title']}' 中的歌曲項目時出錯: {e}")
                        
                        if max_count is not None and len(all_songs_from_playlists) >= max_count:
                            break

                        new_songs_this_scroll = len(self.processed_identifiers_runtime) - initial_song_count
                        if new_songs_this_scroll == 0 and playlist_scroll_attempts > 1:
                            print_debug(f"歌單 '{playlist['title']}' 中沒有發現更多新歌曲，可能已達底部。")
                            break

                except TimeoutException:
                    print_error(f"歌單頁面載入超時: {playlist['url']}")
                except Exception as e:
                    print_error(f"進入歌單 '{playlist['title']}' 或爬取其內容時發生錯誤: {e}")

            return all_songs_from_playlists

        except TimeoutException:
            print_error(f"歌單列表頁面載入超時: {self.start_url}")
        except Exception as e:
            print_error(f"抓取歌單資訊時發生錯誤: {e}")
        
        return []