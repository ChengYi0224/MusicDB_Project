# init of app
from flask import Flask
from .routes import all_blueprints

def create_app():
    # 初始化app
    app = Flask(__name__)

    # 註冊資料庫
    # from .models import db
    # db.init_app(app)

    # 註冊藍圖
    for bp in all_blueprints:
        app.register_blueprint(bp)
    
    return app