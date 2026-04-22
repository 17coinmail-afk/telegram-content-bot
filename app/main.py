import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram import types

from app.config import config
from app.bot import bot, dp
from app.database.session import init_db
from app.handlers import start, topics, content, subscription, channels, admin
from aiogram.types import ErrorEvent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register routers
dp.include_router(start.router)
dp.include_router(topics.router)
dp.include_router(content.router)
dp.include_router(subscription.router)
dp.include_router(channels.router)
dp.include_router(admin.router)


@dp.error()
async def error_handler(event: ErrorEvent):
    logger.exception("Handler error: %s", event.exception)
    try:
        await bot.send_message(
            chat_id=757179699,
            text=f"❌ <b>Bot Error</b>\n<code>{str(event.exception)[:500]}</code>",
        )
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    missing = config.validate()
    if missing:
        logger.warning(f"Missing env vars: {', '.join(missing)}")
    
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
    
    # Set webhook with retry
    if config.WEBHOOK_HOST:
        for attempt in range(3):
            try:
                await bot.set_webhook(
                    url=config.webhook_url,
                    drop_pending_updates=True,
                )
                logger.info(f"Webhook set to {config.webhook_url}")
                break
            except Exception as e:
                logger.error(f"Webhook setup failed (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
    else:
        logger.info("WEBHOOK_HOST not set — webhook not configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        await bot.session.close()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)


@app.post(config.WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        result = await dp.feed_raw_update(bot, data)
        return {"ok": True, "result": str(result)}
    except Exception as e:
        logger.exception("Webhook error: %s", e)
        return {"ok": False, "error": str(e), "type": type(e).__name__}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# For local development with polling
async def main_polling():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
