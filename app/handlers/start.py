from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
from app.database.session import async_session
from app.database.models import User
from app.keyboards.inline import main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                trial_ends_at=datetime.utcnow() + timedelta(days=7),
                posts_reset_at=datetime.utcnow() + timedelta(days=1),
            )
            session.add(user)
            await session.commit()
            
            await message.answer(
                f"👋 Привет, {message.from_user.first_name or 'друг'}!\n\n"
                f"🎁 Тебе доступен <b>пробный период 7 дней</b>!\n"
                f"📌 3 поста в день бесплатно.\n\n"
                f"Что я умею:\n"
                f"• Генерировать посты с картинками на любую тему\n"
                f"• Автоматически публиковать в твой Telegram-канал\n"
                f"• Планировать публикации\n\n"
                f"Начни с создания темы 👇",
                reply_markup=main_menu(),
            )
        else:
            await message.answer(
                f"С возвращением, {user.first_name or 'друг'}!\n\n"
                f"{user.status_text}\n\n"
                f"Что будем делать?",
                reply_markup=main_menu(),
            )


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        status = user.status_text if user else ""
    
    await callback.message.edit_text(
        f"Главное меню\n\n{status}\n\nЧто будем делать?",
        reply_markup=main_menu(),
    )
