import ssl
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import config

# Render PostgreSQL uses self-signed SSL certs
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    config.DATABASE_URL,
    connect_args={"ssl": ssl_context},
    echo=False,
    future=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    from app.database.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
