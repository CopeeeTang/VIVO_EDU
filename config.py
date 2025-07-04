import os
from datetime import timedelta
import logging

class Config:
    # 应用程序的密钥，用于加密会话数据等
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    
    # 读取数据库配置环境变量
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
    
    # 验证必需的数据库配置
    if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
        missing_vars = []
        if not MYSQL_HOST: missing_vars.append('MYSQL_HOST')
        if not MYSQL_USER: missing_vars.append('MYSQL_USER')
        if not MYSQL_PASSWORD: missing_vars.append('MYSQL_PASSWORD')
        if not MYSQL_DATABASE: missing_vars.append('MYSQL_DATABASE')
        
        error_msg = f"缺少必需的数据库环境变量: {', '.join(missing_vars)}"
        print(f"❌ 配置错误: {error_msg}")
        print("请检查 local.env 文件是否包含所有必需的数据库配置")
        raise ValueError(error_msg)
    
    # 阿里云RDS MySQL配置
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/"
        f"{MYSQL_DATABASE}"
    )
    
    # 输出调试信息（隐藏敏感信息）
    print(f"✅ 数据库配置已加载: {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 15,
        'connect_args': {
            'connect_timeout': 10,
            'read_timeout': 20,
        }
    }

    # Redis配置 - 支持本地开发和Docker环境
    # 本地运行时使用 localhost，Docker中使用 redis 服务名
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_DB = os.getenv('REDIS_DB', '0')
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    # Celery配置
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_INCLUDE = ['app.utils.task_async']
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # 上传文件的存储路径
    UPLOAD_FOLDER = 'uploads/'
    
    # 转录文件的存储路径
    TRANSCRIPTS_FOLDER = 'static/transcripts/'
    
    # 允许上传的音频文件扩展名
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a','webm'}

    # 最大上传文件大小 40MB
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  
    
    # PDF文件的存储路径
    PDF_STORAGE_PATH = './checkpoints/knowledge_all.pkl'

    # 日志配置
    LOG_LEVEL = logging.INFO  # 设置全局日志级别

    #图片保存路径
    PATH_IMG='./static/images'

    PATH_FONT='SimHei.ttf'

