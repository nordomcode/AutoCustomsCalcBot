import redis
import json
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

# Функция для получения курсов валют из Redis
def get_currency_rates():
    rates = redis_client.get('currency_rates')
    if rates:
        return json.loads(rates)
    else:
        raise ValueError("Нет данных о курсах валют в Redis!")