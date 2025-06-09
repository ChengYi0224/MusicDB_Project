# init of app
from flask import Flask
from .routes import all_blueprints
from .routes.user import user_bp
from config import Config
import os
from .context_processors import inject_user_to_templates

def create_app():

    # 初始化app
    app = Flask(
        __name__,
        static_folder='../../frontend/static',
        template_folder="../../frontend/templates",
        )

    # 載入設定檔
    app.config.from_object(Config)

    # 設定context processors
    # 這個函式會將使用者資訊注入到所有模板中
    app.context_processor(inject_user_to_templates)
    
    # 註冊資料庫
    from .extensions import db
    db.init_app(app)
    from .extensions import migrate
    migrate.init_app(app, db)

    # 註冊藍圖
    for bp in all_blueprints:
        app.register_blueprint(bp)
    
    return app