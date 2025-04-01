import os
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from models import Base

load_dotenv()  # Загрузка переменных из .env

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_async_engine(DATABASE_URL, echo=True)


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        

