"""Создание картинок с наложенным текстом для Telegram-постов."""

import io
import os
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"


def _find_font(bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Find a suitable font, fallback to default if none found."""
    candidates = [
        FONTS_DIR / ("Inter-ExtraBold.otf" if bold else "Inter-Regular.otf"),
        FONTS_DIR / ("Inter-Bold.otf" if bold else "Inter-Regular.otf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=72 if bold else 36)
    
    # System fallback (Linux)
    system_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in system_fonts:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=72 if bold else 36)
    
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wrap text into lines that fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines if lines else [text]


def _create_overlay_sync(image_bytes: bytes, title: str, subtitle: str = "") -> bytes:
    """Synchronous image generation — run in thread pool."""
    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")
    
    # Resize to Telegram-friendly dimensions (1080x1080 square or 1200x675 landscape)
    # Use landscape for better feed appearance
    target_size = (1200, 675)
    img = img.resize(target_size, Image.LANCZOS)
    
    # Create dark gradient overlay at bottom
    overlay = Image.new("RGBA", target_size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    gradient_height = 380
    for i in range(gradient_height):
        alpha = int(200 * (i / gradient_height))
        y = target_size[1] - gradient_height + i
        draw_overlay.line([(0, y), (target_size[0], y)], fill=(10, 10, 20, alpha))
    
    # Composite
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_title = _find_font(bold=True)
    font_sub = _find_font(bold=False)
    
    # Margins
    margin_x = 60
    max_text_width = target_size[0] - margin_x * 2
    
    # Draw title with shadow
    title_lines = _wrap_text(title, font_title, max_text_width, draw)
    y = target_size[1] - 180 - (len(title_lines) - 1) * 80
    
    for line in title_lines:
        # Shadow
        draw.text((margin_x + 2, y + 2), line, font=font_title, fill=(0, 0, 0, 160))
        # Text
        draw.text((margin_x, y), line, font=font_title, fill=(255, 255, 255, 255))
        y += 80
    
    # Draw subtitle
    if subtitle:
        y += 10
        sub_lines = _wrap_text(subtitle, font_sub, max_text_width, draw)
        for line in sub_lines:
            draw.text((margin_x, y), line, font=font_sub, fill=(200, 200, 220, 230))
            y += 44
    
    # Convert to RGB and save as JPEG
    final = img.convert("RGB")
    output = io.BytesIO()
    final.save(output, format="JPEG", quality=92, optimize=True)
    output.seek(0)
    
    return output.getvalue()


async def create_image_with_text(image_url: str, title: str, subtitle: str = "") -> bytes | None:
    """Download image from URL, overlay text, return JPEG bytes."""
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                return None
            image_bytes = await resp.read()
    
    # Run CPU-heavy Pillow work in thread pool
    import asyncio
    return await asyncio.to_thread(_create_overlay_sync, image_bytes, title, subtitle)
