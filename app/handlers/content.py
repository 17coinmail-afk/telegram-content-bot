from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from sqlalchemy import select, func
from app.database.session import async_session
from app.database.models import User, Topic, Post, Channel
from app.services.ai.groq import generate_post_text
from app.services.ai.images import search_image, generate_post_image
from app.services.telegram import publish_post
from app.keyboards.inline import content_preview, main_menu
from app.config import config

router = Router()


@router.callback_query(F.data == "content:generate")
async def start_generation(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.can_generate:
            await callback.answer(
                "❌ У тебя нет активной подписки. Оформи подписку или дождись окончания пробного периода.",
                show_alert=True,
            )
            return
        
        # Check daily limit
        if user.posts_reset_at and user.posts_reset_at < datetime.utcnow():
            user.posts_today = 0
            user.posts_reset_at = datetime.utcnow() + timedelta(days=1)
            await session.commit()
        
        if user.posts_today >= user.posts_limit:
            await callback.answer(
                f"⚠️ Дневной лимит исчерпан ({user.posts_limit} постов).\n"
                f"Попробуй завтра или оформи подписку!",
                show_alert=True,
            )
            return
        
        # Get topics
        topics_result = await session.execute(
            select(Topic).where(Topic.user_id == user.id, Topic.is_active == True)
        )
        topics = topics_result.scalars().all()
    
    if not topics:
        await callback.answer(
            "Сначала создай тему в разделе 'Мои темы'",
            show_alert=True,
        )
        return
    
    # Show topic selection for generation
    from app.keyboards.inline import topics_list
    await callback.message.edit_text(
        "Выбери тему для генерации поста:",
        reply_markup=topics_list(topics),
    )


@router.callback_query(F.data.startswith("topic:select:"))
async def generate_for_topic(callback: CallbackQuery, bot: Bot):
    # This is also called from topic list — we need to distinguish context
    # For simplicity, if message has 'Выбери тему для генерации' text, we generate
    if callback.message.text and "генерации поста" in callback.message.text:
        topic_id = int(callback.data.split(":")[2])
        
        await callback.message.edit_text("⏳ Генерирую пост... Это займёт 5-10 секунд.")
        
        async with async_session() as session:
            result = await session.execute(
                select(Topic).where(Topic.id == topic_id)
            )
            topic = result.scalar_one()
            
            # Generate text
            text = await generate_post_text(
                topic.name,
                topic.description,
                topic.tone,
                topic.post_length,
            )
            
            # Search image
            image_url = await search_image(topic.name)
            
            # Generate image with text overlay
            image_bytes = None
            if image_url:
                try:
                    # Extract first line as title for overlay
                    title = text.split('\n')[0][:80]
                    image_bytes = await generate_post_image(image_url, title)
                except Exception:
                    image_bytes = None
            
            # Create post record
            post = Post(
                user_id=topic.user_id,
                topic_id=topic.id,
                text=text,
                image_url=image_url,
                status="draft",
            )
            session.add(post)
            
            # Increment daily counter
            user_result = await session.execute(
                select(User).where(User.id == topic.user_id)
            )
            user = user_result.scalar_one()
            user.posts_today += 1
            
            await session.commit()
            await session.refresh(post)
        
        # Show preview
        preview_text = f"✨ <b>Превью поста</b>\n\n{text[:800]}"
        if len(text) > 800:
            preview_text += "\n\n<i>... (текст обрезан в превью)</i>"
        
        if image_bytes:
            await callback.message.delete()
            photo = BufferedInputFile(image_bytes, filename="preview.jpg")
            await callback.message.answer_photo(
                photo=photo,
                caption=preview_text,
                reply_markup=content_preview(post.id),
            )
        elif image_url:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=image_url,
                caption=preview_text,
                reply_markup=content_preview(post.id),
            )
        else:
            await callback.message.edit_text(
                preview_text + "\n\n<i>Картинка не найдена — пост будет текстовым.</i>",
                reply_markup=content_preview(post.id),
            )


@router.callback_query(F.data.startswith("post:publish:"))
async def publish_now(callback: CallbackQuery, bot: Bot):
    post_id = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if not post:
            await callback.answer("Пост не найден", show_alert=True)
            return
        
        # Get user's default channel (first active)
        channel_result = await session.execute(
            select(Channel).where(
                Channel.user_id == post.user_id,
                Channel.is_active == True,
            )
        )
        channel = channel_result.scalar_one_or_none()
    
    if not channel:
        await callback.answer(
            "❌ Не найден канал для публикации. Добавь канал в разделе 'Мои каналы'.",
            show_alert=True,
        )
        return
    
    # Regenerate image with text if needed
    image_bytes = None
    if post.image_url:
        try:
            title = post.text.split('\n')[0][:80]
            image_bytes = await generate_post_image(post.image_url, title)
        except Exception:
            image_bytes = None
    
    try:
        message_id = await publish_post(bot, post, channel, image_bytes)
        
        async with async_session() as session:
            result = await session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one()
            post.status = "published"
            post.published_at = datetime.utcnow()
            post.telegram_message_id = message_id
            await session.commit()
        
        await callback.message.edit_text(
            "✅ Пост опубликован!\n\n"
            f"<a href='https://t.me/{channel.username or 'c/' + str(channel.telegram_id)[4:]}'>{channel.title or 'Канал'}</a>",
            reply_markup=main_menu(),
        )
    except Exception as e:
        async with async_session() as session:
            result = await session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one()
            post.status = "failed"
            post.error_message = str(e)
            await session.commit()
        
        await callback.answer(
            f"❌ Ошибка публикации: {str(e)[:100]}",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("post:regenerate:"))
async def regenerate_post(callback: CallbackQuery, bot: Bot):
    post_id = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one()
        
        topic_result = await session.execute(
            select(Topic).where(Topic.id == post.topic_id)
        )
        topic = topic_result.scalar_one()
    
    await callback.message.edit_text("⏳ Перегенерирую пост...")
    
    text = await generate_post_text(
        topic.name,
        topic.description,
        topic.tone,
        topic.post_length,
    )
    image_url = await search_image(topic.name)
    
    # Regenerate overlay
    image_bytes = None
    if image_url:
        try:
            title = text.split('\n')[0][:80]
            image_bytes = await generate_post_image(image_url, title)
        except Exception:
            image_bytes = None
    
    async with async_session() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one()
        post.text = text
        post.image_url = image_url
        await session.commit()
    
    preview_text = f"✨ <b>Превью поста</b>\n\n{text[:800]}"
    if len(text) > 800:
        preview_text += "\n\n<i>... (текст обрезан в превью)</i>"
    
    if image_bytes:
        await callback.message.delete()
        photo = BufferedInputFile(image_bytes, filename="preview.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=preview_text,
            reply_markup=content_preview(post.id),
        )
    elif image_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=image_url,
            caption=preview_text,
            reply_markup=content_preview(post.id),
        )
    else:
        await callback.message.edit_text(
            preview_text + "\n\n<i>Картинка не найдена — пост будет текстовым.</i>",
            reply_markup=content_preview(post.id),
        )


