
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for, flash
from .extensions import db, migrate, jwt, cors
from .routes.auth_routes import auth_bp
from .routes.audio_routes import audio_bp
from .routes.main_routes import main_bp
from .celery_config import make_celery
import os
import logging
from datetime import timedelta
from redis import Redis
from flask_cors import CORS

def configure_logging(app):
    # 设置全局日志级别
    logging.basicConfig(level=app.config['LOG_LEVEL'])

    # 获取特定日志器
    httpx_logger = logging.getLogger("httpx")
    httpcore_logger = logging.getLogger("httpcore")
    openai_logger = logging.getLogger("openai")

    # 设置特定日志器的日志级别为 WARNING
    httpx_logger.setLevel(logging.WARNING)
    httpcore_logger.setLevel(logging.WARNING)
    openai_logger.setLevel(logging.WARNING)

def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object('config.Config')

    # 初始化 Flask 扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])  # 允许 'Authorization' 头

    # 设置 JWT 配置项
    app.config['JWT_SECRET_KEY'] = app.config['JWT_SECRET_KEY']  # 从 config.py 获取
    app.config['JWT_TOKEN_LOCATION'] = ['headers']  # 从头部获取 JWT
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = app.config['JWT_ACCESS_TOKEN_EXPIRES']
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = app.config['JWT_REFRESH_TOKEN_EXPIRES']
    app.config['JWT_CSRF_ENABLED'] = False  # 禁用 CSRF 保护

    configure_logging(app)

    # 配置详细日志
    logging.basicConfig(level=app.config['LOG_LEVEL'])
    app.logger.setLevel(app.config['LOG_LEVEL'])

    # 测试 Redis 连接
    try:
        redis_client = Redis.from_url(app.config['CELERY_BROKER_URL'])
        redis_client.ping()
        app.logger.info("Successfully connected to Redis")
    except Exception as e:
        app.logger.error(f"Failed to connect to Redis: {str(e)}")

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(audio_bp, url_prefix='/api/audio')
    app.register_blueprint(main_bp)

    celery = make_celery(app)
    app.celery = celery

    # 创建上传文件夹
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TRANSCRIPTS_FOLDER'], exist_ok=True)

    with app.app_context():
        db.create_all()
        print("Database tables created.")



    # 添加 JWT 错误处理器
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.accept_mimetypes.accept_html:
            flash("登录已过期，请重新登录")
            return redirect(url_for('main.login'))
        else:
            return jsonify({"code": 401, "msg": "登录已过期，请重新登录"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        if request.accept_mimetypes.accept_html:
            flash("无效的访问令牌")
            return redirect(url_for('main.login'))
        else:
            return jsonify({"code": 422, "msg": "无效的访问令牌"}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        if request.accept_mimetypes.accept_html:
            flash("缺少访问令牌，请登录")
            return redirect(url_for('main.login'))
        else:
            return jsonify({"code": 401, "msg": "缺少访问令牌"}), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(jwt_header, jwt_payload):
        if request.accept_mimetypes.accept_html:
            flash("需要新的访问令牌，请重新登录")
            return redirect(url_for('main.login'))
        else:
            return jsonify({"code": 401, "msg": "需要新的访问令牌，请重新登录"}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        if request.accept_mimetypes.accept_html:
            flash("令牌已被撤销，请重新登录")
            return redirect(url_for('main.login'))
        else:
            return jsonify({"code": 401, "msg": "令牌已被撤销，请重新登录"}), 401

    # 添加静态文件路由
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except FileNotFoundError:
            app.logger.error(f"文件未找到: {filename}")
            return jsonify({'code': 404, 'msg': '文件不存在'}), 404

    # 错误处理
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"500 error: {error}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {request.url}")
        return jsonify({'code': 404, 'msg': '请求的资源不存在'}), 404

    return app
