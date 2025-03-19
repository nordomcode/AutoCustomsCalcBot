from car_mod import Car
from tasks import get_currency_rates

# Базовые функции расчета
def utilisation_fee_calc(car: Car) -> float:
    if car.age_category == "<3":
        return 20_000.00 * 0.17
    else:
        return 20_000.00 * 0.26

def customs_fee_regular_calc(car: Car) -> float:
    # Структура данных для расчета таможенного сбора в зависимости от стоимости
    price_brackets = [
        (200_000.00, 1_067.00),
        (450_000.00, 2_134.00),
        (1_200_000.00, 4_269.00),
        (2_700_000.00, 11_746.00),
        (4_200_000.00, 16_524.00),
        (5_500_000.00, 21_344.00),
        (7_000_000.00, 27_540.00),
        (float('inf'), 30_000.00)
    ]
    
    # Находим подходящий диапазон для расчета таможенного сбора
    for price_limit, fee in price_brackets:
        if car.rub_price < price_limit:
            return fee
    
    # На всякий случай, хотя до этой строки код не должен дойти
    return 30_000.00

def customs_fee_electro_calc(price: float) -> float:
    # Структура данных для расчета таможенного сбора в зависимости от стоимости
    price_brackets = [
        (200_000.00, 775.00),
        (450_000.00, 1_550.00),
        (1_200_000.00, 3_100.00),
        (2_700_000.00, 8_530.00),
        (4_200_000.00, 12_000.00),
        (5_500_000.00, 15_550.00),
        (7_000_000.00, 20_000.00),
        (8_000_000.00, 23_000.00),
        (9_000_000.00, 25_000.00),
        (10_000_000.00, 27_000.00),
        (float('inf'), 30_000.00)
    ]
    
    # Находим подходящий диапазон для расчета таможенного сбора
    for price_limit, fee in price_brackets:
        if price < price_limit:
            return fee
    
    return 30_000.00  # На всякий случай

def customs_duty_regular_calc(car: Car) -> float:
    rates = get_currency_rates()  # Получаем курсы здесь
    # Структура данных для расчета пошлины в зависимости от возраста
    age_brackets = {
        "<3": {
            # Границы цены в EUR, (процент от стоимости, коэффициент для объема)
            "price_brackets": [
                (8_500 * rates['EUR'], 0.54, 2.5),
                (16_700 * rates['EUR'], 0.48, 3.5),
                (42_300 * rates['EUR'], 0.48, 5.5),
                (84_500 * rates['EUR'], 0.48, 7.5),
                (169_000 * rates['EUR'], 0.48, 15),
                (float('inf'), 0.48, 20)
            ]
        },
        "3-5": {
            # Границы объема, коэффициент для объема
            "volume_brackets": [
                (1_000, 1.5),
                (1_500, 1.7),
                (1_800, 2.5),
                (2_300, 2.7),
                (3_000, 3.0),
                (float('inf'), 3.6)
            ]
        },
        ">5": {
            # Границы объема, коэффициент для объема
            "volume_brackets": [
                (1_000, 3.0),
                (1_500, 3.2),
                (1_800, 3.5),
                (2_300, 4.8),
                (3_000, 5.0),
                (float('inf'), 5.7)
            ]
        }
    }
    
    # Расчет для автомобилей младше 3 лет
    if car.age_category == "<3":
        for price_limit, percent, volume_coef in age_brackets["<3"]["price_brackets"]:
            if car.rub_price < price_limit:
                return max(car.rub_price * percent, volume_coef * rates['EUR'] * car.volume)
    
    # Расчет для автомобилей от 3 до 5 лет или старше 5 лет
    else:
        for volume_limit, coef in age_brackets[car.age_category]["volume_brackets"]:
            if car.volume < volume_limit:
                return coef * rates['EUR'] * car.volume
    
    

def customs_duty_electro_calc(car: Car) -> float:
    # Таможенная пошлина для электромобилей
    return car.rub_price * 0.15

def excise_tax_electro_calc(car: Car) -> float:
    # Определяем границы диапазонов и соответствующие коэффициенты для акциза
    power_brackets = [
        (0, 0),     # граница, коэффициент
        (90, 0),    # до 90 л.с. включительно - 0
        (150, 61),  # от 91 до 150 л.с. - 61 * power
        (200, 583), # от 151 до 200 л.с. - 583 * power
        (300, 955),   # до 201 до 300 л.с. - 955 * power
        (400, 1628),  # от 301 до 400 л.с. - 1628 * power
        (500, 1685), # от 401 до 500 л.с. - 1685 * power
        (float('inf'), 1740)  # свыше 500 л.с. - 1740 * power
    ]
    
    # Находим подходящий диапазон для расчета акциза
    for i, (limit, coef) in enumerate(power_brackets[1:], 1):
        if car.power <= limit:
            return coef * car.power
    
    
