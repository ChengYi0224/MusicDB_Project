# backend/app/routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

# 定義 auth 藍圖
auth_bp = Blueprint('auth', __name__, url_prefix='/auth') # 設定 URL 前綴為 /auth

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET  → 回傳 register.html (註冊表單)
    POST → 處理註冊邏輯
    """
    # 如果使用者已經登入，可以考慮直接導向首頁
    if 'user_id' in session:
        flash('您已登入，無法再次註冊。', 'info')
        return redirect(url_for('default.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            flash('所有欄位都必須填寫。', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('兩次輸入的密碼不一致。', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('此使用者名稱已被使用。', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('註冊成功，請登入！', 'success')
        return redirect(url_for('user.user_login')) # 註冊成功後導向登入頁面，注意這裡改為 user.user_login

    return render_template('register.html')