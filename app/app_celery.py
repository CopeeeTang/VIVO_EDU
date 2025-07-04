from app import create_app
from app.celery_config import make_celery

# 创建 Flask 应用
app = create_app()

# 创建 Celery 应用
celery = make_celery(app)

if __name__ == '__main__':
    celery.start()