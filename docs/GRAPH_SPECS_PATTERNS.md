# Graph Specs Patterns - 간단 정리

## 패턴 1: 값별 분리 (split_by 사용)

**요청:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프"

**LLM 응답:**
```json
{
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

**Backend 처리:**
```python
# Tech 컬럼의 고유값: ["Tech_A", "Tech_B", "Tech_C"]
# → 3개의 graph_spec 생성 (각각 Tech_A, Tech_B, Tech_C로 필터링)
```

---

## 패턴 2: 컬럼별 분리 (graph_specs 배열 직접)

**요청:** "WIDTH, THICKNESS, DEPTH 각각에 대해 트렌드"

**LLM 응답:**
```json
{
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

**Backend 처리:**
```python
# 그대로 사용 (변환 불필요)
```

---

## 요약

| 케이스 | LLM 응답 필드 | Backend 처리 |
|--------|--------------|--------------|
| **값별 분리** | `graph_spec_template` + `split_by` | 고유값 추출 → 템플릿 확장 |
| **컬럼별 분리** | `graph_specs` 배열 | 그대로 사용 |
