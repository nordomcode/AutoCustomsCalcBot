from tasks import update_currency_rates

if __name__ == "__main__":
    print("Получение курсов валют...")
    rates = update_currency_rates()
    print(f"Получены курсы: {rates}") 