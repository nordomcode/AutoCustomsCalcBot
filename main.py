from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand, Message
from aiogram.filters import Command
from car_mod import Car
from automobile_calc import overall_electro_calc, overall_regular_calc, overall_atv_snowmobile_calc
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import logging
from datetime import datetime
import asyncio
import json
import os
from dotenv import load_dotenv
from redis import Redis
from database import User, Calculation, get_db, Request
from contextlib import contextmanager

load_dotenv()

# Настройка логирования в зависимости от окружения
if os.getenv('ENVIRONMENT') == 'production':
    logging.basicConfig(level=logging.WARNING)  # В продакшене логируем только WARNING и выше
else:
    logging.basicConfig(level=logging.INFO)     # В разработке можно логировать INFO

logger = logging.getLogger(__name__)

# Создание экземпляра бота с токеном
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))

# Инициализация Redis для храpfrнения состояний
# redis = Redis(
#     host=os.getenv("REDIS_HOST", "redis"),
#     port=int(os.getenv("REDIS_PORT", 6379)),
#     db=int(os.getenv("REDIS_DB", 0))
# )
# storage = RedisStorage(redis=redis)

# Создаем роутер
router = Router()


# Список поддерживаемых валют
CURRENCIES = os.getenv("CURRENCIES").split(",")

# Словарь месяцев
MONTHS = json.loads(os.getenv("MONTHS", "{}"))

# Список категорий возраста
AGE_CATEGORIES = {
    "Меньше 3 лет": "<3",
    "От 3 до 5 лет": "3-5",
    "Больше 5 лет": ">5"
}

# Список типов транспортных средств
VEHICLE_TYPES = {
    "🚗 Автомобиль": "car",
    "🏍 Квадроцикл": "quad",
    "🛷 Снегоход": "snowmobile"
}

# Обновляем функции создания клавиатур
def get_currency_keyboard():
    builder = ReplyKeyboardBuilder()
    for curr in CURRENCIES:
        builder.add(KeyboardButton(text=curr))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_months_keyboard():
    builder = ReplyKeyboardBuilder()
    for month in MONTHS.keys():
        builder.add(KeyboardButton(text=month))
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

