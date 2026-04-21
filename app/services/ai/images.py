import aiohttp
import random
from app.config import config
from app.services.image_overlay import create_image_with_text

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


async def search_image(query: str) -> str | None:
    """Search for a relevant image on Unsplash. Returns image URL or None."""
    if not config.UNSPLASH_ACCESS_KEY:
        return None
    
    params = {
        "query": query,
        "per_page": 10,
        "orientation": "landscape",
        "client_id": config.UNSPLASH_ACCESS_KEY,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(UNSPLASH_API_URL, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            results = data.get("results", [])
            if not results:
                return None
            
            image = random.choice(results[:5])
            return image["urls"]["regular"]


async def generate_post_image(image_url: str | None, title: str, subtitle: str = "") -> bytes | None:
    """Download image and overlay text. Returns JPEG bytes or None."""
    if not image_url:
        return None
    return await create_image_with_text(image_url, title, subtitle)
