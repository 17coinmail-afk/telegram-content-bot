import aiohttp
from app.config import config

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def build_prompt(topic_name: str, description: str | None, tone: str, length: str) -> str:
    length_map = {
        "short": "150-250 слов",
        "medium": "300-500 слов",
        "long": "600-900 слов",
    }
    length_desc = length_map.get(length, "300-500 слов")
    
    tone_desc = {
        "professional": "деловой, экспертный",
        "casual": "неформальный, дружелюбный",
        "humorous": "с юмором, лёгкий",
        "serious": "серьёзный, аналитический",
    }.get(tone, "деловой")

    prompt = f"""Напиши пост для Telegram-канала на тему "{topic_name}".

Тон: {tone_desc}
Объём: {length_desc}

"""
    if description:
        prompt += f"Контекст: {description}\n\n"
    
    prompt += """Требования:
- Привлекательный заголовок в начале
- Структура: вступление → основная часть → вывод/призыв к действию
- 2-3 абзаца, используй эмодзи
- В конце 3-5 релевантных хештегов
- Пиши на русском языке
- Без воды, конкретика и польза для читателя
"""
    return prompt


async def generate_post_text(topic_name: str, description: str | None, tone: str, length: str) -> str:
    prompt = build_prompt(topic_name, description, tone, length)
    
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Ты — опытный контент-мейкер для Telegram. Пишешь цепляющие, полезные посты на русском языке."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 4000,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(GROQ_API_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Groq API error {resp.status}: {text}")
            
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()
