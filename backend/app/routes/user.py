from flask import Blueprint, jsonify, request
from models import db, User  # 假設 User 是 SQLAlchemy 定義的模型
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')


# 取得所有使用者
@user_bp.route('/', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


# 取得單一使用者
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


# 新增使用者
@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.json
    try:
        new_user = User(
            username=data['username'],
            description=data.get('description', ''),
            email=data['email'],
            password_hash=data['password_hash'],
            role=data['role'],
            profile_image=data.get('profile_image', ''),
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created', 'user_id': new_user.user_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# 更新使用者
@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    user.username = data.get('username', user.username)
    user.description = data.get('description', user.description)
    user.email = data.get('email', user.email)
    user.password_hash = data.get('password_hash', user.password_hash)
    user.role = data.get('role', user.role)
    user.profile_image = data.get('profile_image', user.profile_image)

    db.session.commit()
    return jsonify({'message': 'User updated'}), 200


# 刪除使用者
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200

