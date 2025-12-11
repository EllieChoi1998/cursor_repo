# Multiple Graphs Support - Implementation Summary

## 📋 개요

엑셀 데이터 분석 시 사용자 프롬프트에 따라 **같은 그래프 유형에 대해 여러 개의 그래프를 생성**할 수 있도록 프론트엔드를 수정했습니다.

### 예시 사용 케이스

#### Case 1: 카테고리 값별 분리
- **요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"
- **결과:** Tech 종류별로 별도의 라인그래프가 생성됨 (Tech_A, Tech_B, Tech_C)

#### Case 2: 여러 컬럼별 분리
- **요청:** "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드를 라인그래프로 보여줘"
- **결과:** 3개의 그래프 (WIDTH 트렌드, THICKNESS 트렌드, DEPTH 트렌드)

#### Case 3: 특정 값들만 선택
- **요청:** "EQ01, EQ02, EQ03 각각에 대해 WIDTH 분포를 박스플롯으로 보여줘"
- **결과:** 선택된 3개 장비에 대한 박스플롯만 생성

#### Case 4: 조합 패턴
- **요청:** "Tech_A와 B 각각에 대해 CPK와 YIELD 트렌드를 각각 보여줘"
- **결과:** 4개의 그래프 (Tech_A CPK, Tech_A YIELD, Tech_B CPK, Tech_B YIELD)

#### Case 5: 혼합 그래프 타입
- **요청:** "장비별 WIDTH를 박스플롯과 바차트로 각각 보여줘"
- **결과:** 2개의 그래프 (박스플롯, 바차트)

---

## 🎯 핵심 변경사항

### 1. 응답 형식 확장
- **기존:** `graph_spec` (단일 객체)
- **추가:** `graph_specs` (배열) - 여러 그래프 스펙 지원
- **하위 호환성:** 기존 `graph_spec` 형식도 계속 지원

### 2. real_data는 변경 없음
- 모든 데이터는 하나의 `real_data` 배열에 포함
- 각 그래프는 **필터(transforms)** 또는 **다른 encodings**를 사용하여 데이터를 분리/변환

### 3. 유연한 그래프 생성
- ✅ **필터 기반**: 같은 encodings, 다른 filter
- ✅ **Encoding 기반**: 다른 y.field (컬럼별)
- ✅ **조합**: 필터 + 다른 encodings
- ✅ **타입 혼합**: 같은 데이터, 다른 chart_type

### 4. 모든 그래프 유형 지원
- ✅ `bar_graph` - 바차트
- ✅ `line_graph` - 라인차트
- ✅ `box_plot` - 박스플롯
- ✅ `scatter_plot` - 산점도

---

## 📝 수정된 파일

### 1. `/docs/excel_analysis_response_formats.md`
**변경 내용:**
- `graph_specs` 배열 형식 추가 섹션 (2.1)
- 여러 그래프 생성 예시 추가 (4.6)
- 각 그래프는 동일한 `real_data`를 사용하되 다른 필터 적용

**주요 추가 내용:**
```json
{
  "data": {
    "analysis_type": "line_graph",
    "real_data": [ ... ],  // 모든 데이터 포함
    "graph_specs": [       // 여러 그래프 스펙
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" }
        ],
        "layout": { "title": "Tech_A CPK Trend", ... }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" }
        ],
        "layout": { "title": "Tech_B CPK Trend", ... }
      }
    ]
  }
}
```

### 2. `/docs/llm_prompts_for_plotly_spec_generation.md`
**변경 내용:**
- 다중 그래프 출력 형식 가이드 추가
- 다중 그래프 키워드 인식 가이드 추가
- Line Graph 프롬프트에 여러 그래프 생성 예시 추가

**다중 그래프 키워드:**
| 키워드 | 의미 |
|--------|------|
| 각각, 각 | 카테고리별 개별 그래프 |
| 분리, 분리해서 | 분리된 그래프 |
| 별도, 별도로 | 개별 그래프 |
| 나눠서, 나누어 | 나뉜 그래프 |
| ~별로 (Tech별로, 장비별로) | 카테고리별 그래프 |

