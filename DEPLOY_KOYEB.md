# Деплой на Koyeb (бесплатно, без карты)

## Что используем
- **Koyeb** — хостинг бота (Docker, free tier, не спит)
- **Render** — PostgreSQL + Redis (уже созданы, free tier)

## Пошаговая инструкция

### 1. Получи connection strings из Render
Зайди в Dashboard Render:
- PostgreSQL: https://dashboard.render.com/d/dpg-d7jehc67r5hc73b5okig-a
- Redis: https://dashboard.render.com/d/red-d7jehcd7vvec738take0

Скопируй **External Connection String** для каждого.

### 2. Зарегистрируйся на Koyeb
- https://app.koyeb.com
- Можно войти через GitHub

### 3. Создай приложение
1. **Create App**
2. **GitHub** → выбери репозиторий `telegram-content-bot`
3. **Branch:** `main`
4. Koyeb сам найдёт `Dockerfile` — оставь всё по умолчанию
5. **Port:** `8000` (HTTP)
6. **Plan:** Eco (бесплатно)

### 4. Добавь Environment Variables

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | твой токен от @BotFather |
| `GROQ_API_KEY` | твой ключ от Groq |
| `UNSPLASH_ACCESS_KEY` | `rv8AfdLoIH0xAqDDPc2hiXhevPyh672HRncOGN2p7EQ` |
| `DATABASE_URL` | External Connection String из Render PostgreSQL |
| `REDIS_URL` | External Connection String из Render Redis |
| `WEBHOOK_HOST` | `https://<твой-app-name>.koyeb.app` |
| `WEBHOOK_PATH` | `/webhook` |
| `ADMIN_ID` | `757179699` |
| `SBP_PHONE` | `+79994206101` |
| `SBP_BANK` | `ОЗОН` |
| `SBP_NAME` | `Роман` |
| `TRIAL_DAYS` | `7` |
| `POSTS_PER_DAY_TRIAL` | `3` |
| `POSTS_PER_DAY_SUBSCRIPTION` | `50` |
| `SUBSCRIPTION_PRICE` | `990` |

### 5. Deploy
Нажми **Deploy**. Через 3–5 минут бот будет доступен по URL.

### 6. Установи Webhook в Telegram
Открой в браузере:
```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<твой-app-name>.koyeb.app/webhook
```

Или бот сам установит webhook при старте (уже реализовано в коде).

### 7. Проверь работу
Напиши боту `/start` — должен ответить.

## Важно
- Koyeb Eco (free) даёт 512MB RAM — для бота достаточно
- Render PostgreSQL и Redis бесплатны, но PostgreSQL автоматически удалится через 90 дней если не продлить (делается в один клик в Dashboard)
- Если Koyeb попросит карту при регистрации — используй **GitHub-аккаунт** для входа, обычно не требует
