# crawlers/__init__.py

# 從 base_crawler.py 中，匯出我們希望在頂層就能用到的東西
from .base_crawler import (
    # 核心類別
    BaseCrawler,
    # 設定工具
    LogLevel,
    SetLogLevel,
    # 所有日誌函式
    print_error,
    print_warning,
    print_success,
    print_info,
    print_debug,
    # 常用常數
    TARGET_SITE_DOMAIN,
    REQUEST_DELAY_SECONDS,
    SCROLL_PAUSE_TIME,
    MAX_SCROLL_ATTEMPTS,
    M3U8_WAIT_TIME_SECONDS,
    PLAY_CLICK_WAIT_TIME_SECONDS
)

# 從 browse_song_crawler.py 中，匯出爬蟲類別
from .browse_song_crawler import BrowseSongCrawler

# 從 playlist_crawler.py 中，匯出爬蟲類別
from .playlist_crawler import PlaylistCrawler

# (可選) 為了讓 `from crawlers import *` 的行為更明確，可以定義 __all__
__all__ = [
    'BaseCrawler',
    'BrowseSongCrawler',
    'PlaylistCrawler',
    'LogLevel',
    'SetLogLevel',
    'print_error',
    'print_warning',
    'print_success',
    'print_info',
    'print_debug',
    'TARGET_SITE_DOMAIN'
]