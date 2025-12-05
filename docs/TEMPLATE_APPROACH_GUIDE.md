# Template Approach for Multiple Graph Generation

## 📋 개요

**문제점:**
- 사용자: "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"
- LLM: Tech 컬럼에 어떤 값들이 있는지 모름 (Tech_A, Tech_B, ...?)
- 메타데이터에 고유값을 모두 포함하기엔 너무 많을 수 있음 (100개 이상)
- 프롬프트 토큰 제한

**해결책: Template Approach**
- LLM: 템플릿 1개 생성 + `split_by` 필드 지정 + `{{SPLIT_VALUE}}` 플레이스홀더 사용
- Backend: 실제 고유값 추출 → 템플릿 확장 → `graph_specs` 배열 생성
- Frontend: 확장된 `graph_specs` 배열 렌더링

---

## 🎯 두 가지 접근 방식 비교

### Option A: Template Approach ⭐ RECOMMENDED (카테고리 값별 분리)

**Use case:** "각 Tech별로", "각 장비별로", "각 DEVICE마다"

| 역할 | 책임 |
|------|------|
| LLM | 템플릿 1개 생성 + `split_by` 지정 |
| Backend | 고유값 추출 + 템플릿 확장 → `graph_specs` |
| Frontend | `graph_specs` 배열 렌더링 |

**장점:**
- ✅ LLM은 고유값을 몰라도 됨
- ✅ 토큰 절약
- ✅ 고유값이 100개여도 문제없음
- ✅ Backend에서 개수 제한 가능

**단점:**
- ❌ Backend 처리 로직 추가 필요
- ❌ 플레이스홀더 치환 로직 구현 필요

### Option B: Direct Array Approach (컬럼별 분리)

**Use case:** "WIDTH, THICKNESS, DEPTH 각각"

| 역할 | 책임 |
|------|------|
| LLM | `graph_specs` 배열 직접 생성 (모든 스펙 포함) |
| Backend | LLM 응답 그대로 사용 |
| Frontend | `graph_specs` 배열 렌더링 |

**장점:**
- ✅ Backend 처리 간단
- ✅ LLM이 직접 제어

**단점:**
- ❌ 컬럼명이 많으면 LLM 응답 길어짐
- ❌ 값별 분리에는 사용 불가

---

## 📝 Template Approach 상세 가이드

### 1. LLM Response Format

```json
{
  "data": {
    "analysis_type": "line_graph",
    "real_data": [ ... ],  // 모든 데이터 포함
    "graph_spec_template": {
      "schema_version": "1.0",
      "chart_type": "line_graph",
      "split_by": "TECH",  // 이 컬럼으로 분리
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "DATE", "type": "temporal" },
        "y": { "field": "CPK", "type": "quantitative" }
      },
      "transforms": [
        { 
          "type": "filter", 
          "field": "TECH", 
          "op": "==", 
          "value": "{{SPLIT_VALUE}}"  // 플레이스홀더
        },
        { "type": "sort", "field": "DATE", "direction": "asc" }
      ],
      "layout": {
        "title": "{{SPLIT_VALUE}} CPK Trend",  // 플레이스홀더
        "height": 400
      }
    }
  }
}
```

**Key Fields:**
- `graph_spec_template`: 템플릿 객체 (graph_specs가 아님!)
- `split_by`: 분리 기준 컬럼명
- `{{SPLIT_VALUE}}`: 실제 값으로 치환될 플레이스홀더

### 2. Backend Processing Logic

```python
import json
import copy

def expand_graph_spec_template(response_data, df):
    """
    graph_spec_template을 graph_specs 배열로 확장
    
    Args:
        response_data: LLM 응답 데이터
        df: pandas DataFrame (실제 데이터)
    
    Returns:
        수정된 response_data (graph_specs 포함)
    """
    # 1. 템플릿 추출
    if "graph_spec_template" not in response_data:
        return response_data  # 템플릿 없으면 그대로 반환
    
    template = response_data["graph_spec_template"]
    
    # 2. split_by 컬럼 추출
    if "split_by" not in template:
        # split_by가 없으면 단일 스펙으로 처리
        response_data["graph_spec"] = template
        del response_data["graph_spec_template"]
        return response_data
    
    split_column = template["split_by"]
    
    # 3. 고유값 추출 (최대 10개로 제한)
    if split_column not in df.columns:
        raise ValueError(f"Column '{split_column}' not found in dataframe")
    
    unique_values = df[split_column].unique()
    
    # 성능을 위해 최대 10개로 제한
    MAX_GRAPHS = 10
    if len(unique_values) > MAX_GRAPHS:
        print(f"Warning: {len(unique_values)} unique values found, limiting to {MAX_GRAPHS}")
        unique_values = unique_values[:MAX_GRAPHS]
    
    # 4. 각 값에 대해 스펙 생성
    graph_specs = []
    
    for value in unique_values:
        # 템플릿 복사 (deep copy)
        spec = copy.deepcopy(template)
        
        # split_by 필드 제거 (프론트엔드에 불필요)
        if "split_by" in spec:
            del spec["split_by"]
        
        # {{SPLIT_VALUE}} 플레이스홀더 치환
        spec_str = json.dumps(spec)
        spec_str = spec_str.replace("{{SPLIT_VALUE}}", str(value))
        spec = json.loads(spec_str)
        
        graph_specs.append(spec)
    
    # 5. 응답 데이터 수정
    response_data["graph_specs"] = graph_specs
    del response_data["graph_spec_template"]
    
    # Success 메시지 업데이트
    response_data["success_message"] = (
        f"✅ {len(graph_specs)}개의 {response_data['analysis_type']} 생성 완료"
    )
    
    return response_data


# 사용 예시
def process_llm_response(llm_response, df):
    """LLM 응답 후처리"""
    response_data = llm_response.get("data", {})
    
    # 템플릿 확장
    response_data = expand_graph_spec_template(response_data, df)
    
    return {"data": response_data}
```

