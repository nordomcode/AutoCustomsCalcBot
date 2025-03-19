from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Создаем приложение
celery_app = Celery(__name__)

# Настраиваем конфигурацию
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    imports=['tasks'],
    beat_schedule={
        'update-currency-rates': {
            'task': 'tasks.update_currency_rates',
            'schedule': crontab(minute=0, hour='*/12'),  # каждые 12 часов
        },
    }
)

# Автоматически находить и регистрировать задачи из других модулей
celery_app.autodiscover_tasks(['tasks']) 