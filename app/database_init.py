"""
Database initialization script
"""

import logging
from pathlib import Path
from app.database import db_connection

logger = logging.getLogger(__name__)


def init_database():
    """데이터베이스 초기화 - 테이블 생성"""
    try:
        # SQL 파일 읽기
        sql_file_path = Path(__file__).parent.parent / "tables.sql"
        
        if not sql_file_path.exists():
            logger.error(f"SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 데이터베이스 연결 테스트
        if not db_connection.test_connection():
            logger.error("Database connection test failed")
            return False
        
        # SQL 스크립트 실행
        with db_connection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_script)
                conn.commit()
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()