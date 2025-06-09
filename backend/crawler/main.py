# CRAWLER/main.py

from .crawlers.base_crawler import print_info, print_success, print_error, print_warning
from .crawlers.browse_song_crawler import BrowseSongCrawler
from .crawlers.playlist_crawler import PlaylistCrawler

from .crawlers.base_crawler import SetLogLevel, LogLevel


if __name__ == "__main__":
    # --- 設定日誌等級 ---
    SetLogLevel(LogLevel.INFO)
    
    # ==================================================================
    #                      測試 Playlist Crawler
    # ==================================================================
    # 說明：取消下面您想執行的場景的註解即可。
    
    print_info("正在初始化 Playlist Crawler...")
    playlist_crawler = PlaylistCrawler()

    # --- 爬取歌單中的所有歌曲 ---
    max_playlists = 5
    max_songs_playlist = None
    print_info(f"--- 爬取 {max_playlists} 個歌單的所有歌曲 ---")
    crawled_data = playlist_crawler.crawl(
        max_playlists=max_playlists, max_songs_to_crawl=max_songs_playlist)


    # ==================================================================
    #                     測試 Browse Song Crawler
    # ==================================================================
    # 說明：若要測試此爬蟲，請先註解掉上面 Playlist Crawler 的執行區塊。
    
    print_info("正在初始化 Browse Song Crawler...")
    browse_crawler = BrowseSongCrawler()
    
    # --- 爬取瀏覽頁面歌曲 ---
    max_songs = 10
    print_info(f"--- 執行場景：爬取瀏覽頁面前 {max_songs} 首歌 ---")
    crawled_data = browse_crawler.crawl(max_songs_to_crawl=max_songs)


    # ==================================================================
    #                          執行結果輸出
    # ==================================================================
    if 'crawled_data' in locals() and crawled_data:
        print_success(f"\n爬取完成，總共獲得 {len(crawled_data)} 首新歌曲。")
        for i, song in enumerate(crawled_data):
            title = song.get('title', 'N/A')
            artist = song.get('artist_name', 'N/A')
            playlist_info = f" (來自歌單: {song.get('playlist_title')})" if 'playlist_title' in song else ""
            print(f"  {i+1}. {title} - {artist}{playlist_info}")
    else:
        print_warning("爬取完成，但未獲得任何新歌曲。")