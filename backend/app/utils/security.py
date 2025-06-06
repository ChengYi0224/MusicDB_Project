# backend/app/utils/security.py
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """將傳入的密碼字串進行雜湊處理。"""
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """驗證密碼雜湊與傳入的密碼是否相符。"""
    return check_password_hash(password_hash, password)

# 產生預設密碼 "Password" 的雜湊值，供 User 模型使用
DEFAULT_PASSWORD_HASH = hash_password("Password")
