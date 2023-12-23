from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async_engine = create_async_engine('sqlite+aiosqlite:////home/ubuntu/trace_analytics/analytics.db')  
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

async_engine_backend = create_async_engine('sqlite+aiosqlite:////home/ubuntu/trace_backend/database.db')  
AsyncSessionLocal_backend = sessionmaker(autocommit=False, autoflush=False, bind=async_engine_backend, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_db_backend():
    async with AsyncSessionLocal_backend() as session:
        yield session