**LLM 판단 로직:**
```
IF 사용자가 다중 그래프 키워드 사용:
    → graph_specs 배열 생성
    → 각 카테고리별로 필터 적용한 개별 스펙 생성
    → 각 스펙의 title에 카테고리명 포함
ELSE:
    → 단일 graph_spec 생성 (기존 방식)
```

### 3. `/src/App.vue` - Template 수정

**변경 위치 1: 일반 결과 표시 (478-521 라인)**
```vue
<!-- Multiple Graphs (graph_specs array) -->
<div v-if="result.graphSpecs && result.graphSpecs.length > 0" class="multiple-graphs-container">
  <div 
    v-for="(graphSpec, graphIndex) in result.graphSpecs" 
    :key="`${result.id}-graph-${graphIndex}`"
    class="single-graph-wrapper"
  >
    <PlotlyGraph
      :graph-spec="graphSpec"
      :title="graphSpec?.layout?.title?.text || graphSpec?.layout?.title || `Graph ${graphIndex + 1}`"
      :file-name="result.fileName"
      :success-message="''"
      :height="chartHeight"
    />
  </div>
</div>

<!-- Single Graph (legacy graph_spec) -->
<div v-else class="single-graph-wrapper">
  <PlotlyGraph
    :graph-spec="result.graphSpec"
    :title="result.title"
    :file-name="result.fileName"
    :success-message="''"
    :height="chartHeight"
  />
</div>
```

**변경 위치 2: Fullscreen 모드 (789-830 라인)**
- 동일한 로직으로 여러 그래프 지원

### 4. `/src/App.vue` - Script 수정

**변경 위치: `createResultFromResponseData` 함수 (2084-2140 라인)**

```javascript
// Check if multiple graph specs are provided (graph_specs array)
let graphSpec = null
let graphSpecs = null

if (hasGraphSpec) {
  if (responseData.graph_specs && Array.isArray(responseData.graph_specs) && responseData.graph_specs.length > 0) {
    // Multiple graphs: build each spec in the array
    console.log('📊 Processing multiple graph_specs:', responseData.graph_specs.length)
    graphSpecs = responseData.graph_specs.map((spec, index) => {
      const built = buildGraphSpec(spec, realDataSets)
      console.log(`📊 Built graphSpec ${index}:`, built)
      return built
    }).filter(spec => spec !== null)
    
    console.log('📊 graphSpecs after build:', graphSpecs.length, 'specs')
  } else if (responseData.graph_spec) {
    // Single graph: use legacy graph_spec
    console.log('📊 Processing single graph_spec')
    graphSpec = buildGraphSpec(responseData.graph_spec, realDataSets)
  }
}

result = {
  // ... other fields
  graphSpec,       // 단일 그래프 (legacy)
  graphSpecs,      // 여러 그래프 (new)
  // ...
}
```

### 5. `/src/App.vue` - CSS 수정

**추가된 스타일:**
```css
/* Multiple Graphs Container */
.multiple-graphs-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
}

.single-graph-wrapper {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.single-graph-wrapper:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
}

/* Fullscreen Multiple Graphs */
.fullscreen-multiple-graphs {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  padding: 1rem;
}

.fullscreen-single-graph {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
```

---

## 🔧 백엔드 적용 가이드

### 핵심 개념: Template vs Direct Array

#### ⭐ Template Approach (권장 - 카테고리 값별 분리)
**문제:** LLM이 고유값을 모름 (Tech 컬럼에 몇 개의 값이 있는지, 값이 무엇인지)
**해결:** LLM은 템플릿만 생성, Backend가 실제 값 추출 후 확장

#### Direct Array Approach (컬럼별 분리)
**문제 없음:** 컬럼명은 메타데이터로 제공됨
**방식:** LLM이 직접 graph_specs 배열 생성

---

### 1. 단일 그래프 응답 (기존 방식, 변경 없음)
```python
response_data = {
    "analysis_type": "line_graph",
    "real_data": [all_data],
    "graph_spec": {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "encodings": { ... },
        "layout": { ... }
    }
}
```

