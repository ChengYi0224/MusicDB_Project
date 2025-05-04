from flask import Blueprint, jsonify, request, render_template
from app.extensions import db

default_bp = Blueprint('default', __name__, url_prefix='/')

@default_bp.route('/', methods=['GET'])
def index():
    query = request.args.get('q', '')
    search_results = []

    if query:
        # TODO: 根據 query 搜尋資料庫，例如：
        # search_results = db.session.query(...).filter(...).all()
        search_results = [f"模擬結果：{query}1", f"模擬結果：{query}2"]

    return render_template('index.html', query=query, results=search_results)