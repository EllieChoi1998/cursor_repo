# Graph Spec Pattern - 항상 배열

Backend는 항상 `graph_spec`을 **배열**로 보냄. Frontend가 자동 판단.

---

## 패턴 1: 템플릿 (split_by 있음)

**요청:** "각 Tech별로 CPK 트렌드를 분리해서"

**Backend 응답:**
```json
{
  "graph_spec": [{
    "split_by": "TECH",
    "chart_type": "line_graph",
    "encodings": {"y": {"field": "CPK"}},
    "transforms": [
      {"type": "filter", "field": "TECH", "value": "{{SPLIT_VALUE}}"}
    ],
    "layout": {"title": "{{SPLIT_VALUE}} CPK"}
  }]
}
```

**Frontend 자동 처리:** `[0].split_by` 존재 → TECH 고유값 추출 → 템플릿 확장 → 여러 그래프

---

## 패턴 2: 여러 개

**요청:** "WIDTH, THICKNESS 각각 트렌드"

**Backend 응답:**
```json
{
  "graph_spec": [
    {
      "chart_type": "line_graph",
      "encodings": {"y": {"field": "WIDTH"}},
      "layout": {"title": "WIDTH"}
    },
    {
      "chart_type": "line_graph",
      "encodings": {"y": {"field": "THICKNESS"}},
      "layout": {"title": "THICKNESS"}
    }
  ]
}
```

**Frontend 자동 처리:** 배열 길이 > 1 → 여러 그래프

---

## 패턴 3: 단일

**요청:** "CPK 트렌드"

**Backend 응답:**
```json
{
  "graph_spec": [{
    "chart_type": "line_graph",
    "encodings": {"y": {"field": "CPK"}},
    "layout": {"title": "CPK Trend"}
  }]
}
```

**Frontend 자동 처리:** 배열 길이 = 1 → 단일 그래프

---

## Frontend 자동 판단 로직

```javascript
// graph_spec은 항상 배열
if (graph_spec[0].split_by) {
  // → 템플릿 확장
} else if (graph_spec.length === 1) {
  // → 단일 그래프
} else {
  // → 여러 그래프
}
```

**모든 그래프 타입 지원:** `bar_graph`, `line_graph`, `box_plot`, `scatter_plot`
