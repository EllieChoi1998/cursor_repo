# Graph Specs Patterns - 간단 정리

## 패턴 1: 값별 분리 (split_by 사용)

**요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프"

**Backend 응답:**
```json
{
  "analysis_type": "line_graph",
  "real_data": [...],
  "graph_spec_template": {
    "split_by": "TECH",
    "chart_type": "line_graph",
    "encodings": {
      "x": {"field": "DATE", "type": "temporal"},
      "y": {"field": "CPK", "type": "quantitative"}
    },
    "transforms": [
      {"type": "filter", "field": "TECH", "op": "==", "value": "{{SPLIT_VALUE}}"}
    ],
    "layout": {
      "title": "{{SPLIT_VALUE}} CPK Trend"
    }
  }
}
```

**Frontend 처리:**
```javascript
// 1. real_data에서 TECH 컬럼의 고유값 추출: ["Tech_A", "Tech_B", "Tech_C"]
// 2. 각 값마다 템플릿 복사 & {{SPLIT_VALUE}} 치환
// 3. graphSpecs 배열 생성 → 3개 그래프 렌더링
```

**모든 그래프 타입 지원:** `bar_graph`, `line_graph`, `box_plot`, `scatter_plot`

---

## 패턴 2: 컬럼별 분리 (graph_specs 배열 직접)

**요청:** "WIDTH, THICKNESS, DEPTH 각각에 대해 트렌드"

**Backend 응답:**
```json
{
  "analysis_type": "line_graph",
  "real_data": [...],
  "graph_specs": [
    {
      "chart_type": "line_graph",
      "encodings": {
        "x": {"field": "DATE", "type": "temporal"},
        "y": {"field": "WIDTH", "type": "quantitative"}
      },
      "layout": {"title": "WIDTH Trend"}
    },
    {
      "chart_type": "line_graph",
      "encodings": {
        "x": {"field": "DATE", "type": "temporal"},
        "y": {"field": "THICKNESS", "type": "quantitative"}
      },
      "layout": {"title": "THICKNESS Trend"}
    },
    {
      "chart_type": "line_graph",
      "encodings": {
        "x": {"field": "DATE", "type": "temporal"},
        "y": {"field": "DEPTH", "type": "quantitative"}
      },
      "layout": {"title": "DEPTH Trend"}
    }
  ]
}
```

**Frontend 처리:**
```javascript
// 그대로 렌더링 (변환 불필요)
```

---

## 요약

| 케이스 | Backend 응답 | Frontend 처리 |
|--------|-------------|---------------|
| **값별 분리** | `graph_spec_template` + `split_by` | 고유값 추출 → 템플릿 확장 |
| **컬럼별 분리** | `graph_specs` 배열 | 그대로 렌더링 |

**핵심:**
- Backend는 템플릿만 전송 (고유값 추출 불필요)
- Frontend가 real_data 기반으로 동적 확장
- 모든 그래프 타입에 동일하게 적용
