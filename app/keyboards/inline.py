from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Мои темы", callback_data="topics:list")],
        [InlineKeyboardButton(text="✨ Сгенерировать пост", callback_data="content:generate")],
        [InlineKeyboardButton(text="📢 Мои каналы", callback_data="channels:list")],
        [InlineKeyboardButton(text="💎 Подписка", callback_data="subscription:status")],
    ])


def topics_list(topics: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"📌 {t.name}", callback_data=f"topic:select:{t.id}")]
        for t in topics
    ]
    buttons.append([InlineKeyboardButton(text="➕ Добавить тему", callback_data="topic:add")])
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def topic_actions(topic_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"topic:edit:{topic_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"topic:delete:{topic_id}")],
        [InlineKeyboardButton(text="« Назад", callback_data="topics:list")],
    ])


def content_preview(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Регенерировать", callback_data=f"post:regenerate:{post_id}"),
            InlineKeyboardButton(text="📝 Изменить текст", callback_data=f"post:edit:{post_id}"),
        ],
        [
            InlineKeyboardButton(text="📢 Опубликовать сейчас", callback_data=f"post:publish:{post_id}"),
        ],
        [
            InlineKeyboardButton(text="⏰ Отложить", callback_data=f"post:schedule:{post_id}"),
        ],
        [InlineKeyboardButton(text="« Назад", callback_data="menu:main")],
    ])


def subscription_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оформить подписку — 990 ₽/мес", callback_data="pay:subscribe")],
        [InlineKeyboardButton(text="« Назад", callback_data="menu:main")],
    ])


def payment_confirm(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="pay:check")],
        [InlineKeyboardButton(text="« Назад", callback_data="menu:main")],
    ])


def channel_list(channels: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"📢 {c.title or c.username or c.telegram_id}", callback_data=f"channel:select:{c.id}")]
        for c in channels
    ]
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="channel:add")])
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
