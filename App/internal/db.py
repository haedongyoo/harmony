from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

# sqlite:/// → sqlite+aiosqlite:///
_url = settings.database_url
if _url.startswith("sqlite:///"):
    _url = "sqlite+aiosqlite:///" + _url[len("sqlite:///"):]

engine = create_async_engine(_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
