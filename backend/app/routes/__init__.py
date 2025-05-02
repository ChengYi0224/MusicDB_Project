# init of app.routes

# from .albums import album_bp
# from .artists import artist_bp
from .users import user_bp

# 將所有藍圖放在一個tuple中方便批量註冊
all_blueprints = (user_bp)