### 2. 여러 그래프 응답 - 방법별 가이드

#### 방법 A: 카테고리 값별 분리 (Template-based) ⭐ RECOMMENDED

**문제:** LLM은 Tech 컬럼에 어떤 값들이 있는지 모름 (값이 100개일 수도 있음)
**해결:** LLM은 템플릿만 생성, Backend가 고유값 추출 후 확장

```python
# "각 Tech별로 CPK 트렌드를 분리해서"

# Step 1: LLM이 템플릿 생성 (값을 몰라도 됨)
llm_response = {
    "graph_spec_template": {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "split_by": "TECH",  # 이 컬럼으로 분리
        "dataset_index": 0,
        "encodings": {
            "x": {"field": "DATE", "type": "temporal"},
            "y": {"field": "CPK", "type": "quantitative"}
        },
        "transforms": [
            {"type": "filter", "field": "TECH", "op": "==", "value": "{{SPLIT_VALUE}}"},
            {"type": "sort", "field": "DATE", "direction": "asc"}
        ],
        "layout": {
            "title": "{{SPLIT_VALUE}} CPK Trend",
            "height": 400
        }
    }
}

# Step 2: Backend가 템플릿 확장
def expand_graph_spec_template(template, df):
    """템플릿을 고유값별로 확장"""
    split_column = template.pop("split_by")  # "TECH"
    unique_values = df[split_column].unique()[:10]  # 최대 10개 제한
    
    graph_specs = []
    for value in unique_values:
        # 템플릿 복사
        spec = copy.deepcopy(template)
        
        # {{SPLIT_VALUE}} 플레이스홀더 치환
        spec_str = json.dumps(spec)
        spec_str = spec_str.replace("{{SPLIT_VALUE}}", str(value))
        spec = json.loads(spec_str)
        
        graph_specs.append(spec)
    
    return graph_specs

# Step 3: 최종 응답
if "graph_spec_template" in llm_response:
    graph_specs = expand_graph_spec_template(
        llm_response["graph_spec_template"], 
        df
    )
    response_data = {
        "analysis_type": "line_graph",
        "real_data": [df.to_dict("records")],
        "graph_specs": graph_specs,  # 확장된 배열
        "success_message": f"✅ {len(graph_specs)}개의 라인차트 생성 완료"
    }
```

**장점:**
- ✅ LLM은 고유값을 몰라도 됨 (프롬프트 토큰 절약)
- ✅ 고유값이 100개여도 문제없음
- ✅ Backend에서 개수 제한 가능 (성능 관리)
- ✅ LLM 프롬프트 심플화
```

#### 방법 B: 여러 Y축 컬럼별 분리 (Encoding-based)
```python
# "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드"
y_columns = ["WIDTH", "THICKNESS", "DEPTH"]

graph_specs = []
for col in y_columns:
    spec = {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
            "x": {"field": "DATE", "type": "temporal"},
            "y": {"field": col, "type": "quantitative"},
            "series": {"field": "EQ"}  # 장비별로 색상 구분
        },
        "transforms": [
            {"type": "sort", "field": "DATE", "direction": "asc"}
        ],
        "layout": {
            "title": f"{col} Trend by Equipment",
            "height": 400,
            "yaxis": {"title": f"{col} (μm)"}
        }
    }
    graph_specs.append(spec)

response_data = {
    "analysis_type": "line_graph",
    "real_data": [df.to_dict("records")],
    "graph_specs": graph_specs,
    "success_message": f"✅ {len(y_columns)}개의 파라미터 트렌드 차트 생성 완료"
}
```

#### 방법 C: 특정 값들만 선택 (Selective Filter)
```python
# "EQ01, EQ02, EQ03 각각에 대해 WIDTH 분포"
selected_equipments = ["EQ01", "EQ02", "EQ03"]

graph_specs = []
for eq in selected_equipments:
    spec = {
        "schema_version": "1.0",
        "chart_type": "box_plot",
        "dataset_index": 0,
        "encodings": {
            "category": {"field": "EQ"},
            "value": {"field": "WIDTH"}
        },
        "transforms": [
            {"type": "filter", "field": "EQ", "op": "==", "value": eq}
        ],
        "layout": {
            "title": f"{eq} WIDTH Distribution",
            "height": 400
        },
        "boxpoints": "outliers"
    }
    graph_specs.append(spec)

