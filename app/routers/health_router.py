"""
Health router - Handles health check and utility endpoints
"""

import os
import pandas as pd
from fastapi import APIRouter
from datetime import datetime

from app.services.data_generators import DataGenerators

router = APIRouter()


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Data Analysis Chat API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat (POST)",
            "docs": "/docs"
        },
        "supported_data_types": ['pcm', 'inline', 'rag']
    }


@router.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/api/masking-data-info")
async def get_masking_data_info():
    """마스킹된 데이터 정보 조회"""
    # 마스킹된 엑셀 데이터 로드 시도
    DataGenerators.load_masking_data(excel_name='masking_df.xlsx')
    
    # Note: We'd need to access the global masking_df from data_generators
    # This is a simplified version
    try:
        masking_df = pd.read_excel('masking_df.xlsx')
    except:
        masking_df = None
    
    if masking_df is None:
        return {
            "status": "no_data",
            "message": "마스킹된 엑셀 파일이 로드되지 않았습니다",
            "file_exists": os.path.exists('masking_df.xlsx')
        }
    
    if masking_df.empty:
        return {
            "status": "empty_data",
            "message": "마스킹된 데이터가 비어있습니다"
        }
    
    # 데이터 정보 반환
    info = {
        "status": "loaded",
        "message": "마스킹된 데이터가 성공적으로 로드되었습니다",
        "shape": {
            "rows": int(masking_df.shape[0]),
            "columns": int(masking_df.shape[1])
        },
        "columns": list(masking_df.columns),
        "data_types": {col: str(dtype) for col, dtype in masking_df.dtypes.items()},
        "sample_data": masking_df.head(3).to_dict('records') if len(masking_df) > 0 else []
    }
    
    # PARA 컬럼 정보
    if 'PARA' in masking_df.columns:
        para_counts = masking_df['PARA'].value_counts().to_dict()
        info["para_info"] = {
            "unique_paras": list(para_counts.keys()),
            "counts": para_counts
        }
    
    return info


@router.post("/api/reload-masking-data")
async def reload_masking_data():
    """마스킹된 엑셀 데이터 다시 로드"""
    success = DataGenerators.load_masking_data(excel_name='masking_df.xlsx')
    
    if success:
        try:
            masking_df = pd.read_excel('masking_df.xlsx')
            shape_info = {
                "rows": int(masking_df.shape[0]),
                "columns": int(masking_df.shape[1])
            }
        except:
            shape_info = None
            
        return {
            "status": "success",
            "message": "마스킹된 데이터를 성공적으로 다시 로드했습니다",
            "shape": shape_info
        }
    else:
        return {
            "status": "error",
            "message": "마스킹된 데이터 로드에 실패했습니다"
        }
