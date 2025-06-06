# backend/app/routes/user.py
from flask import Blueprint, request, render_template, session, redirect, url_for, flash, session
from app.extensions import db
from app.models import User
from werkzeug.security import check_password_hash

# 定義 user 藍圖
user_bp = Blueprint('user', __name__, url_prefix='/user') # 設定 URL 前綴為 /user

@user_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    """
    GET  → 回傳 login.html (登入表單)
    POST → 驗證 username, password；成功就設定 session['user_id']，然後跳回首頁；失敗則顯示錯誤
    """
    # 如果使用者已經登入，可以考慮直接導向首頁或使用者個人頁面
    if 'user_id' in session:
        flash('您已登入。', 'info')
        return redirect(url_for('default.index')) # 假設首頁是 default.index

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error_msg = '請輸入帳號與密碼'
            return render_template('login.html', error=error_msg)

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            error_msg = '帳號或密碼錯誤'
            return render_template('login.html', error=error_msg)

        session['user_id'] = user.user_id
        flash('登入成功！', 'success')
        return redirect(url_for('default.index')) # 登入成功後導向首頁

    # 如果是 GET 請求，顯示登入表單
    return render_template('login.html')

@user_bp.route('/logout')
def user_logout():
    """
    登出功能：清除 session 中的 user_id
    """
    session.pop('user_id', None) # 移除 session 中的 user_id
    flash('您已登出。', 'info')
    return redirect(url_for('default.index')) # 登出後導向首頁或登入頁面

# 你可以添加其他使用者相關的路由，例如個人資料頁面
@user_bp.route('/profile')
def user_profile():
    if 'user_id' not in session:
        flash('請先登入。', 'warning')
        return redirect(url_for('user.user_login')) # 導向登入頁面
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user:
        return render_template('profile.html', user=user) # 需要創建 profile.html
    else:
        flash('找不到您的使用者資訊。', 'danger')
        return redirect(url_for('user.user_login'))