def get_age_categories_keyboard():
    builder = ReplyKeyboardBuilder()
    for category in AGE_CATEGORIES.keys():
        builder.add(KeyboardButton(text=category))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_vehicle_types_keyboard():
    builder = ReplyKeyboardBuilder()
    for vehicle_type in VEHICLE_TYPES.keys():
        builder.add(KeyboardButton(text=vehicle_type))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Начать расчет"))
    builder.add(KeyboardButton(text="Информация о компании"))
    builder.add(KeyboardButton(text="Оставить заявку"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# валидирующие функции  
def parse_float(value: str):
    try:
        return float(value)
    except ValueError:
        return None

def parse_int(value: str):
    try:
        return int(value)
    except ValueError:
        return None

# Класс для хранения состояний формы
class CarForm(StatesGroup):
    vehicle_type = State()
    engine_type = State()
    currency = State()
    price = State()
    age_category = State()
    volume = State()
    power = State()

# Класс для хранения состояний формы запроса
class RequestForm(StatesGroup):
    name = State()
    phone = State()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # Сохраняем пользователя в базу данных
    try:
        with get_db() as db:
            # Проверяем, существует ли пользователь
            existing_user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
            
            if not existing_user:
                # Создаем нового пользователя
                new_user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username or ""
                )
                db.add(new_user)
                logging.info(f"Добавлен новый пользователь: {message.from_user.id}")
            else:
                logging.info(f"Пользователь уже существует: {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя: {e}")
        logging.exception("Подробная информация об ошибке:")

    await message.answer(f"Привет, {message.from_user.first_name}! Я бот для расчета таможенных платежей при ввозе автомобилей в Россию.")
    await message.answer("Выберите тип транспортного средства:", reply_markup=get_vehicle_types_keyboard())
    await state.set_state(CarForm.vehicle_type)

# Обработчик выбора типа ТС
@router.message(CarForm.vehicle_type)
async def process_vehicle_type(message: Message, state: FSMContext):
    if message.text not in VEHICLE_TYPES:
        await message.answer(
            "Пожалуйста, выберите тип транспортного средства из предложенных вариантов:",
            reply_markup=get_vehicle_types_keyboard()
        )
        return
    
    vehicle_type = VEHICLE_TYPES[message.text]
    await state.update_data(vehicle_type=vehicle_type)
    
    # Для квадроциклов и снегоходов пропускаем выбор типа двигателя
    if vehicle_type in ['quad', 'snowmobile']:
        # Устанавливаем тип двигателя по умолчанию для квадроциклов и снегоходов
        await state.update_data(engine_type='gasoline')
        # Переходим сразу к выбору валюты
        await state.set_state(state=CarForm.currency)
        await message.answer(
            "Выберите валюту стоимости:",
            reply_markup=get_currency_keyboard()
        )
    else:
        # Для автомобилей предлагаем выбрать тип двигателя
        await state.set_state(state=CarForm.engine_type)
        
        # Создаем клавиатуру для выбора типа двигателя
        engine_types = {"Электрический": "electric", "Гибридный": "hybrid", "Бензиновый": "gasoline", "Дизельный": "diesel"}
        builder = ReplyKeyboardBuilder()
        for engine_type in engine_types.keys():
            builder.add(KeyboardButton(text=engine_type))
        builder.adjust(1)  # по одной кнопке в ряд
        
        await message.answer(
            "Выберите тип двигателя:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

# Обработчик выбора типа двигателя
@router.message(CarForm.engine_type)
async def process_engine_type(message: Message, state: FSMContext):
    engine_types = {"Электрический": "electric", "Гибридный": "hybrid", "Бензиновый": "gasoline", "Дизельный": "diesel"}
    if message.text not in engine_types:
        builder = ReplyKeyboardBuilder()
        for engine_type in engine_types.keys():
            builder.add(KeyboardButton(text=engine_type))
        builder.adjust(1)  # по одной кнопке в ряд
        await message.answer(
            "Пожалуйста, выберите тип двигателя из предложенных вариантов:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        return
    
    engine_type = engine_types[message.text]
    await state.update_data(engine_type=engine_type)
    
    # Переходим к выбору валюты
    await state.set_state(state=CarForm.currency)
    await message.answer(
        "Выберите валюту стоимости:",
        reply_markup=get_currency_keyboard()
    )

# Обработчик ввода валюты
@router.message(CarForm.currency)
async def process_currency(message: Message, state: FSMContext):
    if message.text not in CURRENCIES:
        await message.answer(
            "Пожалуйста, выберите валюту из предложенных вариантов:",
            reply_markup=get_currency_keyboard()
        )
        return
    
    await state.update_data(currency=message.text)
    await state.set_state(state=CarForm.price)
    await message.answer(
        "Введите стоимость автомобиля (только число):", 
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик ввода цены
@router.message(CarForm.price)
async def process_price(message: Message, state: FSMContext):
    price = parse_float(message.text)
    if price is None:
        await message.answer("Пожалуйста, введите корректное число.")
        return
        
    if price <= 0:
        await message.answer("Пожалуйста, введите положительное число.")
        return
    
    await state.update_data(price=price)
    
    # Для всех типов ТС запрашиваем возрастную категорию
    await state.set_state(state=CarForm.age_category)
    await message.answer(
        "Выберите возраст транспортного средства:",
        reply_markup=get_age_categories_keyboard()
    )

# Обработчик выбора возрастной категории
@router.message(CarForm.age_category)
async def process_age_category(message: Message, state: FSMContext):
    category_name = message.text
    if category_name not in AGE_CATEGORIES:
        await message.answer(
            "Пожалуйста, выберите возраст из предложенных вариантов:",
            reply_markup=get_age_categories_keyboard()
        )
        return
        
    age_category = AGE_CATEGORIES[category_name]
    await state.update_data(age_category=age_category)
    
    # Получаем данные о типе ТС и двигателя
    data = await state.get_data()
    
    # Для электромобилей и гибридов запрашиваем мощность
    if data.get('engine_type') in ['electric', 'hybrid']:
        await state.update_data(volume=0)  # Устанавливаем объем двигателя в 0
        await state.set_state(state=CarForm.power)
        await message.answer(
            "Введите мощность двигателя в л.с. (только число):",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        # Для остальных типов ТС запрашиваем объем двигателя
        await state.set_state(state=CarForm.volume)
        await message.answer(
            "Введите объем двигателя в см³.\nНапример: 1500",
            reply_markup=ReplyKeyboardRemove()
        )

# Обработчик ввода объема
@router.message(CarForm.volume)
async def process_volume(message: Message, state: FSMContext):
    volume = parse_float(message.text)
    if volume is None:
        await message.answer("Пожалуйста, введите корректное число.")
        return
        
    if volume <= 0:
        await message.answer("Пожалуйста, введите положительное число.\nНапример: 1500")
        return
    
    await state.update_data(volume=volume)
    
    # Получаем данные о типе ТС и двигателя
    data = await state.get_data()
    
    # Устанавливаем мощность в 0 для обычных автомобилей
    data['power'] = 0
    await state.update_data(power=data['power'])
    
    # Выполняем расчет
    await finalize_calculation(message, state, data)

# Обработчик ввода мощности и финальный расчет
@router.message(CarForm.power)
async def process_power(message: Message, state: FSMContext):
    power = parse_float(message.text)
    if power is None:
        await message.answer("Пожалуйста, введите корректное число.")
        return
        
    if power <= 0:
        await message.answer("Пожалуйста, введите положительное число.")
        return
    
    # Получаем все данные и обновляем мощность
    data = await state.get_data()
    data['power'] = power
    await state.update_data(power=power)
    
    # Выполняем расчет
    await finalize_calculation(message, state, data)

async def finalize_calculation(message: Message, state: FSMContext, data: dict):
    try:
        safe_data = data.copy()
        car = Car(
            price=safe_data['price'],
            volume=safe_data['volume'],
            currency=safe_data['currency'],
            power=safe_data['power'],
            age_category=safe_data['age_category'],
            vehicle_type=safe_data['vehicle_type'],
            engine_type=safe_data['engine_type']
        )

        # Определяем тип расчета
        if safe_data['vehicle_type'] in ['quad', 'snowmobile']:
            fees = overall_atv_snowmobile_calc(car)
        elif safe_data['engine_type'] in ['electric', 'hybrid']:
            fees = overall_electro_calc(car)
        else:
            fees = overall_regular_calc(car)

        # Проверяем наличие всех необходимых ключей
        required_keys = ['total', 'customs_duty', 'customs_fee', 'util_fee', 'excise_tax', 'vat']
        missing_keys = [key for key in required_keys if key not in fees]
        if missing_keys:
            logging.error("Отсутствуют обязательные ключи в расчете", extra={
                'user_id': message.from_user.id,
                'missing_keys': missing_keys,
                'calculation_type': safe_data['vehicle_type']
            })
            raise KeyError(f"Отсутствуют обязательные ключи: {missing_keys}")

        # Получаем названия для отображения
        age_category_name = next(name for name, code in AGE_CATEGORIES.items() if code == safe_data['age_category'])
        vehicle_type_name = next(name for name, code in VEHICLE_TYPES.items() if code == safe_data['vehicle_type'])
        
        # Базовая информация
        response = (
            f"Результаты расчета:\n\n"
            f"Тип ТС: {vehicle_type_name}\n"
            f"Стоимость: {car.price} {car.currency}\n"
            f"Возраст: {age_category_name}\n"
        )
        
        # Добавляем информацию о характеристиках двигателя в зависимости от его типа
        if safe_data['engine_type'] in ['electric', 'hybrid']:
            response += f"Мощность двигателя: {car.power} л.с.\n"
        else:
            response += f"Объем двигателя: {car.volume} см³\n"
        
        response += (
            f"Стоимость в рублях: {car.rub_price:.2f} ₽\n\n"
            f"Общая сумма таможенных платежей: {fees['total']:.2f} ₽\n\n"
            f"<b>Детализация:</b>\n"
            f"- Таможенная пошлина: {fees['customs_duty']:.2f} ₽\n"
            f"- Таможенный сбор: {fees['customs_fee']:.2f} ₽\n"
            f"- Утилизационный сбор: {fees['util_fee']:.2f} ₽\n"
        )
        
        # Добавляем информацию об акцизе и НДС только для электромобилей и гибридов
        if safe_data['engine_type'] in ['electric', 'hybrid']:
            response += (
                f"- Акцизный сбор: {fees['excise_tax']:.2f} ₽\n"
                f"- НДС: {fees['vat']:.2f} ₽\n"
            )

        # После завершения расчета показываем сообщение и клавиатуру с кнопками
        await message.answer(
            response + "\n\nИспользуйте команды меню для дальнейших действий.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

        # Сохраняем результат расчета в базу данных
        try:
            with get_db() as db:
                user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
                if not user:
                    user = User(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username
                    )
                    db.add(user)
                
                calculation = Calculation(
                    telegram_id=message.from_user.id,
                    vehicle_type=safe_data['vehicle_type'],
                    engine_type=safe_data['engine_type'],
                    price=safe_data['price'],
                    currency=safe_data['currency'],
                    age_category=safe_data['age_category'],
                    total_fees=fees['total'],
                    customs_duty=fees['customs_duty'],
                    customs_fee=fees['customs_fee'],
                    util_fee=fees['util_fee'],
                    excise_tax=fees['excise_tax'],
                    vat=fees['vat']
                )
                db.add(calculation)
                logging.info("Расчет успешно сохранен", extra={
                    'user_id': message.from_user.id,
                    'calculation_id': calculation.id
                })
        except Exception as e:
            logging.error("Ошибка при сохранении расчета", extra={
                'user_id': message.from_user.id,
                'error': str(e),
                'calculation_data': safe_data
            })
            await message.answer("Произошла ошибка при сохранении результата расчета. Пожалуйста, попробуйте еще раз или обратитесь к администратору.")
            await state.clear()
            return

    except Exception as e:
        logging.error("Ошибка при расчете", extra={
            'user_id': message.from_user.id,
            'error': str(e),
            'calculation_data': safe_data
        })
        await message.answer("Произошла ошибка при расчете. Пожалуйста, попробуйте еще раз или обратитесь к администратору.")
        await state.clear()
        return

# Добавим функцию настройки команд меню
async def set_commands(bot: Bot):
    # Создаем список команд
    commands = [
        BotCommand(
            command="start",
            description="Начать расчет"
        ),
        BotCommand(
            command="info",
            description="Информация о компании"
        ),
        BotCommand(
            command="request",
            description="Оставить заявку"
        )
    ]
    
    # Устанавливаем команды для всех пользователей
    await bot.set_my_commands(commands)
    
    # Логируем успешную установку команд
    logging.info("Команды меню успешно установлены")

# Обработчик команды /info
@router.message(Command(commands=["info"]))
async def cmd_info(message: Message, state: FSMContext):
    # Сбрасываем текущее состояние, если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        if current_state.startswith("CarForm"):
            await message.answer("⚠️ Текущий процесс расчета прерван.")
        elif current_state.startswith("RequestForm"):
            await message.answer("⚠️ Процесс оформления заявки прерван.")
    
    await message.answer(
        "Информация о компании:\n\n"
        "Наша компания специализируется на помощи в растаможке автомобилей, квадроциклов и снегоходов. "
        "Мы предоставляем полный спектр услуг по таможенному оформлению и консультированию.\n\n"
        "Контактная информация:\n"
        "📞 Телефон: +7 (XXX) XXX-XX-XX\n"
        "📧 Email: info@example.com\n"
        "🌐 Сайт: www.example.com\n"
        "📍 Адрес: г. Москва, ул. Примерная, д. 123",
        reply_markup=get_main_menu_keyboard()
    )

# Обработчик команды /request
@router.message(Command(commands=["request"]))
async def cmd_request(message: Message, state: FSMContext):
    # Сбрасываем текущее состояние, если оно есть
    current_state = await state.get_state()
    if current_state is not None and current_state.startswith("CarForm"):
        await state.clear()
        await message.answer("⚠️ Текущий процесс расчета прерван.")
    
    # Устанавливаем состояние для ввода имени
    await state.set_state(RequestForm.name)
    await message.answer(
        "Чтобы оставить заявку на консультацию или услуги по растаможке, "
        "пожалуйста, укажите ваше имя:",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик ввода имени
@router.message(RequestForm.name)
async def process_name(message: Message, state: FSMContext):
    # Сохраняем имя
    await state.update_data(name=message.text)
    
    # Переходим к вводу номера телефона
    await state.set_state(RequestForm.phone)
    await message.answer(
        "Спасибо! Теперь, пожалуйста, укажите ваш номер телефона:",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик ввода номера телефона
@router.message(RequestForm.phone)
async def process_phone(message: Message, state: FSMContext):
    # Проверяем валидность номера телефона
    if not is_valid_phone(message.text):
        await message.answer(
            "Пожалуйста, введите корректный номер телефона. "
            "Номер должен содержать от 7 до 20 символов и может включать цифры, +, -, пробелы и скобки."
        )
        return
    
    # Сохраняем номер телефона
    await state.update_data(phone=message.text)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Сохраняем заявку в базу данных
    try:
        with get_db() as db:
            request = Request(
                telegram_id=message.from_user.id,
                name=data['name'],
                phone=data['phone']
            )
            db.add(request)
            logging.info(f"Сохранена заявка от пользователя {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении заявки: {e}")
        logging.exception("Подробная информация об ошибке:")
    
    # Выводим сообщение об успешной отправке заявки
    await message.answer(
        f"Спасибо за вашу заявку!\n\n"
        f"Мы получили следующие контактные данные:\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n\n"
        f"Наши специалисты свяжутся с вами в ближайшее время для консультации по вопросам растаможки.",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()

# Функция для начала расчета
async def start_calculation(message: Message, state: FSMContext):
    await state.set_state(state=CarForm.vehicle_type)
    await message.answer(
        "Выберите тип транспортного средства:",
        reply_markup=get_vehicle_types_keyboard()
    )

# Функция для валидации номера телефона
def is_valid_phone(phone: str) -> bool:
    import re
    # Простая проверка: должен содержать только цифры, +, -, пробелы и скобки
    # и быть длиной от 7 до 20 символов
    pattern = r'^[0-9\+\-\(\)\s]{7,20}$'
    return bool(re.match(pattern, phone))

# Обработчик текстового сообщения "Информация о компании"
@router.message(lambda message: message.text == "Информация о компании")
async def text_info(message: Message, state: FSMContext):
    # Перенаправляем на обработчик команды /info
    await cmd_info(message, state)

# Обработчик текстового сообщения "Оставить заявку"
@router.message(lambda message: message.text == "Оставить заявку")
async def text_request(message: Message, state: FSMContext):
    # Перенаправляем на обработчик команды /request
    await cmd_request(message, state)

# Обработчик текстового сообщения "Начать расчет"
@router.message(lambda message: message.text == "Начать расчет")
async def text_start_calculation(message: Message, state: FSMContext):
    # Сбрасываем текущее состояние, если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        if current_state.startswith("CarForm"):
            await message.answer("⚠️ Текущий процесс расчета прерван. Начинаем заново.")
        elif current_state.startswith("RequestForm"):
            await message.answer("⚠️ Процесс оформления заявки прерван. Начинаем расчет.")
    
    # Начинаем расчет
    await start_calculation(message, state)

# Изменим функцию main
async def main():
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Включаем роутер
    dp.include_router(router)
    
    # Установка команд меню
    await set_commands(bot)
    
    # Запуск бота в режиме polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
