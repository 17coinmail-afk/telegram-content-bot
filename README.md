# Telegram Content Bot 🤖

Автоматический генератор постов для Telegram-каналов с AI и подпиской.

## Возможности

- ✨ Генерация постов с помощью AI (Groq API / Qwen)
- 🖼 Поиск картинок (Unsplash — бесплатно)
- 📢 Автопостинг в каналы
- ⏰ Отложенная публикация
- 💎 Подписка через ЮKassa
- 🎁 Пробный период 7 дней

## Стек

- Python 3.11 + aiogram 3.x
- FastAPI + uvicorn (webhook)
- PostgreSQL + SQLAlchemy
- Redis
- Render (деплой)

## Быстрый старт

### 1. Локальный запуск

```bash
# Установка
pip install -r requirements.txt

# Переменные окружения
export BOT_TOKEN=your_telegram_bot_token
export GROQ_API_KEY=your_groq_key
export UNSPLASH_ACCESS_KEY=your_unsplash_key
export YOOKASSA_SHOP_ID=your_shop_id
export YOOKASSA_SECRET_KEY=your_secret_key
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/botdb
export REDIS_URL=redis://localhost:6379/0

# Запуск
python -m app.main
```

### 2. Деплой на Render

1. Форк/залей репозиторий на GitHub
2. Создай Web Service на Render из Docker
3. Добавь Environment Variables в панели Render
4. Добавь `render.yaml` как Blueprint
5. Готово!

### 3. Настройка Telegram

1. Создай бота через [@BotFather](https://t.me/BotFather)
2. Получи токен, добавь в `BOT_TOKEN`
3. Для webhook: укажи `WEBHOOK_HOST` (URL от Render)
4. Добавь бота администратором в каналы для автопостинга

### 4. Настройка ЮKassa

1. Зарегистрируйся на [yookassa.ru](https://yookassa.ru)
2. Получи `shopId` и секретный ключ
3. Добавь webhook URL: `https://your-site.com/webhook/yookassa`

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация, пробный период |
| `/admin` | Статистика (только админ) |

## Лимиты

- Пробный период: 7 дней, 3 поста/день
- Подписка: 990 ₽/мес, 50 постов/день

## Структура

```
telegram-content-bot/
├── app/
│   ├── main.py           # FastAPI + webhook
│   ├── bot.py            # Экземпляр бота
│   ├── config.py         # Настройки
│   ├── handlers/         # Обработчики команд
│   ├── services/         # AI, платежи, публикация
│   ├── database/         # Модели и сессии
│   └── keyboards/        # Inline-кнопки
├── Dockerfile
├── render.yaml
└── requirements.txt
```
