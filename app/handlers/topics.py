from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from app.database.session import async_session
from app.database.models import User, Topic
from app.keyboards.inline import topics_list, topic_actions, main_menu

router = Router()


class TopicForm(StatesGroup):
    name = State()
    description = State()
    tone = State()
    length = State()


@router.callback_query(F.data == "topics:list")
async def list_topics(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        topics_result = await session.execute(
            select(Topic).where(Topic.user_id == user.id, Topic.is_active == True)
        )
        topics = topics_result.scalars().all()
    
    if not topics:
        await callback.message.edit_text(
            "У тебя пока нет тем.\n\n"
            "Тема — это направление для постов. Например: AI в маркетинге, финансовая грамотность, здоровье.\n\n"
            "Создай первую тему 👇",
            reply_markup=topics_list([]),
        )
        return
    
    await callback.message.edit_text(
        f"📌 Твои темы ({len(topics)}):\n\n"
        f"Выбери тему для генерации поста или создай новую.",
        reply_markup=topics_list(topics),
    )


@router.callback_query(F.data == "topic:add")
async def add_topic_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopicForm.name)
    await callback.message.edit_text(
        "➕ Создание новой темы\n\n"
        "Шаг 1/4: Введи название темы\n"
        "Пример: AI в маркетинге",
    )


@router.message(TopicForm.name)
async def add_topic_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TopicForm.description)
    await message.answer(
        "Шаг 2/4: Опиши тему подробнее (или отправь '-')\n"
        "Это поможет AI генерировать более точный контент.",
    )


@router.message(TopicForm.description)
async def add_topic_description(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else None
    await state.update_data(description=desc)
    await state.set_state(TopicForm.tone)
    await message.answer(
        "Шаг 3/4: Выбери тон постов:\n\n"
        "1️⃣ Деловой\n"
        "2️⃣ Неформальный\n"
        "3️⃣ С юмором\n"
        "4️⃣ Серьёзный\n\n"
        "Отправь цифру 1-4",
    )


@router.message(TopicForm.tone)
async def add_topic_tone(message: Message, state: FSMContext):
    tone_map = {"1": "professional", "2": "casual", "3": "humorous", "4": "serious"}
    tone = tone_map.get(message.text, "professional")
    await state.update_data(tone=tone)
    await state.set_state(TopicForm.length)
    await message.answer(
        "Шаг 4/4: Выбери длину постов:\n\n"
        "1️⃣ Короткие (150-250 слов)\n"
        "2️⃣ Средние (300-500 слов)\n"
        "3️⃣ Длинные (600-900 слов)\n\n"
        "Отправь цифру 1-3",
    )


@router.message(TopicForm.length)
async def add_topic_length(message: Message, state: FSMContext):
    length_map = {"1": "short", "2": "medium", "3": "long"}
    length = length_map.get(message.text, "medium")
    data = await state.get_data()
    await state.clear()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one()
        
        topic = Topic(
            user_id=user.id,
            name=data["name"],
            description=data.get("description"),
            tone=data["tone"],
            post_length=length,
        )
        session.add(topic)
        await session.commit()
    
    await message.answer(
        f"✅ Тема \"{data['name']}\" создана!\n\n"
        f"Теперь можешь генерировать посты по этой теме.",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data.startswith("topic:select:"))
async def select_topic(callback: CallbackQuery):
    topic_id = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
    
    if not topic:
        await callback.answer("Тема не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📌 Тема: <b>{topic.name}</b>\n\n"
        f"Описание: {topic.description or 'нет'}\n"
        f"Тон: {topic.tone}\n"
        f"Длина: {topic.post_length}\n\n"
        f"Что сделать?",
        reply_markup=topic_actions(topic.id),
    )


@router.callback_query(F.data.startswith("topic:delete:"))
async def delete_topic(callback: CallbackQuery):
    topic_id = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if topic:
            topic.is_active = False
            await session.commit()
    
    await callback.answer("Тема удалена")
    await list_topics(callback)
