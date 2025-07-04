# 导入所需的Flask扩展和Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 初始化数据库对象
db = SQLAlchemy()
# 初始化数据库迁移对象
migrate = Migrate()
# 初始化JWT管理对象
jwt = JWTManager()
# 初始化CORS对象，用于处理跨域请求
cors = CORS()

