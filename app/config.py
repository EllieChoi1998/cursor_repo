"""
Configuration settings for the application
"""

import os
from typing import List


class Settings:
    """Application settings"""
    
    # App Info
    APP_TITLE: str = "Data Analysis Chat API"
    APP_VERSION: str = "1.0.0"
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://192.168.0.200:81"
    ]
    
    # Static Files
    STATIC_DIR: str = "static"
    DOCS_DIR: str = os.path.join(STATIC_DIR, "docs")
    
    # Data Files
    MASKING_DATA_FILE: str = "masking_df.xlsx"
    IQC_DATA_FILE: str = "iqc_data.xlsx"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # SSO Settings
    SSO_ALLOWED_ORIGINS: List[str] = [
        "http://192.168.0.200",
        "http://192.168.0.196"
    ]
    SSO_REDIRECT_BASE_URL: str = "http://192.168.0.196:80"
    
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "192.168.0.196")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "chat_analysis_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "dkzndk")
    DB_PORT: int = int(os.getenv("DB_PORT", "5433"))
    
    # Static file examples
    STATIC_EXAMPLES = {
        "example1.pdf": "PCM 데이터 분석 가이드\n\n이 문서는 PCM 데이터 분석 방법에 대한 상세한 가이드입니다.",
        "example2.pdf": "Commonality 분석 기법\n\nCommonality 분석을 통한 품질 관리 방법을 설명합니다.",
        "example3.pdf": "데이터 시각화 모범 사례\n\n효과적인 데이터 시각화 방법과 모범 사례를 제시합니다."
    }


settings = Settings()
