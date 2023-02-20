from os import getenv

DB_NAME = getenv("DB_NAME", "postgres")
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", 5432)
DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "postgres")

WEB_HOST = getenv("WEB_HOST", "localhost")
WEB_PORT = getenv("WEB_PORT", 8080)

if getenv("TEST"):
    ENGINE_STRING = "sqlite+aiosqlite:///:memory:"
else:
    ENGINE_STRING = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