### 3. Complete Backend Flow

```python
from typing import Dict, Any
import pandas as pd

def generate_excel_analysis_response(
    df: pd.DataFrame,
    user_request: str,
    llm_api_func
) -> Dict[str, Any]:
    """
    엑셀 데이터 분석 응답 생성 (템플릿 지원)
    
    Args:
        df: pandas DataFrame
        user_request: 사용자 요청
        llm_api_func: LLM API 호출 함수
    
    Returns:
        프론트엔드로 전송할 최종 응답
    """
    # 1. 메타데이터 추출
    column_metadata = extract_column_metadata(df)
    sample_data = df.head(5).to_dict('records')
    
    # 2. 다중 그래프 여부 판단
    is_multiple = should_create_multiple_graphs(user_request, column_metadata)
    
    # 3. LLM 프롬프트 생성
    if is_multiple:
        # 값별 분리인지 컬럼별 분리인지 판단
        if is_value_based_split(user_request):
            prompt = get_template_prompt(column_metadata, user_request)
        else:
            prompt = get_array_prompt(column_metadata, user_request)
    else:
        prompt = get_single_graph_prompt(column_metadata, user_request)
    
    # 4. LLM API 호출
    llm_response = llm_api_func(prompt)
    
    # 5. 응답 파싱
    response_data = {
        "analysis_type": llm_response.get("chart_type", "line_graph"),
        "real_data": [df.to_dict("records")],
        "file_name": "analysis.xlsx",
        "summary": llm_response.get("summary", ""),
        "success_message": "✅ 분석 완료"
    }
    
    # 6. graph_spec_template 또는 graph_specs 추가
    if "graph_spec_template" in llm_response:
        response_data["graph_spec_template"] = llm_response["graph_spec_template"]
    elif "graph_specs" in llm_response:
        response_data["graph_specs"] = llm_response["graph_specs"]
    elif "graph_spec" in llm_response:
        response_data["graph_spec"] = llm_response["graph_spec"]
    
    # 7. 템플릿 확장 (있는 경우)
    response_data = expand_graph_spec_template(response_data, df)
    
    # 8. 최종 응답 반환
    return {"data": response_data}


def should_create_multiple_graphs(user_request: str, metadata: dict) -> bool:
    """다중 그래프 생성 여부 판단"""
    keywords = ["각각", "각", "분리", "별도", "나눠서", "개별", "따로"]
    return any(keyword in user_request for keyword in keywords)


def is_value_based_split(user_request: str) -> bool:
    """값별 분리 (템플릿 필요) vs 컬럼별 분리 (배열 직접 생성)"""
    # "각 XXX별로" 패턴 → 값별 분리
    value_patterns = ["별로", "마다", "각각"]
    
    # "WIDTH, THICKNESS" 같이 컬럼 나열 → 컬럼별 분리
    column_patterns = [",", "와", "과", "그리고"]
    
    has_value_pattern = any(p in user_request for p in value_patterns)
    has_column_pattern = any(p in user_request for p in column_patterns)
    
    # 값별 패턴이 있고 컬럼 나열이 없으면 값별 분리
    return has_value_pattern and not has_column_pattern
```

### 4. Placeholder Replacement Rules

**지원하는 플레이스홀더:**

| 플레이스홀더 | 설명 | 예시 |
|-------------|------|------|
| `{{SPLIT_VALUE}}` | split_by 컬럼의 실제 값 | "Tech_A", "EQ01" |
| `{{SPLIT_COLUMN}}` | split_by 컬럼명 | "TECH", "EQ" |

**치환 위치:**
- ✅ `transforms[].value`
- ✅ `layout.title`
- ✅ `layout.xaxis.title`
- ✅ `layout.yaxis.title`
- ✅ 기타 모든 문자열 필드

**예시:**
```json
// Before (template)
{
  "title": "{{SPLIT_VALUE}} Analysis for {{SPLIT_COLUMN}}",
  "transforms": [
    { "field": "TECH", "value": "{{SPLIT_VALUE}}" }
  ]
}

// After (TECH = "Tech_A")
{
  "title": "Tech_A Analysis for TECH",
  "transforms": [
    { "field": "TECH", "value": "Tech_A" }
  ]
}
```

