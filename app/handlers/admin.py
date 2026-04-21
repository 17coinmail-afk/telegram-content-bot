from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy import select, func
from app.database.session import async_session
from app.database.models import User, Payment
from app.keyboards.inline import main_menu
from datetime import datetime, timedelta

router = Router()

ADMIN_IDS = [757179699]


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        payments_count = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "succeeded")
        )
        total_revenue = await session.scalar(
            select(func.sum(Payment.amount)).where(Payment.status == "succeeded")
        )
        posts_count = await session.scalar(select(func.count(Post.id)))
        active_subs = await session.scalar(
            select(func.count(User.id)).where(User.subscription_ends_at > func.now())
        )
        pending_payments = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "pending")
        )
    
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👤 Пользователей: {users_count}\n"
        f"💎 Активных подписок: {active_subs}\n"
        f"⏳ Ожидают проверки: {pending_payments}\n"
        f"💳 Подтверждённых платежей: {payments_count}\n"
        f"💰 Выручка: {total_revenue or 0} ₽\n"
        f"📝 Сгенерировано постов: {posts_count}\n\n"
        f"/broadcast — рассылка всем\n"
        f"/pending — платежи на проверку\n"
        f"/approve_123 — подтвердить платёж (замени 123 на ID)",
        reply_markup=main_menu(),
    )


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == "pending").order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()
    
    if not payments:
        await message.answer("Нет платежей на проверку.")
        return
    
    text = "⏳ <b>Платежи на проверку:</b>\n\n"
    for p in payments:
        user_result = await session.execute(select(User).where(User.id == p.user_id))
        user = user_result.scalar_one_or_none()
        username = f"@{user.username}" if user and user.username else f"ID {user.telegram_id if user else '?'}}"
        text += f"ID: <code>{p.id}</code> | {p.amount} ₽ | {username}\nКоммент: <code>{p.sbp_comment or '—'}</code>\n\n"
    
    await message.answer(text)


@router.message(Command("approve"))
async def cmd_approve(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Parse command: /approve_123 or /approve 123
    parts = message.text.replace("/approve", "").strip().replace("_", " ").split()
    if not parts or not parts[-1].isdigit():
        await message.answer("Использование: /approve_123 или /approve 123")
        return
    
    payment_id = int(parts[-1])
    
    async with async_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        
        if not payment:
            await message.answer("Платёж не найден.")
            return
        
        if payment.status == "succeeded":
            await message.answer("Этот платёж уже подтверждён.")
            return
        
        payment.status = "succeeded"
        
        user_result = await session.execute(select(User).where(User.id == payment.user_id))
        user = user_result.scalar_one()
        
        if user.subscription_ends_at and user.subscription_ends_at > datetime.utcnow():
            user.subscription_ends_at += timedelta(days=30)
        else:
            user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
        
        await session.commit()
        
        # Notify user
        try:
            await message.bot.send_message(
                user.telegram_id,
                f"🎉 <b>Подписка активирована!</b>\n\n"
                f"Сумма: {payment.amount} ₽\n"
                f"Действует до: {user.subscription_ends_at.strftime('%d.%m.%Y')}\n\n"
                f"Теперь ты можешь генерировать до 50 постов в день!",
                reply_markup=main_menu(),
            )
        except Exception:
            pass
        
        await message.answer(
            f"✅ Платёж #{payment_id} подтверждён.\n"
            f"Пользователь {user.telegram_id} уведомлён."
        )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст>")
        return
    
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(user.telegram_id, text)
            sent += 1
        except Exception:
            failed += 1
    
    await message.answer(f"✅ Отправлено: {sent}\n❌ Не удалось: {failed}")