response_data = {
    "analysis_type": "box_plot",
    "real_data": [df.to_dict("records")],
    "graph_specs": graph_specs,
    "success_message": "✅ 3개 장비 박스플롯 생성 완료"
}
```

#### 방법 D: 조합 패턴 (Filter + Different Encodings)
```python
# "Tech_A와 B 각각에 대해 CPK와 YIELD 트렌드를 각각"
techs = ["Tech_A", "Tech_B"]
metrics = ["CPK", "YIELD"]

graph_specs = []
for tech in techs:
    for metric in metrics:
        spec = {
            "schema_version": "1.0",
            "chart_type": "line_graph",
            "dataset_index": 0,
            "encodings": {
                "x": {"field": "DATE", "type": "temporal"},
                "y": {"field": metric, "type": "quantitative"}
            },
            "transforms": [
                {"type": "filter", "field": "TECH", "op": "==", "value": tech},
                {"type": "sort", "field": "DATE", "direction": "asc"}
            ],
            "layout": {
                "title": f"{tech} {metric} Trend",
                "height": 400,
                "yaxis": {
                    "title": metric,
                    "range": [0.8, 2.0] if metric == "CPK" else [95, 100]
                }
            }
        }
        graph_specs.append(spec)

response_data = {
    "analysis_type": "line_graph",
    "real_data": [df.to_dict("records")],
    "graph_specs": graph_specs,
    "success_message": f"✅ {len(techs)}개 Tech × {len(metrics)}개 지표 = {len(graph_specs)}개 차트 생성 완료"
}
```

### 3. LLM 프롬프트 처리
```python
def should_create_multiple_graphs(user_request: str) -> bool:
    """사용자 요청에서 다중 그래프 키워드 감지"""
    keywords = ["각각", "각", "분리", "별도", "나눠서", "개별"]
    return any(keyword in user_request for keyword in keywords)

def generate_graph_specs(df, user_request, column_metadata):
    """LLM을 사용하여 graph_spec(s) 생성"""
    
    if should_create_multiple_graphs(user_request):
        # 다중 그래프 생성 프롬프트 사용
        prompt = get_multiple_graphs_prompt(
            column_metadata=column_metadata,
            user_request=user_request
        )
        # LLM 응답은 graph_specs 배열
        llm_response = call_llm_api(prompt)
        return {
            "graph_specs": llm_response["graph_specs"]
        }
    else:
        # 단일 그래프 생성 프롬프트 사용
        prompt = get_single_graph_prompt(
            column_metadata=column_metadata,
            user_request=user_request
        )
        # LLM 응답은 graph_spec 객체
        llm_response = call_llm_api(prompt)
        return {
            "graph_spec": llm_response["graph_spec"]
        }
