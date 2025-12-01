"""
Database initialization script
Run this to create all tables in the database
"""
from app.database import engine, Base
from app.models import User, Subscription, Payment, Conversion
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Print table names
        logger.info("Tables created:")
        for table in Base.metadata.tables.keys():
            logger.info(f"  - {table}")
            
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
