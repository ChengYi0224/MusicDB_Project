# crawler/browse_song_crawler.py
from .base_crawler import BaseCrawler, print_info, print_debug, print_warning, print_error, TARGET_SITE_DOMAIN, REQUEST_DELAY_SECONDS, SCROLL_PAUSE_TIME, MAX_SCROLL_ATTEMPTS
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from backend import config

# --- CSS Selectors for Browse Page ---
SONG_LIST_BROWSE_URL = f"{TARGET_SITE_DOMAIN}/music/browse/"
SONG_ITEM_SELECTOR = "ul.list-group-song > li.work-item.item_box"
SONG_TITLE_SELECTOR_IN_ITEM = "div.work-item-info > h4 > a"
ARTIST_NAME_SELECTOR_IN_ITEM = "div.work-item-info > h5 > a"
PLAY_BUTTON_SELECTOR_IN_ITEM = "div.text-right button.js-browse[data-id]"
LOAD_MORE_BUTTON_SELECTOR = "button.btn-loadmore"

class BrowseSongCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(output_filepath = config.BROWSE_CRAWLER_OUTPUT_FILE, 
                         download_base_dir = config.DOWNLOAD_BASE_DIR)
        self.start_url = SONG_LIST_BROWSE_URL

    def crawl(self, max_songs_to_crawl=20, crawl_in_order=True, perform_download_and_save=True):
        """
        覆寫 crawl 方法以確保 max_songs_to_crawl 有一個預設值且不為 None。
        """
        # 如果使用者傳入 None，強制設為預設值 20
        if max_songs_to_crawl is None:
            print_warning(f"BrowseSongCrawler 不允許無限爬取，'max_songs_to_crawl' 已被重設為預設值 20。")
            max_songs_to_crawl = 20
        
        # 呼叫父類別的 crawl 方法
        return super().crawl(
            max_songs_to_crawl=max_songs_to_crawl,
            crawl_in_order=crawl_in_order,
            perform_download_and_save=perform_download_and_save
        )

    def _fetch_all_items(self, max_count):
        # 因為 crawl 方法保證了 max_count 永遠是數字，這裡不需處理 None 的情況
        song_infos = []
        processed_song_ids = set()
        print_info(f"開始從 {self.start_url} 蒐集歌曲資訊...")
        try:
            self.driver.get(self.start_url)
            print_debug(f"已導覽至: {self.start_url}")
            time.sleep(REQUEST_DELAY_SECONDS + 2)

            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, LOAD_MORE_BUTTON_SELECTOR))
                )
                print_debug("偵測到「點我看更多」按鈕，嘗試點擊...")
                self.driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(SCROLL_PAUSE_TIME)
            except TimeoutException:
                print_debug("未找到「點我看更多」按鈕，將直接滾動。")
            except Exception as e:
                print_warning(f"點擊「點我看更多」按鈕時發生錯誤: {e}")

            scroll_attempts = 0
            # max_count 在此處必為數字
            while len(song_infos) < max_count and scroll_attempts < MAX_SCROLL_ATTEMPTS:
                scroll_attempts += 1
                print_debug(f"嘗試滾動第 {scroll_attempts}/{MAX_SCROLL_ATTEMPTS} 次...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                song_items = soup.select(SONG_ITEM_SELECTOR)
                new_found_this_round = 0
                for item in song_items:
                    try:
                        play_button = item.select_one(PLAY_BUTTON_SELECTOR_IN_ITEM)
                        song_id = play_button.get('data-id') if play_button else None
                        if not song_id or song_id in processed_song_ids:
                            continue

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
                if new_found_this_round == 0 and scroll_attempts > 1:
                    print_debug("此次滾動未發現新歌曲，可能已達頁面底部。")
                    break
        except TimeoutException:
            print_error(f"頁面載入超時: {self.start_url}")
        except Exception as e:
            print_error(f"抓取歌曲資訊時發生錯誤: {e}")
        print_info(f"總共蒐集到 {len(song_infos)} 首不重複的歌曲資訊。")
        return song_infos