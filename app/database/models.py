from datetime import datetime, timedelta
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(128))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Daily limits
    posts_today: Mapped[int] = mapped_column(Integer, default=0)
    posts_reset_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", lazy="selectin")
    topics: Mapped[list["Topic"]] = relationship(back_populates="user", lazy="selectin")
    channels: Mapped[list["Channel"]] = relationship(back_populates="user", lazy="selectin")
    posts: Mapped[list["Post"]] = relationship(back_populates="user", lazy="selectin")
    
    @property
    def is_trial_active(self) -> bool:
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at
    
    @property
    def is_subscription_active(self) -> bool:
        if not self.subscription_ends_at:
            return False
        return datetime.utcnow() < self.subscription_ends_at
    
    @property
    def can_generate(self) -> bool:
        return self.is_trial_active or self.is_subscription_active
    
    @property
    def posts_limit(self) -> int:
        if self.is_subscription_active:
            return 50  # config.POSTS_PER_DAY_SUBSCRIPTION
        if self.is_trial_active:
            return 3   # config.POSTS_PER_DAY_TRIAL
        return 0
    
    @property
    def status_text(self) -> str:
        if self.is_subscription_active:
            days = (self.subscription_ends_at - datetime.utcnow()).days
            return f"💎 Подписка активна ({days} дн.)"
        if self.is_trial_active:
            days = (self.trial_ends_at - datetime.utcnow()).days
            return f"🎁 Пробный период ({days} дн.)"
        return "❌ Подписка неактивна"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, succeeded, canceled
    sbp_comment: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="payments")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(String(32), default="professional")  # professional, casual, humorous, serious
    post_length: Mapped[str] = mapped_column(String(32), default="medium")  # short, medium, long
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="topics")
    posts: Mapped[list["Post"]] = relationship(back_populates="topic")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256))
    username: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="channels")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"))
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id"))
    
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512))
    
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft, scheduled, published, failed
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger)
    error_message: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="posts")
    topic: Mapped["Topic | None"] = relationship(back_populates="posts")
