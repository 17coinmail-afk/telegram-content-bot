import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    
    # Payments (СБП — реквизиты для перевода)
    SBP_PHONE: str = os.getenv("SBP_PHONE", "")
    SBP_BANK: str = os.getenv("SBP_BANK", "")
    SBP_NAME: str = os.getenv("SBP_NAME", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/botdb")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Webhook (Render)
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    
    # Business logic
    TRIAL_DAYS: int = int(os.getenv("TRIAL_DAYS", "7"))
    POSTS_PER_DAY_TRIAL: int = int(os.getenv("POSTS_PER_DAY_TRIAL", "3"))
    POSTS_PER_DAY_SUBSCRIPTION: int = int(os.getenv("POSTS_PER_DAY_SUBSCRIPTION", "50"))
    SUBSCRIPTION_PRICE: int = int(os.getenv("SUBSCRIPTION_PRICE", "990"))  # RUB per month
    
    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"
    
    def validate(self) -> list[str]:
        """Return list of missing required env vars"""
        required = [
            ("BOT_TOKEN", self.BOT_TOKEN),
            ("GROQ_API_KEY", self.GROQ_API_KEY),
            ("DATABASE_URL", self.DATABASE_URL),
        ]
        return [name for name, value in required if not value]


config = Config()
