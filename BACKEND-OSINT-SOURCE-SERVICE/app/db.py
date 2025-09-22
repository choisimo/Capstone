from typing import Optional, AsyncGenerator
import asyncio

class AsyncSession:
    def __init__(self):
        pass
    
    async def execute(self, stmt):
        pass
    
    async def commit(self):
        pass
    
    async def rollback(self):
        pass
    
    async def close(self):
        pass

class sessionmaker:
    def __init__(self, bind=None, class_=None):
        self.bind = bind
        self.class_ = class_
    
    def __call__(self):
        return AsyncSession()

class AsyncEngine:
    def __init__(self, url: str):
        self.url = url

def create_async_engine(url: str) -> AsyncEngine:
    return AsyncEngine(url)

class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine, class_=AsyncSession)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.SessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# Initialize database with config
from app.config import settings
database = Database(settings.database_url)

# Dependency for FastAPI
async def get_db():
    async for session in database.get_session():
        yield session