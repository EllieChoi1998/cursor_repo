"""
Excel 데이터 분석 서비스
엑셀 파일을 업로드하고 분석하는 서비스
"""

import pandas as pd
import json
import io
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
import asyncio
from datetime import datetime


class ExcelAnalysisService:
    """엑셀 데이터 분석 서비스"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    async def analyze_excel_file(self, file: UploadFile, prompt: str, chatroom_id: int, user_id: str) -> Dict[str, Any]:
        """
        엑셀 파일을 분석하고 결과를 반환
        
        Args:
            file: 업로드된 엑셀 파일
            prompt: 분석 프롬프트
            chatroom_id: 채팅방 ID
            user_id: 사용자 ID
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 파일 확장자 검증
            if not self._is_valid_file_format(file.filename):
                return {
                    'error': '지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일만 업로드 가능합니다.',
                    'success': False
                }
            
            # 파일 읽기
            content = await file.read()
            df = await self._read_excel_file(content, file.filename)
            
            if df is None or df.empty:
                return {
                    'error': '파일을 읽을 수 없거나 데이터가 비어있습니다.',
                    'success': False
                }
            
            # 데이터 분석 수행
            analysis_result = await self._perform_analysis(df, prompt)
            
            # 결과 포맷팅
            result = {
                'success': True,
                'file_name': file.filename,
                'data_type': 'excel_analysis',
                'analysis_type': analysis_result['type'],
                'data': analysis_result['data'],
                'summary': analysis_result['summary'],
                'chart_config': analysis_result.get('chart_config'),
                'sql': analysis_result.get('sql'),
                'chatroom_id': chatroom_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                'error': f'파일 분석 중 오류가 발생했습니다: {str(e)}',
                'success': False
            }
    
    def _is_valid_file_format(self, filename: str) -> bool:
        """파일 형식 검증"""
        if not filename:
            return False
        
        file_ext = filename.lower().split('.')[-1]
        return f'.{file_ext}' in self.supported_formats
    
    async def _read_excel_file(self, content: bytes, filename: str) -> Optional[pd.DataFrame]:
        """엑셀 파일 읽기"""
        try:
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext in ['xlsx', 'xls']:
                # 엑셀 파일 읽기
                df = pd.read_excel(io.BytesIO(content))
            elif file_ext == 'csv':
                # CSV 파일 읽기
                df = pd.read_csv(io.BytesIO(content))
            else:
                return None
            
            return df
            
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            return None
    
    async def _perform_analysis(self, df: pd.DataFrame, prompt: str) -> Dict[str, Any]:
        """데이터 분석 수행"""
        try:
            # 기본 정보 수집
            basic_info = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'sample_data': df.head(10).to_dict('records')
            }
            
            # 프롬프트에 따른 분석 타입 결정
            analysis_type = self._determine_analysis_type(prompt)
            
            if analysis_type == 'chart':
                return await self._create_chart_analysis(df, prompt, basic_info)
            elif analysis_type == 'summary':
                return await self._create_summary_analysis(df, prompt, basic_info)
            else:
                return await self._create_general_analysis(df, prompt, basic_info)
                
        except Exception as e:
            return {
                'type': 'error',
                'data': {},
                'summary': f'분석 중 오류가 발생했습니다: {str(e)}',
                'error': str(e)
            }
    
    def _determine_analysis_type(self, prompt: str) -> str:
        """프롬프트를 기반으로 분석 타입 결정"""
        prompt_lower = prompt.lower()
        
        if any(keyword in prompt_lower for keyword in ['차트', '그래프', '시각화', 'chart', 'graph', 'visualization']):
            return 'chart'
        elif any(keyword in prompt_lower for keyword in ['요약', '정리', '개요', 'summary']):
            return 'summary'
        else:
            return 'analysis'
    
    async def _create_general_analysis(self, df: pd.DataFrame, prompt: str, basic_info: Dict) -> Dict[str, Any]:
        """일반 분석 수행"""
        # 통계 정보 계산
        numeric_columns = df.select_dtypes(include=['number']).columns
        stats = {}
        
        for col in numeric_columns:
            stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median())
            }
        
        # 데이터 요약 생성
        summary = f"""
데이터 분석 결과:
- 총 행 수: {basic_info['shape'][0]}
- 총 열 수: {basic_info['shape'][1]}
- 컬럼: {', '.join(basic_info['columns'])}
- 결측값이 있는 컬럼: {[col for col, count in basic_info['null_counts'].items() if count > 0]}

수치형 컬럼 통계:
{self._format_stats(stats)}

분석 요청: {prompt}
        """.strip()
        
        return {
            'type': 'excel_analysis',
            'data': {
                'basic_info': basic_info,
                'statistics': stats,
                'raw_data': df.to_dict('records')
            },
            'summary': summary
        }
    
    async def _create_chart_analysis(self, df: pd.DataFrame, prompt: str, basic_info: Dict) -> Dict[str, Any]:
        """차트 분석 수행"""
        # 차트 생성을 위한 데이터 준비
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        chart_config = {
            'chart_type': 'bar',  # 기본값
            'x_column': categorical_columns[0] if categorical_columns else None,
            'y_column': numeric_columns[0] if numeric_columns else None,
            'data': df.to_dict('records')
        }
        
        # 프롬프트에 따른 차트 타입 결정
        prompt_lower = prompt.lower()
        if any(keyword in prompt_lower for keyword in ['선', 'line', '트렌드']):
            chart_config['chart_type'] = 'line'
        elif any(keyword in prompt_lower for keyword in ['산점도', 'scatter', '상관관계']):
            chart_config['chart_type'] = 'scatter'
        elif any(keyword in prompt_lower for keyword in ['파이', 'pie', '비율']):
            chart_config['chart_type'] = 'pie'
        
        summary = f"""
차트 분석 결과:
- 차트 타입: {chart_config['chart_type']}
- X축: {chart_config['x_column'] or 'N/A'}
- Y축: {chart_config['y_column'] or 'N/A'}
- 데이터 포인트: {len(df)}

분석 요청: {prompt}
        """.strip()
        
        return {
            'type': 'excel_chart',
            'data': {
                'basic_info': basic_info,
                'chart_data': df.to_dict('records')
            },
            'summary': summary,
            'chart_config': chart_config
        }
    
    async def _create_summary_analysis(self, df: pd.DataFrame, prompt: str, basic_info: Dict) -> Dict[str, Any]:
        """요약 분석 수행"""
        # 데이터 인사이트 생성
        insights = []
        
        # 결측값 체크
        null_columns = [col for col, count in basic_info['null_counts'].items() if count > 0]
        if null_columns:
            insights.append(f"주의: {', '.join(null_columns)} 컬럼에 결측값이 있습니다.")
        
        # 수치형 데이터 통계
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 0:
            insights.append(f"수치형 데이터 {len(numeric_columns)}개 컬럼이 있습니다.")
            
            # 이상치 체크 (간단한 IQR 방법)
            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                if len(outliers) > 0:
                    insights.append(f"{col} 컬럼에 {len(outliers)}개의 이상치가 있습니다.")
        
        # 범주형 데이터 체크
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_columns) > 0:
            insights.append(f"범주형 데이터 {len(categorical_columns)}개 컬럼이 있습니다.")
            
            for col in categorical_columns:
                unique_count = df[col].nunique()
                insights.append(f"{col} 컬럼에는 {unique_count}개의 고유값이 있습니다.")
        
        summary = f"""
데이터 요약:
- 총 행 수: {basic_info['shape'][0]}
- 총 열 수: {basic_info['shape'][1]}
- 컬럼: {', '.join(basic_info['columns'])}

주요 인사이트:
{chr(10).join(f"• {insight}" for insight in insights)}

분석 요청: {prompt}
        """.strip()
        
        return {
            'type': 'excel_summary',
            'data': {
                'basic_info': basic_info,
                'insights': insights,
                'sample_data': df.head(5).to_dict('records')
            },
            'summary': summary
        }
    
    def _format_stats(self, stats: Dict[str, Dict[str, float]]) -> str:
        """통계 정보 포맷팅"""
        if not stats:
            return "수치형 데이터가 없습니다."
        
        formatted = []
        for col, stat in stats.items():
            formatted.append(f"  {col}: 평균={stat['mean']:.2f}, 표준편차={stat['std']:.2f}")
        
        return "\n".join(formatted)