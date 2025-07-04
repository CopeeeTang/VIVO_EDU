# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.extensions import db
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies, verify_jwt_in_request
)
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 输入验证
    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'code': 400, 'msg': '用户名已存在'}), 400

    # 哈希密码
    hashed_password = generate_password_hash(password)

    # 创建新用户
    new_user = User(
        username=username,
        password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'code': 201, 'msg': '注册成功'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

    # 创建JWT
    access_token = create_access_token(identity=user.user_id, expires_delta=timedelta(hours=24))
    refresh_token = create_refresh_token(identity=user.user_id)

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()

    # 创建响应并返回令牌
    response = make_response(jsonify({
        'code': 200,
        'msg': '登录成功',
        'data': {
            'user_id': user.user_id,
            'access_token': access_token,  # 添加 access_token 到响应体
            'refresh_token': refresh_token  # 可选：添加 refresh_token
        }
    }), 200)

    return response

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    受保护的路由示例
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户未找到'}), 404
    return jsonify({'code': 200, 'msg': '访问成功', 'data': {'username': user.username}}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    刷新访问令牌
    """
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({'code': 200, 'msg': 'Token 刷新成功', 'access_token': new_token}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出，仅通知前端清除令牌
    """
    return jsonify({'msg': '登出成功'}), 200

@auth_bp.route('/check_login', methods=['GET'])
def check_login():
    """
    检查用户是否已登录
    """
    try:
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        if current_user:
            return jsonify({'logged_in': True, 'user_id': current_user}), 200
        else:
            return jsonify({'logged_in': False}), 200
    except:
        return jsonify({'msg': '缺少授权头部'}), 401
