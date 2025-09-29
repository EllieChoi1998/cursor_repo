#!/usr/bin/env python3
"""
Database initialization script
Run this script to set up the PostgreSQL database with all required tables
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database_init import init_database
from app.database import db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Test database connection first
    logger.info("Testing database connection...")
    if not db_connection.test_connection():
        logger.error("❌ Database connection failed!")
        logger.error("Please check your database configuration:")
        logger.error(f"  Host: {os.getenv('DB_HOST', 'localhost')}")
        logger.error(f"  Database: {os.getenv('DB_DATABASE', 'chat_analysis_db')}")
        logger.error(f"  User: {os.getenv('DB_USER', 'postgres')}")
        logger.error(f"  Port: {os.getenv('DB_PORT', '5433')}")
        logger.error("\nMake sure PostgreSQL is running and the database exists.")
        return False
    
    logger.info("✅ Database connection successful!")
    
    # Initialize database schema
    logger.info("Initializing database schema...")
    if init_database():
        logger.info("✅ Database initialization completed successfully!")
        logger.info("\nDatabase is ready to use with the following features:")
        logger.info("  - User management")
        logger.info("  - Chatroom management with soft delete")
        logger.info("  - Message and response storage")
        logger.info("  - Chat history preservation")
        logger.info("  - User session management")
        logger.info("  - Data preservation utilities")
        return True
    else:
        logger.error("❌ Database initialization failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)