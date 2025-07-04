from celery import Celery
import logging

def make_celery(app):
    # 创建 Celery 实例
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)



    # 定义自定义任务基类，确保任务可以访问 Flask 的上下文
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    CELERY_LOGGER = logging.getLogger('celery')
    CELERY_LOGGER.setLevel(app.config['LOG_LEVEL'])


    return celery
