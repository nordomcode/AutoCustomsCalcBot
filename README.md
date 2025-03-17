# AutomobileCalcBot
## Описание
Телеграм бот для рассчета таможенных платежей при ввозе автомобилей, квадроциклов и снегоходов.

## Основные функции
- По команде "Начать рассчет"(/start) начинает запрашивать у пользователя данные для расчета таможенных платежей. Вконце выводит детализированный итоговый рассчет
- По команде "Информация о компании"(/info) контактную информацию
- По команде "Оставить заявку"(/request) запрашивает у пользователя Имя и Номер телефона для связи.

## Шаги
1. Запрашивает у пользователя тип транспортного средства: автомобиль, снегоход, квадроцикл (снегоход и квадроцикл обрабатываются одинаково)
2. Для автомобиля запрашивает тип двигателя: электрический, гибрид, бензиновый, дизельный (электрический/гибрид и бензиновый/дизельный обрабатываются одинаково)
3. Запрашивает валюту покупки
4. Запрашивает стоимость техники в ранее указанной валюте
5. Для электрических и гибридов запрашивает мощность в л.с. | Для бензиновых и дизельных, снегоходов и квадрациклов запрашивает объем куб. см.
6. Запрашивает категорию возраста техники:
   - Моложе 3 лет
   - От 3х до 5 лет
   - Стараше 5 лет
7. Выдает рассчет

## Валюта
Валюта запрашивается раз в сутки на сайте Центробанка РФ: Eur(евро), USD(доллар США), CNY(юани), KRW(корейские воны).
Данные кешируются в Redis

## PostgreSQL база
Хранит данные о пользователях, оставивших заявку или просто взаимодействовавших с ботом




