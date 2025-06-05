# init of app
from flask import Flask
from .routes import all_blueprints
from .routes.user import user_bp
from config import Config
import os

def create_app():

    # 初始化app
    app = Flask(
        __name__,
        static_folder='../../frontend/static',
        template_folder="../../frontend/templates",
        )

    # 載入設定檔
    app.config.from_object(Config)
    
    # 註冊資料庫
    from .extensions import db
    db.init_app(app)

    # 註冊藍圖
    for bp in all_blueprints:
        app.register_blueprint(bp)
    
    return app