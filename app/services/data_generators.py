"""
Data generators service - Handles generation of sample and real data
"""

import pandas as pd
import numpy as np
import random
import math
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# 전역 변수로 마스킹된 데이터프레임 저장
masking_df = None


class DataGenerators:
    """데이터 생성 서비스"""
    
    @staticmethod
    def load_masking_data(excel_name: str = 'masking_df.xlsx') -> bool:
        """마스킹된 엑셀 데이터 로드"""
        global masking_df
        try:
            masking_df = pd.read_excel(excel_name)
            print(f"📊 마스킹 데이터 로드 완료: {masking_df.shape[0]}행 {masking_df.shape[1]}열")
            print(f"📊 컬럼 목록: {list(masking_df.columns)}")
            return True
        except FileNotFoundError:
            print("⚠️ masking_df.xlsx 파일을 찾을 수 없습니다. 샘플 데이터를 사용합니다.")
            return False
        except Exception as e:
            print(f"❌ 마스킹 데이터 로드 오류: {e}")
            return False

    @staticmethod
    def generate_pcm_trend_data() -> dict:
        """PCM 트렌드 데이터 생성"""
        data = {}
        para_list = ["PARA1", "PARA2"]
        for para in para_list:
            single = []
            for i in range(1, 1000):
                single.append({
                    'DATE_WAFER_ID': f'2025-06-{i}:36:57:54_A12345678998999',
                    'MIN': round(random.uniform(8, 12), 2),
                    'MAX': round(random.uniform(18, 22), 2),
                    'Q1': round(random.uniform(14, 16), 2),
                    'Q2': round(random.uniform(15, 17), 2),
                    'Q3': round(random.uniform(16, 18), 2),
                    'DEVICE': random.choice(['A', 'B', 'C']),
                    'USL': 30,
                    'TGT': 15,
                    'LSL': 1,
                    'UCL': 25,
                    'LCL': 6
                })
            data[para] = single
        return data

    @staticmethod
    def generate_commonality_data() -> Tuple[List, Dict]:
        """Commonality 데이터 생성"""
        # 테이블용 배열 데이터 생성 (PCM 트렌드 데이터를 배열로 변환)
        pcm_data = DataGenerators.generate_pcm_trend_data()
        
        print(f"🔍 generate_commonality_data: pcm_data type = {type(pcm_data)}")
        print(f"🔍 generate_commonality_data: pcm_data keys = {list(pcm_data.keys()) if isinstance(pcm_data, dict) else 'not dict'}")
        
        # PARA별 객체를 배열로 변환
        table_data = []
        for para_name, para_data in pcm_data.items():
            for row in para_data:
                table_data.append({
                    **row,
                    'PARA': para_name
                })
        
        print(f"🔍 generate_commonality_data: table_data type = {type(table_data)}")
        print(f"🔍 generate_commonality_data: table_data length = {len(table_data)}")
        print(f"🔍 generate_commonality_data: table_data sample = {table_data[:2] if table_data else 'empty'}")
        
        # Commonality 정보
        commonality = {
            'good_lots': ['LOT001', 'LOT002', 'LOT003'],
            'bad_lots': ['LOT004', 'LOT005'],
            'good_wafers': ['WAFER001', 'WAFER002', 'WAFER003'],
            'bad_wafers': ['WAFER004', 'WAFER005']
        }
        
        return table_data, commonality

    @staticmethod
    def generate_pcm_point_data() -> List:
        """PCM 트렌드 포인트(라인+마커)용 예시 데이터 (고정값)"""
        return [
            {'DATE_WAFER_ID': '2025-06-1:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 10},
            {'DATE_WAFER_ID': '2025-06-2:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 11},
            {'DATE_WAFER_ID': '2025-06-3:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 12},
            {'DATE_WAFER_ID': '2025-06-4:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-5:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 14},
            {'DATE_WAFER_ID': '2025-06-6:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 11},
            {'DATE_WAFER_ID': '2025-06-7:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 12},
            {'DATE_WAFER_ID': '2025-06-8:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-9:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 14},
            {'DATE_WAFER_ID': '2025-06-10:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 15},
            {'DATE_WAFER_ID': '2025-06-11:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 10},
            {'DATE_WAFER_ID': '2025-06-12:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 11},
            {'DATE_WAFER_ID': '2025-06-13:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 12},
            {'DATE_WAFER_ID': '2025-06-14:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-15:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 14},
            {'DATE_WAFER_ID': '2025-06-16:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 12},
            {'DATE_WAFER_ID': '2025-06-17:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-18:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 14},
            {'DATE_WAFER_ID': '2025-06-19:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 15},
            {'DATE_WAFER_ID': '2025-06-20:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 16},
            {'DATE_WAFER_ID': '2025-06-21:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 14},
            {'DATE_WAFER_ID': '2025-06-22:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-23:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 13},
            {'DATE_WAFER_ID': '2025-06-24:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 12},
            {'DATE_WAFER_ID': '2025-06-25:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 11},
        ]

    @staticmethod
    def generate_inline_analysis_data() -> List:
        """INLINE 분석 데이터 생성"""
        # 마스킹된 엑셀 데이터 로드 시도
        DataGenerators.load_masking_data(excel_name='iqc_data.xlsx')
        global masking_df

        # 실제 엑셀 데이터가 있으면 사용
        if masking_df is not None and not masking_df.empty:
            try:
                print("📊 실제 마스킹 데이터 사용")
                
                # 데이터프레임 복사 후 정리
                df_clean = masking_df.copy()
                
                # 1. datetime/timestamp 컬럼들을 문자열로 변환
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                        df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"📅 날짜 컬럼 변환: {col}")
                    elif df_clean[col].dtype == 'object':
                        # object 타입 컬럼에서 숨겨진 Timestamp 찾기
                        sample_val = df_clean[col].dropna().iloc[0] if len(df_clean[col].dropna()) > 0 else None
                        if sample_val is not None and isinstance(sample_val, (pd.Timestamp, datetime)):
                            df_clean[col] = df_clean[col].apply(
                                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
                            )
                            print(f"📅 숨겨진 날짜 컬럼 변환: {col}")
                
                # 2. NaN, inf, -inf 값들을 None으로 변환 (중요!)
                df_clean = df_clean.replace([np.nan, np.inf, -np.inf], None)
                
                # 3. numpy 타입들을 Python 기본 타입으로 변환
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'int64':
                        df_clean[col] = df_clean[col].astype('Int64')  # nullable integer
                    elif df_clean[col].dtype == 'float64':
                        pass  # float은 그대로

                # 4. 딕셔너리로 변환
                data = df_clean.to_dict(orient='records')
                
                # 5. 각 레코드에서 모든 Timestamp 객체를 문자열로 변환
                for record in data:
                    for key, value in list(record.items()):
                        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                            print(f"🚨 레코드 내 Timestamp 변환: {key}")
                        elif key.startswith('NO_VAL') and value == 9:
                            record[key] = None
                        elif hasattr(value, 'item'):  # numpy scalar types
                            record[key] = value.item()
                
                # 6. JSON 직렬화 테스트
                try:
                    json.dumps(data[0] if data else {}, default=str)
                    print("✅ JSON 직렬화 테스트 통과")
                except Exception as json_error:
                    print(f"🚨 JSON 직렬화 테스트 실패: {json_error}")
                    # 문제가 있는 값들을 모두 문자열로 변환
                    for record in data:
                        for key, value in list(record.items()):
                            try:
                                json.dumps(value)
                            except:
                                print(f"🔧 문제 값 수정: {key} = {type(value)} -> str")
                                record[key] = str(value) if value is not None else None
                
                print(f"✅ 데이터 변환 완료: {len(data)}개 레코드")
                print(f"📊 실제 데이터 컬럼: {list(df_clean.columns)}")
                if len(data) > 0:
                    print(f"📊 첫 번째 행 샘플: {data[0]}")
                
                return data
                
            except Exception as e:
                print(f"❌ 실제 데이터 처리 오류: {e}")
                print("📊 샘플 데이터로 대체합니다.")
        
        print("📊 샘플 데이터 생성 (엑셀 파일 없음)")
        data = []
        for i in range(1, 16):
            data.append({
                'timestamp': f'2024-01-{i:02d}',
                'critical_path_length': round(random.uniform(10, 20), 2),
                'performance_score': round(random.uniform(0.7, 0.95), 3),
                'bottleneck_count': random.randint(1, 5),
                'optimization_potential': round(random.uniform(0.1, 0.3), 3)
            })
        return data

    @staticmethod
    def generate_inline_trend_initial_data() -> List:
        """INLINE Trend Initial 데이터 생성 (DEVICE 기준)"""
        DataGenerators.load_masking_data(excel_name='iqc_data.xlsx')
        global masking_df

        # 실제 엑셀 데이터가 있으면 사용
        if masking_df is not None and not masking_df.empty:
            try:
                print("📊 실제 마스킹 데이터 사용")
                
                # 데이터프레임 복사 후 정리
                df_clean = masking_df.copy()
                
                # 1. datetime/timestamp 컬럼들을 문자열로 변환
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                        df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"📅 날짜 컬럼 변환: {col}")
                
                # 2. NaN, inf, -inf 값들을 None으로 변환 (중요!)
                df_clean = df_clean.replace([np.nan, np.inf, -np.inf], None)
                
                # 3. numpy 타입들을 Python 기본 타입으로 변환
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'int64':
                        df_clean[col] = df_clean[col].astype('Int64')  # nullable integer
                    elif df_clean[col].dtype == 'float64':
                        pass  # float은 그대로

                # 4. (수정) FOR_KEY 단일 필터링 제거 — 모든 FOR_KEY 유지
                if 'FOR_KEY' in df_clean.columns:
                    df_clean['FOR_KEY'] = df_clean['FOR_KEY'].astype(str).str.strip()
                    uniq = df_clean['FOR_KEY'].dropna().unique().tolist()
                    print(f"📝 FOR_KEY 고유값 수: {len(uniq)} | 예시: {uniq[:5]}")

                # 5. x축용 key 컬럼 생성
                if 'TRANS_DATE' in df_clean.columns:
                    df_clean['_sort_ts'] = pd.to_datetime(df_clean['TRANS_DATE'], errors='coerce')
                    df_clean = df_clean.sort_values('_sort_ts')
                    df_clean['key'] = df_clean['_sort_ts'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna(df_clean['TRANS_DATE'].astype(str))
                    df_clean = df_clean.drop(columns=['_sort_ts'])
                    print("📝 TRANS_DATE를 key로 사용")
                
                # 6. 딕셔너리로 변환 후 다시 한번 NaN 체크
                data = df_clean.to_dict(orient='records')
                
                # 7. 각 레코드에서 NaN/inf/결측코드 처리 및 key 문자열 보장
                for record in data:
                    for key, value in record.items():
                        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                            record[key] = None
                        elif key.startswith('NO_VAL') and value == 9:
                            record[key] = None
                    if 'key' in record and record['key'] is not None:
                        record['key'] = str(record['key'])
                
                print(f"✅ 데이터 변환 완료: {len(data)}개 레코드")
                print(f"📊 실제 데이터 컬럼: {list(df_clean.columns)}")
                if len(data) > 0:
                    print(f"📊 첫 번째 행 샘플: {data[0]}")
                
                return data
                
            except Exception as e:
                print(f"❌ 실제 데이터 처리 오류: {e}")
                print("📊 샘플 데이터로 대체합니다.")
        
        # (샘플 데이터 생성부는 기존 그대로 둠)
        print("📊 박스플롯용 샘플 데이터 생성")
        data = []
        devices = ['DEVICE_A', 'DEVICE_B', 'DEVICE_C']
        for i, device in enumerate(devices):
            base_values = [380 + i*20, 420 + i*20, 460 + i*20]
            for j in range(5):
                key_idx = i * 5 + j + 1
                data.append({
                    'key': f'2024-01-{key_idx:02d} 10:00:00',
                    'FOR_KEY': 'P1931.52926.5',  # 샘플은 그대로
                    'DEVICE': device,
                    'NO_VAL1': round(base_values[0] + random.uniform(-30, 30), 3),
                    'NO_VAL2': round(base_values[1] + random.uniform(-30, 30), 3), 
                    'NO_VAL3': round(base_values[2] + random.uniform(-30, 30), 3),
                    'NO_VAL4': round(base_values[0] + random.uniform(-25, 25), 3),
                    'NO_VAL5': round(base_values[1] + random.uniform(-25, 25), 3),
                    'USL': 550,
                    'LSL': 300,
                    'TGT': 420,
                    'UCL': 500,
                    'LCL': 350
                })
        return data

    @staticmethod
    def generate_inline_trend_followup_data(criteria: str) -> List:
        """INLINE Trend Followup 데이터 생성 (다양한 criteria 기준)"""
        DataGenerators.load_masking_data(excel_name='iqc_data.xlsx')
        global masking_df

        # 실제 엑셀 데이터가 있으면 사용
        if masking_df is not None and not masking_df.empty:
            try:
                print(f"📊 실제 마스킹 데이터 사용 (criteria: {criteria})")
                
                df_clean = masking_df.copy()
                
                # 1. datetime/timestamp 컬럼들을 문자열로 변환 (강화)
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                        df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"📅 날짜 컬럼 변환: {col}")
                    elif df_clean[col].dtype == 'object':
                        sample_val = df_clean[col].dropna().iloc[0] if len(df_clean[col].dropna()) > 0 else None
                        if sample_val is not None and isinstance(sample_val, (pd.Timestamp, datetime)):
                            df_clean[col] = df_clean[col].apply(
                                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
                            )
                            print(f"📅 숨겨진 날짜 컬럼 변환: {col}")
                
                # 2. NaN, inf, -inf → None
                df_clean = df_clean.replace([np.nan, np.inf, -np.inf], None)
                
                # 3. numpy 스칼라 타입 처리
                for col in df_clean.columns:
                    if df_clean[col].dtype == 'int64':
                        df_clean[col] = df_clean[col].astype('Int64')
                    elif df_clean[col].dtype == 'float64':
                        pass

                # 4. criteria 보정
                if criteria not in df_clean.columns:
                    print(f"⚠️ criteria '{criteria}' 컬럼이 없습니다. 사용 가능한 컬럼: {list(df_clean.columns)}")
                    available_criteria = ['MAIN_EQ', 'DEVICE', 'PARA', 'EQ_CHAM', 'LOT_ID', 'OPER', 'ROUTE']
                    for alt_criteria in available_criteria:
                        if alt_criteria in df_clean.columns:
                            print(f"📝 대체 criteria 사용: {alt_criteria}")
                            criteria = alt_criteria
                            break
                    else:
                        raise ValueError("No valid criteria found")
                
                # 5. (수정) FOR_KEY 단일 필터링 제거 — 모든 FOR_KEY 유지
                if 'FOR_KEY' in df_clean.columns:
                    df_clean['FOR_KEY'] = df_clean['FOR_KEY'].astype(str).str.strip()
                    uniq = df_clean['FOR_KEY'].dropna().unique().tolist()
                    print(f"📝 FOR_KEY 고유값 수: {len(uniq)} | 예시: {uniq[:5]}")

                # 6. x축용 key 컬럼 생성
                if 'TRANS_DATE' in df_clean.columns:
                    df_clean['_sort_ts'] = pd.to_datetime(df_clean['TRANS_DATE'], errors='coerce')
                    df_clean = df_clean.sort_values('_sort_ts')
                    df_clean['key'] = df_clean['_sort_ts'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna(df_clean['TRANS_DATE'].astype(str))
                    df_clean = df_clean.drop(columns=['_sort_ts'])
                    print("📝 TRANS_DATE를 key로 사용")
                elif 'LOT_NO' in df_clean.columns:
                    df_clean['key'] = df_clean['LOT_NO'].astype(str)
                    print("📝 LOT_NO를 key로 사용")
                elif 'WAFER_ID' in df_clean.columns:
                    df_clean['key'] = df_clean['WAFER_ID'].astype(str)
                    print("📝 WAFER_ID를 key로 사용")
                elif 'FOR_KEY' in df_clean.columns:
                    df_clean['key'] = df_clean['FOR_KEY'].astype(str)
                    print("📝 FOR_KEY를 key로 사용")
                else:
                    df_clean['key'] = df_clean.reset_index().index.astype(str)
                    print("📝 인덱스를 key로 사용")
                
                # 🚨 criteria 컬럼 Timestamp 특별 처리
                if criteria in df_clean.columns:
                    print(f"🔍 criteria '{criteria}' 컬럼 타입: {df_clean[criteria].dtype}")
                    sample_vals = df_clean[criteria].dropna().head(3).tolist()
                    print(f"🔍 criteria 샘플 값들: {sample_vals}")
                    for i, val in enumerate(sample_vals):
                        print(f"  {i}: {val} (type: {type(val)})")
                        if isinstance(val, (pd.Timestamp, datetime)):
                            df_clean[criteria] = df_clean[criteria].apply(
                                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
                            )
                            print(f"✅ criteria '{criteria}' Timestamp → 문자열 변환 완료")
                            break
                
                # 7. 정렬
                try:
                    print(f"📊 정렬 전 criteria '{criteria}' 고유값: {df_clean[criteria].nunique()}개")
                    for idx, val in df_clean[criteria].items():
                        if isinstance(val, (pd.Timestamp, datetime)):
                            df_clean.at[idx, criteria] = val.strftime('%Y-%m-%d %H:%M:%S')
                            print(f"🔧 정렬 전 추가 Timestamp 수정: {idx}")
                    df_clean = df_clean.sort_values([criteria, 'key'])
                    print(f"📊 {criteria} 기준 정렬 완료")
                except Exception as e:
                    print(f"⚠️ 정렬 실패: {e}, 기본 순서 유지")
                
                # 8. 딕셔너리 변환
                data = df_clean.to_dict(orient='records')
                
                # 9. JSON 비호환 값 정리
                for record in data:
                    for key, value in list(record.items()):
                        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                            print(f"🚨 늦게 발견된 Timestamp 변환: {key}")
                        elif key.startswith('NO_VAL') and value == 9:
                            record[key] = None
                        elif hasattr(value, 'item'):
                            record[key] = value.item()
                    if 'key' in record and record['key'] is not None:
                        record['key'] = str(record['key'])
                
                print(f"✅ 데이터 변환 완료: {len(data)}개 레코드")
                print(f"📊 사용된 criteria: {criteria}")
                
                # JSON 직렬화 테스트
                try:
                    json.dumps(data[0] if data else {}, default=str)
                    print("✅ JSON 직렬화 테스트 통과")
                except Exception as json_error:
                    print(f"🚨 JSON 직렬화 테스트 실패: {json_error}")
                    for record in data:
                        for key, value in list(record.items()):
                            try:
                                json.dumps(value)
                            except:
                                print(f"🔧 문제 값 수정: {key} = {type(value)} -> str")
                                record[key] = str(value) if value is not None else None
                
                print(f"📊 {criteria} 고유값: {sorted(list(set([r[criteria] for r in data if r.get(criteria) is not None])))}")
                return data
                
            except Exception as e:
                print(f"❌ 실제 데이터 처리 오류: {e}")
                print("📊 샘플 데이터로 대체합니다.")
        
        # (샘플 데이터 생성부는 기존 그대로 둠)
        print(f"📊 박스플롯용 샘플 데이터 생성 중 (criteria: {criteria})")
        data = []
        if criteria == "MAIN_EQ":
            criteria_values = ['EQ_001', 'EQ_002', 'EQ_003', 'EQ_004']
        elif criteria == "PARA":
            criteria_values = ['PARA_X', 'PARA_Y', 'PARA_Z']
        elif criteria == "EQ_CHAM":
            criteria_values = ['P0', 'P1', 'P2', 'P3']
        elif criteria == "OPER":
            criteria_values = ['OPER_1', 'OPER_2', 'OPER_3']
        elif criteria == "ROUTE":
            criteria_values = ['ROUTE_A', 'ROUTE_B', 'ROUTE_C']
        else:
            criteria_values = ['DEVICE_A', 'DEVICE_B', 'DEVICE_C']
        
        for i, criteria_val in enumerate(criteria_values):
            base_values = [380 + i*20, 420 + i*20, 460 + i*20]
            for j in range(5):
                key_idx = i * 5 + j + 1
                data.append({
                    'key': f'2024-01-{key_idx:02d} 10:00:00',
                    'FOR_KEY': 'P1931.52926.5',  # 샘플은 그대로
                    criteria: criteria_val,
                    'NO_VAL1': round(base_values[0] + random.uniform(-30, 30), 3),
                    'NO_VAL2': round(base_values[1] + random.uniform(-30, 30), 3),
                    'NO_VAL3': round(base_values[2] + random.uniform(-30, 30), 3),
                    'NO_VAL4': round(base_values[0] + random.uniform(-25, 25), 3),
                    'NO_VAL5': round(base_values[1] + random.uniform(-25, 25), 3),
                    'USL': 550,
                    'LSL': 300,
                    'TGT': 420,
                    'UCL': 500,
                    'LCL': 350
                })
        return data

    @staticmethod
    def generate_rag_search_data() -> Dict:
        """RAG 검색 데이터 생성"""
        return {
            'query': 'PCM 데이터 분석',
            'results': [
                {'title': 'PCM 트렌드 분석 가이드', 'relevance': 0.95, 'content': 'PCM 데이터의 트렌드 분석 방법...'},
                {'title': 'Commonality 분석 기법', 'relevance': 0.88, 'content': 'Commonality 분석을 통한 품질 관리...'},
                {'title': '데이터 시각화 모범 사례', 'relevance': 0.82, 'content': '효과적인 데이터 시각화 방법...'}
            ],
            'total_results': 15,
            'search_time': 0.23
        }

    @staticmethod
    def generate_rag_answer_data() -> List:
        return [
            {
                "file_name": "example1.pdf",
                "file_path": "/static/docs/example1.pdf",
                "similarity": 0.98
            },
            {
                "file_name": "example2.pdf",
                "file_path": "/static/docs/example2.pdf",
                "similarity": 0.92
            },
            {
                "file_name": "example3.pdf",
                "file_path": "/static/docs/example3.pdf",
                "similarity": 0.89
            }
        ]

    @staticmethod
    def generate_pcm_to_trend_data() -> Dict:
        """PCM To Trend 데이터 생성 (실제 마스킹된 엑셀 데이터 또는 샘플 데이터 사용)"""
        # 마스킹된 엑셀 데이터 로드 시도
        DataGenerators.load_masking_data(excel_name='masking_df.xlsx')
        
        global masking_df
        
        # 실제 엑셀 데이터가 있으면 사용
        if masking_df is not None and not masking_df.empty:
            print("📊 실제 마스킹 데이터 사용")
            data = {}
            
            # PARA 컬럼이 있는지 확인
            if 'PARA' in masking_df.columns:
                # PARA별로 데이터 그룹화
                para_groups = masking_df.groupby('PARA')
                for para_name, para_data in para_groups:
                    # 데이터프레임을 딕셔너리 리스트로 변환
                    data[para_name] = para_data.to_dict('records')
                    print(f"📊 PARA {para_name}: {len(para_data)}개 레코드")
            else:
                # PARA 컬럼이 없으면 전체 데이터를 하나의 그룹으로 처리
                data['ALL_DATA'] = masking_df.to_dict('records')
                print(f"📊 전체 데이터: {len(masking_df)}개 레코드")
            
            return data
        
        # 엑셀 파일이 없으면 샘플 데이터 생성
        print("📊 샘플 데이터 생성 (엑셀 파일 없음)")
        data = {}
        para_list = ["PARA_A", "PARA_B", "PARA_C"]
        route_list = ["route1", "route2", "route3"]
        oper_list = ["oper1", "oper2", "oper3", "oper4"]
        
        for para in para_list:
            single = []
            for i in range(1, 16):  # 15개 스텝 데이터 생성
                # 실제 데이터 구조와 동일한 범위로 값 생성
                min_val = round(random.uniform(350, 450), 4)
                max_val = round(random.uniform(600, 700), 4)
                q1_val = round(random.uniform(min_val + 30, min_val + 80), 4)
                q2_val = round(random.uniform(q1_val + 30, q1_val + 80), 4)
                q3_val = round(random.uniform(q2_val + 30, max_val - 30), 4)
                
                single.append({
                    # 마스킹된 컬럼들 (실제로는 ID나 인덱스 정보)
                    'Unnamed: 0.1': i,  # 마스킹된 컬럼 1
                    'Unnamed: 0': i,    # 마스킹된 컬럼 2
                    
                    # 실제 데이터 컬럼들
                    'key': f'{i}',  # 실제 데이터에서는 숫자 형태
                    'MAIN_ROUTE_DESC': random.choice(route_list),
                    'MAIN_OPER_DESC': random.choice(oper_list),
                    'EQ_CHAM': random.choice(['P0', 'P1', 'P2']),
                    'PARA': para,
                    
                    # 통계값들 (실제 데이터 범위 반영)
                    'MIN': min_val,
                    'MAX': max_val,
                    'Q1': q1_val,
                    'Q2': q2_val,
                    'Q3': q3_val,
                    
                    # 제어선들 (실제 데이터 범위 반영)
                    'USL': 550,
                    'TGT': 420,
                    'LSL': 300,
                    'UCL': 500,
                    'LCL': 360
                })
            data[para] = single
        
        # PARA별로 분리된 데이터 반환
        return data

    @staticmethod
    def generate_two_tables_data(test_empty_scenario: str = None) -> Dict:
        """Two Tables 데이터 생성 - 서로 다른 컬럼과 데이터를 가진 두 개의 테이블"""
        # 마스킹된 엑셀 데이터 로드 시도
        DataGenerators.load_masking_data(excel_name='masking_df.xlsx')
        global masking_df
        
        # 첫 번째 테이블: Lot Hold 데이터 (가상의 lot hold 정보)
        lot_hold_data = []
        for i in range(1, 16):
            lot_hold_data.append({
                'LOT_ID': f'LOT_{i:03d}',
                'HOLD_REASON': random.choice(['QUALITY_ISSUE', 'EQUIPMENT_MAINT', 'MATERIAL_SHORTAGE', 'PROCESS_DEVIATION']),
                'HOLD_DATE': f'2024-12-{random.randint(1, 31):02d}',
                'HOLD_STATUS': random.choice(['ACTIVE', 'RELEASED', 'CANCELLED']),
                'PRIORITY': random.choice(['HIGH', 'MEDIUM', 'LOW']),
                'WAFER_COUNT': random.randint(10, 25),
                'AFFECTED_STEP': random.choice(['PHOTO', 'ETCH', 'DIFFUSION', 'METAL']),
                'OWNER': random.choice(['ENGINEER_A', 'ENGINEER_B', 'ENGINEER_C'])
            })
        
        # 두 번째 테이블: PE Confirm Module 데이터 (가상의 PE 확인 모듈 정보)
        pe_confirm_data = []
        for i in range(1, 12):  # 다른 개수로 설정
            pe_confirm_data.append({
                'MODULE_ID': f'PE_MOD_{i:02d}',
                'CONFIRM_STATUS': random.choice(['CONFIRMED', 'PENDING', 'REJECTED']),
                'CONFIRM_DATE': f'2024-12-{random.randint(1, 31):02d}',
                'PARAMETER_NAME': random.choice(['TEMPERATURE', 'PRESSURE', 'FLOW_RATE', 'POWER']),
                'TARGET_VALUE': round(random.uniform(100, 500), 2),
                'ACTUAL_VALUE': round(random.uniform(95, 505), 2),
                'TOLERANCE': round(random.uniform(5, 15), 1),
                'RESULT': random.choice(['PASS', 'FAIL', 'WARNING']),
                'INSPECTOR': random.choice(['INSPECTOR_X', 'INSPECTOR_Y', 'INSPECTOR_Z'])
            })
        
        # 실제 엑셀 데이터가 있으면 첫 번째 테이블에 활용
        if masking_df is not None and not masking_df.empty:
            # 실제 데이터의 일부를 첫 번째 테이블로 사용 (최대 10개 레코드)
            sample_size = min(10, len(masking_df))
            lot_hold_data = masking_df.head(sample_size).to_dict('records')
            print(f"📊 Using real data for lot_hold: {sample_size} records")
        
        # 테스트 시나리오 처리 (특별한 경우에만)
        if test_empty_scenario:
            if test_empty_scenario == 'empty_lot_hold':
                lot_hold_data = []
                print("🔄 Test scenario: Empty lot_hold data")
            elif test_empty_scenario == 'empty_pe_confirm':
                pe_confirm_data = []
                print("🔄 Test scenario: Empty pe_confirm data")
            elif test_empty_scenario == 'both_empty':
                lot_hold_data = []
                pe_confirm_data = []
                print("🔄 Test scenario: Both tables empty")
        
        print(f"📊 Generated data - Lot Hold: {len(lot_hold_data)} records, PE Confirm: {len(pe_confirm_data)} records")
        
        return {
            "result": "lot_hold_pe_confirm_module",
            "real_data": [
                {"lot_hold_module": lot_hold_data},
                {"pe_confirm_module": pe_confirm_data}
            ]
        }
