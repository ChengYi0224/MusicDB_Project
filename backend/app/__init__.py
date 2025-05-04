# init of app
from flask import Flask
from .routes import all_blueprints
from .routes.user import user_bp
from config import Config

def create_app():
    # 初始化app
    app = Flask(__name__)

    # 載入設定檔
    app.config.from_object(Config)  
    # 或者使用 ProductionConfig 根據環境
    # app.config.from_object(ProductionConfig)
    
    # 註冊資料庫
    from .extensions import db
    db.init_app(app)

    # 註冊藍圖
    for bp in all_blueprints:
        app.register_blueprint(bp)
    
    return app