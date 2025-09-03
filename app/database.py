"""
Database connection and utilities
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL 데이터베이스 연결 관리"""
    
    def __init__(self):
        self.connection_params = {
            'host': settings.DB_HOST,
            'database': settings.DB_DATABASE,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'port': settings.DB_PORT
        }
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = False
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self) -> Generator[psycopg2.extras.RealDictCursor, None, None]:
        """데이터베이스 커서 컨텍스트 매니저"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except psycopg2.Error as e:
                logger.error(f"Database cursor error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except psycopg2.Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# 전역 데이터베이스 연결 인스턴스
db_connection = DatabaseConnection()