# app/db_async.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# ------------------------------------------------------------------------------
# 1️⃣ Explicitly load .env from project root
# ------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")

print(f"[db_async] Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)

# ------------------------------------------------------------------------------
# 2️⃣ Get and validate DATABASE_URL
# ------------------------------------------------------------------------------
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("[db_async] DATABASE_URL not set in .env")

# Ensure async driver prefix
if "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"[db_async] Using DATABASE_URL: {db_url}")

# ------------------------------------------------------------------------------
# 3️⃣ Build async engine and session
# ------------------------------------------------------------------------------
import ssl
from sqlalchemy.ext.asyncio import create_async_engine

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # optional: Azure certs already validated by host
ssl_context.verify_mode = ssl.CERT_REQUIRED

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args={"ssl": ssl_context},
    future=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# ------------------------------------------------------------------------------
# 4️⃣ Dependency for FastAPI routes
# ------------------------------------------------------------------------------
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
