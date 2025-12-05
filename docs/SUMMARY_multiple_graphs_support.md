# Multiple Graphs Support - Implementation Summary

## 📋 개요

엑셀 데이터 분석 시 사용자 프롬프트에 따라 **같은 그래프 유형에 대해 여러 개의 그래프를 생성**할 수 있도록 프론트엔드를 수정했습니다.

### 예시 사용 케이스
- **사용자 요청:** "각 Tech별로 A컬럼에 대한 트렌드를 분리해서 라인그래프 보여줘"
- **결과:** Tech 종류별로 별도의 라인그래프가 생성됨 (Tech_A, Tech_B, Tech_C 등)

---

## 🎯 핵심 변경사항

### 1. 응답 형식 확장
- **기존:** `graph_spec` (단일 객체)
- **추가:** `graph_specs` (배열) - 여러 그래프 스펙 지원
- **하위 호환성:** 기존 `graph_spec` 형식도 계속 지원

### 2. real_data는 변경 없음
- 모든 데이터는 하나의 `real_data` 배열에 포함
- 각 그래프는 **필터(transforms)**를 사용하여 데이터를 분리

### 3. 모든 그래프 유형 지원
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

### 2. 여러 그래프 응답 (새 방식)
```python
# 1. 데이터에서 고유 카테고리 추출
unique_techs = df["TECH"].unique()

# 2. 각 카테고리별로 graph_spec 생성
graph_specs = []
for tech in unique_techs:
    spec = {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
            "x": {"field": "DATE", "type": "temporal"},
            "y": {"field": "CPK", "type": "quantitative"}
        },
        "transforms": [
            {"type": "filter", "field": "TECH", "op": "==", "value": tech},
            {"type": "sort", "field": "DATE", "direction": "asc"}
        ],
        "layout": {
            "title": f"{tech} CPK Trend",
            "height": 400,
            "margin": {"l": 80, "r": 80, "t": 100, "b": 150},
            # ... 기타 레이아웃 설정
        }
    }
    graph_specs.append(spec)

# 3. 응답 데이터 구성
response_data = {
    "analysis_type": "line_graph",
    "real_data": [df.to_dict("records")],  # 모든 데이터 포함
    "graph_specs": graph_specs,             # graph_spec이 아닌 graph_specs!
    "success_message": f"✅ {len(unique_techs)}개의 라인차트 생성 완료"
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
**결과:** 1개의 라인차트 표시

### 시나리오 2: 여러 그래프 (새 방식)
**요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"
**응답:** `graph_specs` 배열 사용 (3개 스펙)
**결과:** 3개의 라인차트 표시 (Tech_A, Tech_B, Tech_C)

### 시나리오 3: 여러 그래프 - 바차트
**요청:** "장비별로 불량 개수를 개별 바차트로 보여줘"
**응답:** `graph_specs` 배열 사용
**결과:** 장비 수만큼 바차트 표시

### 시나리오 4: 여러 그래프 - 박스플롯
**요청:** "각 DEVICE마다 WIDTH 분포를 별도 박스플롯으로"
**응답:** `graph_specs` 배열 사용
**결과:** DEVICE 수만큼 박스플롯 표시

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
