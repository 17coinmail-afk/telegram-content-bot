from aiogram import Bot
from aiogram.types import BufferedInputFile
from app.database.models import Post, Channel


async def publish_post(bot: Bot, post: Post, channel: Channel, image_bytes: bytes | None = None) -> int:
    """Publish post to Telegram channel. Returns message_id or raises."""
    if image_bytes:
        photo = BufferedInputFile(image_bytes, filename="post.jpg")
        msg = await bot.send_photo(
            chat_id=channel.telegram_id,
            photo=photo,
            caption=post.text[:1024] if len(post.text) > 1024 else post.text,
        )
    else:
        msg = await bot.send_message(
            chat_id=channel.telegram_id,
            text=post.text,
        )
    return msg.message_id