def utilisation_fee_atv_snowmobile_calc(car: Car) -> float:
    # Базовая ставка для мотовездеходов, снегоболотоходов и снегоходов
    base_rate = 172500.0
    
    # Логика расчета акцизного сбора:
    # 1. Если категория <3 и объем < 300, то базовая ставка * 0.4
    # 2. Если категория <3 и объем >= 300, то базовая ставка * 0.7
    # 3. Если категория не <3 и объем < 300, то базовая ставка * 0.7
    # 4. Если категория не <3 и объем >= 300, то базовая ставка * 1.3
    
    if car.age_category == '<3':  # Новые (до 3 лет)
        if car.volume < 300:  # Объем двигателя менее 300 см³
            return base_rate * 0.4
        else:  # Объем двигателя не менее 300 см³
            return base_rate * 0.7
    else:  # Старые (3 года и более)
        if car.volume < 300:  # Объем двигателя менее 300 см³
            return base_rate * 0.7
        else:  # Объем двигателя не менее 300 см³
            return base_rate * 1.3

def vax_electro_calc(car: Car, customs_duty: float, excise_tax: float) -> float:
    # Рассчитываем НДС (20%)
    return (car.rub_price + customs_duty + excise_tax) * 0.20

# Общие функции расчета
def overall_electro_calc(car: Car) -> dict:
    # Рассчитываем таможенную пошлину
    customs_duty = customs_duty_electro_calc(car)
    
    # Рассчитываем акцизный сбор
    excise_tax = excise_tax_electro_calc(car)
    
    # Рассчитываем таможенный сбор
    customs_fee = customs_fee_regular_calc(car)
    
    # Рассчитываем утилизационный сбор
    util_fee = utilisation_fee_calc(car)
    
    # Рассчитываем НДС
    vat = vax_electro_calc(car, customs_duty, excise_tax)
    
    # Рассчитываем общую сумму
    total = customs_duty + excise_tax + util_fee + customs_fee + vat
    
    # Возвращаем словарь с детализацией платежей
    return {
        "total": total,
        "customs_duty": customs_duty,
        "excise_tax": excise_tax,
        "util_fee": util_fee,
        "customs_fee": customs_fee,
        "vat": vat
    }


def overall_atv_snowmobile_calc(car: Car) -> dict:
    # Рассчитываем таможенную пошлину
    customs_duty = car.rub_price * 0.05
    
    # Рассчитываем таможенный сбор
    customs_fee = 250.00
    
    # Рассчитываем утилизационный сбор (используем тот же, что и для обычных авто)
    util_fee = utilisation_fee_atv_snowmobile_calc(car)
    
    
    # Для квадроциклов и снегоходов нет НДС в нашей модели
    vat = car.rub_price * 0.20
    
    # Рассчитываем общую сумму
    total = customs_duty + customs_fee + util_fee + vat
    
    # Возвращаем словарь с детализацией платежей
    return {
        "total": total, # общая сумма платежей          
        "customs_duty": customs_duty, # таможенная пошлина
        "util_fee": util_fee, # утилизационный сбор
        "customs_fee": customs_fee, # таможенный сбор
        "vat": vat # НДС
    }

def overall_regular_calc(car: Car) -> dict:
    # Рассчитываем таможенную пошлину
    customs_duty = customs_duty_regular_calc(car)
    
    # Рассчитываем таможенный сбор
    customs_fee = customs_fee_regular_calc(car)
    
    # Рассчитываем утилизационный сбор
    util_fee = utilisation_fee_calc(car)
    
    # Для обычных автомобилей нет акцизного сбора и НДС в нашей модели
    excise_tax = 0
    vat = 0
    
    # Рассчитываем общую сумму
    total = customs_duty + customs_fee + util_fee
    
    # Возвращаем словарь с детализацией платежей
    return {
        "total": total,
        "customs_duty": customs_duty,
        "excise_tax": excise_tax,
        "util_fee": util_fee,
        "customs_fee": customs_fee,
        "vat": vat
    }


