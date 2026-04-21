from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy import select
from app.database.session import async_session
from app.database.models import User, Channel
from app.keyboards.inline import channel_list, main_menu

router = Router()


@router.callback_query(F.data == "channels:list")
async def list_channels(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        channels_result = await session.execute(
            select(Channel).where(Channel.user_id == user.id, Channel.is_active == True)
        )
        channels = channels_result.scalars().all()
    
    if not channels:
        await callback.message.edit_text(
            "📢 У тебя пока нет подключённых каналов.\n\n"
            "Чтобы добавить канал:\n"
            "1. Добавь этого бота администратором в канал\n"
            "2. Отправь сюда юзернейм канала (например, @mychannel) или перешли любой пост из канала",
            reply_markup=channel_list([]),
        )
        return
    
    await callback.message.edit_text(
        f"📢 Твои каналы ({len(channels)}):\n\n"
        f"Бот может автоматически публиковать посты в эти каналы.",
        reply_markup=channel_list(channels),
    )


@router.callback_query(F.data == "channel:add")
async def add_channel_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "➕ Добавление канала\n\n"
        "1. Добавь этого бота администратором в канал\n"
        "2. Отправь сюда юзернейм канала (например, @mychannel) или перешли любой пост из канала\n\n"
        "Отправь юзернейм или перешли пост:",
    )


@router.message(F.text.startswith("@"))
async def add_channel_by_username(message: Message, bot: Bot):
    username = message.text.strip().lstrip("@")
    
    try:
        chat = await bot.get_chat(f"@{username}")
        
        # Check if bot is admin
        bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer(
                "❌ Бот не является администратором этого канала.\n\n"
                "Добавь бота администратором и попробуй снова.",
                reply_markup=main_menu(),
            )
            return
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one()
            
            channel = Channel(
                user_id=user.id,
                telegram_id=chat.id,
                title=chat.title,
                username=chat.username,
            )
            session.add(channel)
            await session.commit()
        
        await message.answer(
            f"✅ Канал \"{chat.title}\" добавлен!\n\n"
            f"Теперь бот может публиковать посты в этот канал.",
            reply_markup=main_menu(),
        )
    
    except Exception as e:
        await message.answer(
            f"❌ Не удалось добавить канал: {str(e)[:200]}\n\n"
            f"Убедись, что:\n"
            f"• Юзернейм указан правильно\n"
            f"• Бот добавлен администратором\n"
            f"• Канал публичный",
            reply_markup=main_menu(),
        )


@router.message(F.forward_from_chat)
async def add_channel_by_forward(message: Message, bot: Bot):
    chat = message.forward_from_chat
    if chat.type != "channel":
        await message.answer("Это не канал. Перешли пост из канала.")
        return
    
    try:
        bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer(
                "❌ Бот не является администратором этого канала.",
                reply_markup=main_menu(),
            )
            return
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one()
            
            channel = Channel(
                user_id=user.id,
                telegram_id=chat.id,
                title=chat.title,
                username=chat.username,
            )
            session.add(channel)
            await session.commit()
        
        await message.answer(
            f"✅ Канал \"{chat.title}\" добавлен!",
            reply_markup=main_menu(),
        )
    
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)[:200]}",
            reply_markup=main_menu(),
        )
