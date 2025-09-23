import asyncio
import logging
from database import init_db
import models  # Importa los modelos para que se registren con SQLAlchemy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")

if __name__ == "__main__":
    # Fix for "Event loop is closed" on Windows
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass
    asyncio.run(init_db())
    logger.info("Database initialized successfully!")