```

---

## ✅ 테스트 시나리오

### 시나리오 1: 단일 그래프 (기존 방식)
**요청:** "날짜별 CPK 트렌드를 라인차트로 보여줘"
**응답:** `graph_spec` 사용
**방식:** 단일 그래프, series로 구분
**결과:** 1개의 라인차트 (모든 데이터 포함)

### 시나리오 2: 카테고리 값별 분리
**요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"
**응답:** `graph_specs` 배열 (3개 스펙)
**방식:** Filter-based (각 Tech 값으로 필터)
**결과:** 3개의 라인차트 (Tech_A, Tech_B, Tech_C)

### 시나리오 3: 여러 Y축 컬럼별
**요청:** "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드"
**응답:** `graph_specs` 배열 (3개 스펙)
**방식:** Encoding-based (다른 y.field)
**결과:** 3개의 라인차트 (각각 다른 측정값)

### 시나리오 4: 특정 값 선택
**요청:** "EQ01, EQ02, EQ03 각각에 대해 WIDTH 분포를 박스플롯으로"
**응답:** `graph_specs` 배열 (3개 스펙)
**방식:** Selective Filter (명시된 값들만)
**결과:** 3개의 박스플롯 (선택된 장비만)

### 시나리오 5: 조합 패턴
**요청:** "Tech_A와 B 각각에 대해 CPK와 YIELD 트렌드를 각각"
**응답:** `graph_specs` 배열 (4개 스펙)
**방식:** Filter + Different Encodings (2 techs × 2 metrics)
**결과:** 4개의 라인차트 (Tech_A CPK, Tech_A YIELD, Tech_B CPK, Tech_B YIELD)

### 시나리오 6: 혼합 그래프 타입
**요청:** "장비별 WIDTH를 박스플롯과 바차트로 각각"
**응답:** `graph_specs` 배열 (2개 스펙, 다른 chart_type)
**방식:** Different chart_type
**결과:** 2개의 그래프 (박스플롯 1개, 바차트 1개)

---

## 📊 프론트엔드 렌더링 방식

### 일반 보기
- 여러 그래프가 **세로로 스택**되어 표시
- 각 그래프는 개별 카드 형태 (테두리, 그림자)
- hover 시 시각적 피드백 제공

### Fullscreen 모드
- 동일하게 세로 스택 레이아웃
- 각 그래프 높이: 800px
- 스크롤 가능

### 데이터 테이블
- 여러 그래프 아래에 `real_data` 테이블 표시
- 모든 그래프가 공유하는 데이터셋

---

## 🎨 사용자 경험 개선

### Before (기존)
- "Tech별로 CPK 보여줘" → 하나의 그래프에 여러 라인 (series 사용)
- 많은 카테고리가 있으면 그래프가 복잡해짐

### After (개선)
- "각 Tech별로 CPK를 분리해서 보여줘" → 각 Tech마다 독립적인 그래프
- 각 그래프에 명확한 제목
- 개별 그래프로 트렌드 비교가 용이

---

## 🔍 주의사항

### 1. 백엔드 수정 금지
- ⚠️ 백엔드 코드는 수정하지 않았습니다
- ✅ 프론트엔드만 수정하여 하위 호환성 유지
- ✅ 기존 `graph_spec` 응답도 정상 작동

### 2. real_data 변경 없음
- ⚠️ `real_data`는 항상 모든 데이터 포함
- ✅ 각 그래프는 필터로 데이터 분리
- ✅ 데이터 중복 없음 (효율적)

### 3. 성능 고려
- 그래프가 많아질수록 렌더링 시간 증가
- 권장: 최대 10개 이하의 그래프
- 너무 많은 카테고리는 다른 방식 권장 (페이지네이션 등)

---

## 📚 참고 문서

1. `/docs/excel_analysis_response_formats.md` - API 응답 형식 전체 가이드
2. `/docs/llm_prompts_for_plotly_spec_generation.md` - LLM 프롬프트 템플릿
3. `/src/components/PlotlyGraph.vue` - PlotlyGraph 컴포넌트 (수정 없음)
4. `/src/App.vue` - 메인 애플리케이션 (수정됨)

---

## 🚀 다음 단계

### 백엔드 개발자가 할 일
1. `docs/llm_prompts_for_plotly_spec_generation.md`의 프롬프트 템플릿 확인
2. 다중 그래프 키워드 감지 로직 구현
3. LLM API 호출 시 적절한 프롬프트 선택
4. `graph_specs` 배열 생성 로직 구현
5. 테스트 및 검증

### 프론트엔드 개발자가 할 일
- ✅ 완료! 추가 작업 없음
- 백엔드에서 `graph_specs` 응답을 보내면 자동으로 여러 그래프 렌더링

---

## 📞 문의

구현 관련 질문이나 이슈가 있으면 이 문서와 함께 수정된 파일들을 참고하세요.

**수정된 파일:**
- `/docs/excel_analysis_response_formats.md`
- `/docs/llm_prompts_for_plotly_spec_generation.md`
- `/src/App.vue` (template, script, style)
- `/docs/SUMMARY_multiple_graphs_support.md` (이 문서)

**Date:** 2025-12-05
**Version:** 1.0
