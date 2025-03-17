import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
from typing import Dict
import time

import os
import dotenv
import json

dotenv.load_dotenv()

CURRENCY_CODES = json.loads(os.getenv("CURRENCY_CODES", "{}"))

# Кэш для хранения курсов валют
_currency_cache = {
    "rates": {},
    "last_update": None
}

def get_cbr_currency_rates() -> Dict[str, float]:
    """
    Получает курсы валют из API Центробанка РФ с кэшированием.
    Обновляет курсы только раз в день или при первом запуске.
    
    Returns:
        Dict[str, float]: Словарь с курсами валют {'USD': 00.00, 'EUR': 00.00, 'KRW': 00.00, 'CNY': 00.00}
    """
    global _currency_cache
    
    # Проверяем, нужно ли обновить кэш
    current_time = datetime.now()
    if (_currency_cache["last_update"] is None or 
        current_time - _currency_cache["last_update"] > timedelta(hours=24) or
        not _currency_cache["rates"]):
        
        try:
            # Получаем новые курсы
            url = "https://www.cbr.ru/scripts/XML_daily.asp"
            response = requests.get(url, timeout=5)  # Добавляем таймаут
            response.encoding = 'windows-1251'  # Устанавливаем кодировку для корректного чтения кириллицы
            
            root = ET.fromstring(response.text)
            
            rates = {}
            
            for currency, code in CURRENCY_CODES.items():
                # Находим элемент валюты по ID
                valute = root.find(f".//Valute[@ID='{code}']")
                if valute is not None:
                    # Получаем значение и номинал
                    nominal = float(valute.find('Nominal').text.replace(',', '.'))
                    value = float(valute.find('Value').text.replace(',', '.'))
                    rates[currency] = value / nominal
            
            # Обновляем кэш
            _currency_cache["rates"] = rates
            _currency_cache["last_update"] = current_time
            
            print(f"Курсы валют обновлены: {current_time}")
        except Exception as e:
            print(f"Ошибка при получении курсов валют: {e}")
            # Если есть кэшированные данные, используем их
            if _currency_cache["rates"]:
                print("Используем кэшированные курсы валют")
            else:
                # Если кэша нет, устанавливаем значения по умолчанию
                _currency_cache["rates"] = {
                    "USD": 90.0,
                    "EUR": 100.0,
                    "KRW": 0.07,
                    "CNY": 12.5
                }
                print("Используем значения курсов валют по умолчанию")
    
    return _currency_cache["rates"]

# Для тестирования
if __name__ == "__main__":
    try:
        # Первый запрос - получение из API
        rates1 = get_cbr_currency_rates()
        print("Текущие курсы валют (первый запрос):")
        for currency, rate in rates1.items():
            print(f"{currency}: {rate:.7f} RUB")
        
        # Второй запрос - должен использовать кэш
        time.sleep(1)  # Пауза для демонстрации
        rates2 = get_cbr_currency_rates()
        print("\nТекущие курсы валют (второй запрос, должен использовать кэш):")
        for currency, rate in rates2.items():
            print(f"{currency}: {rate:.7f} RUB")
            
    except Exception as e:
        print(f"Ошибка при получении курсов валют: {e}")