---

## 🚀 실전 예시

### 예시 1: 카테고리 값별 분리

**사용자 요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"

**LLM 응답:**
```json
{
  "graph_spec_template": {
    "split_by": "TECH",
    "chart_type": "line_graph",
    "encodings": {
      "x": { "field": "DATE" },
      "y": { "field": "CPK" }
    },
    "transforms": [
      { "type": "filter", "field": "TECH", "op": "==", "value": "{{SPLIT_VALUE}}" }
    ],
    "layout": {
      "title": "{{SPLIT_VALUE}} CPK Trend"
    }
  }
}
```

**Backend 처리:**
```python
df["TECH"].unique()  # ['Tech_A', 'Tech_B', 'Tech_C']

# 템플릿 확장 결과
graph_specs = [
  { "chart_type": "line_graph", "transforms": [{"value": "Tech_A"}], "layout": {"title": "Tech_A CPK Trend"} },
  { "chart_type": "line_graph", "transforms": [{"value": "Tech_B"}], "layout": {"title": "Tech_B CPK Trend"} },
  { "chart_type": "line_graph", "transforms": [{"value": "Tech_C"}], "layout": {"title": "Tech_C CPK Trend"} }
]
```

**Frontend 렌더링:** 3개의 라인그래프

---

### 예시 2: 컬럼별 분리 (템플릿 불필요)

**사용자 요청:** "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드"

**LLM 응답:** (템플릿 없이 직접 배열)
```json
{
  "graph_specs": [
    { "encodings": { "y": { "field": "WIDTH" } }, "layout": { "title": "WIDTH Trend" } },
    { "encodings": { "y": { "field": "THICKNESS" } }, "layout": { "title": "THICKNESS Trend" } },
    { "encodings": { "y": { "field": "DEPTH" } }, "layout": { "title": "DEPTH Trend" } }
  ]
}
```

**Backend 처리:** 그대로 사용 (변환 불필요)

**Frontend 렌더링:** 3개의 라인그래프

---

## ⚙️ 설정 및 최적화

### 성능 고려사항

```python
# config.py
MAX_GRAPHS_PER_REQUEST = 10  # 최대 그래프 개수 제한
TEMPLATE_CACHE_TTL = 300      # 템플릿 캐시 TTL (초)
UNIQUE_VALUES_LIMIT = 15      # 고유값 제한 (경고 표시)

def expand_graph_spec_template_optimized(response_data, df, config):
    """최적화된 템플릿 확장"""
    template = response_data["graph_spec_template"]
    split_column = template["split_by"]
    
    # 1. 고유값 개수 체크
    unique_values = df[split_column].unique()
    
    if len(unique_values) > config.UNIQUE_VALUES_LIMIT:
        # 경고 로그 + 상위 N개만 선택
        logger.warning(
            f"Too many unique values ({len(unique_values)}) for column '{split_column}'. "
            f"Limiting to top {config.MAX_GRAPHS_PER_REQUEST}."
        )
        # 빈도수 기준 상위 N개 선택
        top_values = df[split_column].value_counts().head(config.MAX_GRAPHS_PER_REQUEST).index
        unique_values = top_values
    else:
        unique_values = unique_values[:config.MAX_GRAPHS_PER_REQUEST]
    
    # 2. 템플릿 확장
    # ... (동일)
```

### 에러 처리

```python
def expand_graph_spec_template_safe(response_data, df):
    """에러 처리 포함 템플릿 확장"""
    try:
        if "graph_spec_template" not in response_data:
            return response_data
        
        template = response_data["graph_spec_template"]
        
        # split_by 검증
        if "split_by" not in template:
            logger.error("Missing 'split_by' field in template")
            # Fallback: 단일 그래프로 변환
            response_data["graph_spec"] = template
            del response_data["graph_spec_template"]
            return response_data
        
        split_column = template["split_by"]
        
        # 컬럼 존재 여부 검증
        if split_column not in df.columns:
            logger.error(f"Column '{split_column}' not found in dataframe")
            # Fallback: 에러 메시지 반환
            response_data["error"] = f"컬럼 '{split_column}'을 찾을 수 없습니다."
            return response_data
        
        # 정상 처리
        return expand_graph_spec_template(response_data, df)
        
    except Exception as e:
        logger.exception("Error expanding template")
        response_data["error"] = f"그래프 생성 중 오류 발생: {str(e)}"
        return response_data
```

---

## 📚 참고 자료

- [excel_analysis_response_formats.md](./excel_analysis_response_formats.md) - 응답 형식 전체 가이드
- [llm_prompts_for_plotly_spec_generation.md](./llm_prompts_for_plotly_spec_generation.md) - LLM 프롬프트 템플릿
- [SUMMARY_multiple_graphs_support.md](./SUMMARY_multiple_graphs_support.md) - 다중 그래프 지원 요약

---

**작성일:** 2025-12-05  
**버전:** 1.0
