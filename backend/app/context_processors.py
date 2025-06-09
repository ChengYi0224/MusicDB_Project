# \BACKEND\APP\context_processors.py

from flask import session
from .models import User

def inject_user_to_templates():
    """
    從 session 取得 user_id，並透過它查詢最新的使用者物件，
    最後將其注入到所有模板中。
    """
    user_info = None
    if 'user_id' in session:
        # 每次都從資料庫獲取最新的使用者資料
        user_info = User.query.get(session['user_id'])
    
    return dict(user=user_info)