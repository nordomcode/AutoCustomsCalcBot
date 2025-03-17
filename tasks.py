from celery import Celery
from celery.schedules import crontab
import xml.etree.ElementTree as ET
import requests
import json
import redis
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

# Настройка Celery
celery_app = Celery('tasks')
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Настройка периодических задач
celery_app.conf.beat_schedule = {
    'update-currency-rates': {
        'task': 'tasks.update_currency_rates',
        'schedule': crontab(hour='*/12'),  # Каждые 12 часов
    },
}

CURRENCY_CODES = json.loads(os.getenv("CURRENCY_CODES", "{}"))

@celery_app.task
def update_currency_rates() -> Dict[str, float]:
    """
    Получает курсы валют из API Центробанка РФ и сохраняет их в Redis.
    
    Returns:
        Dict[str, float]: Словарь с курсами валют {'USD': 00.00, 'EUR': 00.00, 'KRW': 00.00, 'CNY': 00.00}
    """
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    response = requests.get(url)
    response.encoding = 'windows-1251'
    
    root = ET.fromstring(response.text)
    rates = {}
    
    for currency, code in CURRENCY_CODES.items():
        valute = root.find(f".//Valute[@ID='{code}']")
        if valute is not None:
            nominal = float(valute.find('Nominal').text.replace(',', '.'))
            value = float(valute.find('Value').text.replace(',', '.'))
            rates[currency] = value / nominal
    
    # Сохраняем курсы в Redis
    redis_client.set('currency_rates', json.dumps(rates))
    
    return rates

def get_currency_rates() -> Dict[str, float]:
    """
    Получает курсы валют из Redis. Если данных нет, запрашивает их у ЦБ РФ.
    
    Returns:
        Dict[str, float]: Словарь с курсами валют
    """
    rates = redis_client.get('currency_rates')
    if rates:
        return json.loads(rates)
    
    # Если данных в Redis нет, запрашиваем их
    return update_currency_rates() 