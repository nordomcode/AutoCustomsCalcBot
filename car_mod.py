from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from cbr import get_currency_rates

import os
import dotenv

dotenv.load_dotenv()
CURRENCIES = os.getenv("CURRENCIES").split(",")

# Удаляем глобальную переменную X_RATE, которая вызывает запрос при импорте
# X_RATE = get_cbr_currency_rates()  # Получаем актуальные курсы валют

class CarBase(BaseModel):
    price: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    currency: str
    power: float = Field(default=1, ge=0)
    age_category: Literal['<3', '3-5', '>5']
    vehicle_type: Literal['car', 'quad', 'snowmobile']
    engine_type: Literal['electric', 'hybrid', 'gasoline', 'diesel']

class Car:
    def __init__(self, price: float, volume: float, currency: str, power: float = 1, age_category: str = '>5', vehicle_type: str = 'car', engine_type: str = 'regular'):
        # Валидация данных через Pydantic
        car_data = CarBase(
            price=price,
            volume=volume,
            currency=currency,
            power=power,
            age_category=age_category,
            vehicle_type=vehicle_type,
            engine_type=engine_type
        )
        
        self.price = car_data.price
        self.volume = car_data.volume
        self.currency = car_data.currency
        self.power = car_data.power
        self.age_category = car_data.age_category
        self.vehicle_type = car_data.vehicle_type
        self.engine_type = car_data.engine_type
        self.rub_price = self.calculate_price_in_rubles()
        
    def calculate_price_in_rubles(self) -> float:
        # Получаем курсы валют только при необходимости, а не при импорте
        rates = get_currency_rates()
        return self.price * rates[self.currency]
