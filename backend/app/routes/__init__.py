# init of app.routes

# from .albums import album_bp
# from .artists import artist_bp
from .user import user_bp
from .default import default_bp
from .auth import auth_bp
from .playlist import playlist_bp

# 將所有藍圖放在一個tuple中方便批量註冊
all_blueprints = (user_bp, default_bp, auth_bp, playlist_bp)  # , album_bp, artist_bp