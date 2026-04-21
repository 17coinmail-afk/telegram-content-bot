from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from app.database.session import async_session
from app.database.models import User, Payment
from app.keyboards.inline import subscription_menu, main_menu
from app.config import config
import uuid

router = Router()


def _generate_sbp_comment(user_id: int) -> str:
    """Generate unique comment for SBP transfer."""
    return f"SUB{user_id}_{uuid.uuid4().hex[:6].upper()}"


@router.callback_query(F.data == "subscription:status")
async def show_subscription(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("Сначала нажми /start", show_alert=True)
        return
    
    text = (
        f"💎 <b>Подписка</b>\n\n"
        f"Статус: {user.status_text}\n"
        f"Постов сегодня: {user.posts_today} / {user.posts_limit}\n\n"
    )
    
    if user.is_subscription_active:
        days = (user.subscription_ends_at - datetime.utcnow()).days
        text += f"Подписка действует ещё {days} дней.\n\nСпасибо за поддержку! 🙏"
        await callback.message.edit_text(text, reply_markup=main_menu())
    else:
        text += (
            f"Стоимость: <b>{config.SUBSCRIPTION_PRICE} ₽/месяц</b>\n\n"
            f"В подписке:\n"
            f"• До {config.POSTS_PER_DAY_SUBSCRIPTION} постов в день\n"
            f"• Автопостинг в каналы\n"
            f"• Генерация картинок с текстом\n"
            f"• Техподдержка"
        )
        await callback.message.edit_text(text, reply_markup=subscription_menu())


@router.callback_query(F.data == "pay:subscribe")
async def show_sbp_details(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
    
    # Generate unique comment
    comment = _generate_sbp_comment(user.id)
    
    # Save payment to DB
    async with async_session() as session:
        db_payment = Payment(
            user_id=user.id,
            amount=config.SUBSCRIPTION_PRICE,
            currency="RUB",
            status="pending",
            sbp_comment=comment,
            description="Подписка на 1 месяц (СБП)",
        )
        session.add(db_payment)
        await session.commit()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"pay:confirm:{comment}")],
        [InlineKeyboardButton(text="« Назад", callback_data="subscription:status")],
    ])
    
    await callback.message.edit_text(
        f"💎 Оформление подписки через СБП\n\n"
        f"Сумма: <b>{config.SUBSCRIPTION_PRICE} ₽</b>\n"
        f"Период: 1 месяц\n\n"
        f"📱 <b>Реквизиты для перевода:</b>\n"
        f"Телефон: <code>{config.SBP_PHONE}</code>\n"
        f"Банк: {config.SBP_BANK}\n"
        f"Получатель: {config.SBP_NAME}\n\n"
        f"⚠️ <b>Обязательно укажи комментарий:</b>\n"
        f"<code>{comment}</code>\n\n"
        f"После перевода нажми кнопку «Я оплатил». Админ проверит и активирует подписку.",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("pay:confirm:"))
async def confirm_sbp_payment(callback: CallbackQuery):
    comment = callback.data.split(":")[2]
    
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.sbp_comment == comment)
        )
        payment = result.scalar_one_or_none()
    
    if not payment:
        await callback.answer("Платёж не найден", show_alert=True)
        return
    
    if payment.status != "pending":
        await callback.answer("Этот платёж уже обработан", show_alert=True)
        return
    
    # Notify admin
    from app.handlers.admin import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                admin_id,
                f"🔔 <b>Новый платёж на проверку</b>\n\n"
                f"Пользователь: {callback.from_user.id} (@{callback.from_user.username})\n"
                f"Сумма: {payment.amount} ₽\n"
                f"Комментарий: <code>{comment}</code>\n\n"
                f"Проверь поступление на карту и подтверди:\n"
                f"/approve_{payment.id}",
            )
        except Exception:
            pass
    
    await callback.message.edit_text(
        f"⏳ Заявка на оплату отправлена!\n\n"
        f"Комментарий: <code>{comment}</code>\n\n"
        f"Админ проверит поступление средств и активирует подписку в течение 24 часов.",
        reply_markup=main_menu(),
    )
