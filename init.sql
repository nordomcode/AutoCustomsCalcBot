CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calculations (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES users(telegram_id),
    vehicle_type VARCHAR(50),
    engine_type VARCHAR(50),
    price DECIMAL(15,2),
    currency VARCHAR(10),
    age_category VARCHAR(50),
    calculation_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индекс для быстрого поиска по telegram_id
CREATE INDEX idx_calculations_telegram_id ON calculations(telegram_id); 