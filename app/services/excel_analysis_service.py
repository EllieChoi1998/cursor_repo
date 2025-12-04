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
                'success_message': analysis_result.get('success_message', '✅ 엑셀 분석이 완료되었습니다.'),
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
                'type': 'general_text',
                'data': {},
                'summary': f'분석 중 오류가 발생했습니다: {str(e)}',
                'error': str(e),
                'chart_config': None,
                'success_message': f'❌ 분석 중 오류가 발생했습니다: {str(e)}'
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
            'summary': summary,
            'chart_config': None,
            'success_message': '✅ 엑셀 데이터 분석이 완료되었습니다.'
        }
    
    async def _create_chart_analysis(self, df: pd.DataFrame, prompt: str, basic_info: Dict) -> Dict[str, Any]:
        """차트 분석 수행 - Plotly 스펙 생성"""
        # 차트 생성을 위한 데이터 준비
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 프롬프트에 따른 차트 타입 결정
        prompt_lower = prompt.lower()
        chart_type = 'bar'  # 기본값
        
        if any(keyword in prompt_lower for keyword in ['박스', 'box', '분포', 'distribution']):
            chart_type = 'box'
        elif any(keyword in prompt_lower for keyword in ['선', 'line', '트렌드', 'trend']):
            chart_type = 'line'
        elif any(keyword in prompt_lower for keyword in ['산점도', 'scatter', '상관관계', 'correlation']):
            chart_type = 'scatter'
        elif any(keyword in prompt_lower for keyword in ['파이', 'pie', '비율']):
            chart_type = 'pie'
        
        # Plotly figure 생성
        plotly_spec = self._create_plotly_spec(
            df=df,
            chart_type=chart_type,
            x_column=categorical_columns[0] if categorical_columns else None,
            y_columns=numeric_columns[:5] if numeric_columns else []  # 최대 5개 컬럼
        )
        
        summary = f"""
차트 분석 결과:
- 차트 타입: {chart_type}
- X축: {categorical_columns[0] if categorical_columns else 'Index'}
- Y축: {', '.join(numeric_columns[:5]) if numeric_columns else 'N/A'}
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
            'chart_config': {
                'chart_type': chart_type,
                'plotly_spec': plotly_spec
            },
            'success_message': f'✅ {chart_type} 차트가 생성되었습니다.'
        }
    
    def _create_plotly_spec(self, df: pd.DataFrame, chart_type: str, x_column: str, y_columns: List[str]) -> Dict[str, Any]:
        """Plotly 스펙 생성"""
        data = []
        
        if chart_type == 'box':
            # 박스플롯 생성
            for y_col in y_columns:
                if x_column:
                    # 그룹별 박스플롯
                    data.append({
                        'type': 'box',
                        'name': y_col,
                        'x': df[x_column].tolist(),
                        'y': df[y_col].tolist(),
                        'boxmean': 'sd'
                    })
                else:
                    # 단일 박스플롯
                    data.append({
                        'type': 'box',
                        'name': y_col,
                        'y': df[y_col].tolist(),
                        'boxmean': 'sd'
                    })
            
            # 규격선 추가 (컬럼 이름에 USL, LSL, TGT가 포함된 경우)
            shapes = []
            spec_columns = [col for col in df.columns if any(spec in col.upper() for spec in ['USL', 'LSL', 'TGT', 'UCL', 'LCL'])]
            
            for spec_col in spec_columns:
                spec_value = df[spec_col].iloc[0] if len(df) > 0 else None
                if spec_value is not None:
                    color = "rgba(255, 0, 0, 0.6)" if 'USL' in spec_col.upper() or 'LSL' in spec_col.upper() else "rgba(0, 128, 0, 0.8)"
                    dash_style = "dash" if 'USL' in spec_col.upper() or 'LSL' in spec_col.upper() else "solid"
                    
                    shapes.append({
                        'type': 'line',
                        'xref': 'paper',
                        'yref': 'y',
                        'x0': 0,
                        'x1': 1,
                        'y0': spec_value,
                        'y1': spec_value,
                        'line': {
                            'color': color,
                            'width': 2,
                            'dash': dash_style
                        }
                    })
            
            layout = {
                'title': {'text': '박스플롯 분석'},
                'boxmode': 'group',
                'yaxis': {'title': {'text': 'Value'}},
                'margin': {'l': 80, 'r': 80, 't': 100, 'b': 120, 'pad': 10},
                'autosize': True,
                'shapes': shapes
            }
            
            if x_column:
                layout['xaxis'] = {'title': {'text': x_column}, 'tickangle': 0}
            
        elif chart_type == 'line':
            # 라인 차트 생성
            for y_col in y_columns:
                data.append({
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': y_col,
                    'x': df[x_column].tolist() if x_column else list(range(len(df))),
                    'y': df[y_col].tolist()
                })
            
            layout = {
                'title': {'text': '트렌드 차트'},
                'xaxis': {'title': {'text': x_column or 'Index'}},
                'yaxis': {'title': {'text': 'Value'}},
                'margin': {'l': 80, 'r': 80, 't': 100, 'b': 120, 'pad': 10},
                'autosize': True
            }
            
        elif chart_type == 'scatter':
            # 산점도 생성
            if len(y_columns) >= 2:
                data.append({
                    'type': 'scatter',
                    'mode': 'markers',
                    'x': df[y_columns[0]].tolist(),
                    'y': df[y_columns[1]].tolist(),
                    'marker': {'size': 8, 'opacity': 0.7}
                })
                
                layout = {
                    'title': {'text': '산점도'},
                    'xaxis': {'title': {'text': y_columns[0]}},
                    'yaxis': {'title': {'text': y_columns[1]}},
                    'margin': {'l': 80, 'r': 80, 't': 100, 'b': 120, 'pad': 10},
                    'autosize': True
                }
            else:
                # 데이터 부족 시 기본 bar 차트로
                return self._create_plotly_spec(df, 'bar', x_column, y_columns)
                
        else:  # bar (기본)
            # 막대 차트 생성
            for y_col in y_columns:
                data.append({
                    'type': 'bar',
                    'name': y_col,
                    'x': df[x_column].tolist() if x_column else list(range(len(df))),
                    'y': df[y_col].tolist()
                })
            
            layout = {
                'title': {'text': '막대 차트'},
                'barmode': 'group',
                'xaxis': {'title': {'text': x_column or 'Index'}, 'tickangle': 0},
                'yaxis': {'title': {'text': 'Value'}},
                'margin': {'l': 80, 'r': 80, 't': 100, 'b': 120, 'pad': 10},
                'autosize': True
            }
        
        return {
            'data': data,
            'layout': layout,
            'config': {
                'displaylogo': False,
                'responsive': True,
                'scrollZoom': True
            }
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
            'summary': summary,
            'chart_config': None,
            'success_message': '✅ 엑셀 데이터 요약이 완료되었습니다.'
        }
    
    def _format_stats(self, stats: Dict[str, Dict[str, float]]) -> str:
        """통계 정보 포맷팅"""
        if not stats:
            return "수치형 데이터가 없습니다."
        
        formatted = []
        for col, stat in stats.items():
            formatted.append(f"  {col}: 평균={stat['mean']:.2f}, 표준편차={stat['std']:.2f}")
        
        return "\n".join(formatted)