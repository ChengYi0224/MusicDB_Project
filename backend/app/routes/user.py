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
    
# 新增：編輯個人資料路由
@user_bp.route("/profile/edit", methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('請先登入。', 'warning')
        return redirect(url_for('user.user_login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id) # 獲取當前登入的使用者物件

    if not user:
        flash('找不到您的使用者資訊。', 'danger')
        return redirect(url_for('user.user_login'))

    if request.method == 'POST':
        # 獲取表單資料
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        new_description = request.form.get('description', '')

        # 簡單的驗證
        if not new_username:
            flash('使用者名稱不能為空。', 'danger')
            return render_template("edit_profile.html", user=user)
        if not new_email:
            flash('信箱不能為空。', 'danger')
            return render_template("edit_profile.html", user=user)
        
        # 檢查使用者名稱和郵箱是否已被其他使用者使用 (排除當前使用者本身)
        if new_username != user.username:
            existing_user_by_username = User.query.filter_by(username=new_username).first()
            if existing_user_by_username and existing_user_by_username.user_id != user.user_id:
                flash('該使用者名稱已被使用，請選擇其他名稱。', 'danger')
                return render_template("edit_profile.html", user=user)
        
        if new_email != user.email:
            existing_user_by_email = User.query.filter_by(email=new_email).first()
            if existing_user_by_email and existing_user_by_email.user_id != user.user_id:
                flash('該信箱已被註冊，請選擇其他信箱。', 'danger')
                return render_template("edit_profile.html", user=user)

        # 更新使用者物件的屬性
        user.username = new_username
        user.email = new_email
        user.description = new_description

        try:
            db.session.commit() # 提交資料庫變更
            flash('個人資料更新成功！', 'success')
            return redirect(url_for('user.user_profile'))
        except Exception as e:
            db.session.rollback() # 出錯時回滾
            flash(f'更新失敗：{e}。', 'danger')
            # 可以在這裡添加更詳細的錯誤日誌
            print(f"Database update error: {e}")

    # 如果是 GET 請求，顯示編輯表單頁面
    return render_template("edit_profile.html", user=user)
