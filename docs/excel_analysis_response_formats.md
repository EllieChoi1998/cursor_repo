# Excel Analysis Streaming Response Guide

This document summarizes the payload requirements discussed in the last answer so you can push them to GitHub as-is.


## 1. SSE Chunk Basics

- Each chunk is sent as `data: { ... }\n\n` over the `/excel_analysis_stream` endpoint.
- **Chat bubbles** appear only when the chunk contains either `progress_message` (normal updates) or `msg` (errors).  
  Example success toast: `{"progress_message": "✅ 엑셀 분석이 완료되었습니다. 요약 보고서를 생성했어요."}`
- **Error bubbles** use `msg`: `{"msg": "❌ 엑셀 파일 형식을 확인해주세요. .xlsx/.xls/.csv만 지원됩니다."}`
- Actual analysis content must be delivered in a separate chunk using the `data` key.


## 2. Data Payload Skeleton

```json
{
  "data": {
    "analysis_type": "table | bar_graph | line_graph | box_plot | scatter_plot | general_text | excel_analysis | excel_chart | excel_summary",
    "file_name": "string",
    "summary": "string",
    "success_message": "string",
    "real_data": [ ... ],          // see section 3
    "graph_spec": { ... },         // Declarative spec, see section 3
    "sql": "string | null",
    "timestamp": "ISO-8601 string",
    "additional_fields": "pass anything else the frontend might need"
  }
}
```

The frontend (`src/App.vue`) reads `analysis_type` to decide how to render the result tab:

- `table` → `result.data` becomes the primary table rows.
- `bar_graph`, `line_graph`, `box_plot`, `scatter_plot` → Plotly charts are rendered from `graph_spec`.
- `general_text` → plain text block.
- `excel_analysis`, `excel_chart`, `excel_summary` → specialized Excel cards using `data`, `summary`, and `chart_config`.


## 3. `real_data` & Declarative Graph Specs

- `real_data` should be an array of datasets.  
  `[[{...}, {...}], [{...}]]` means “two data tables”, while a single dataset looks like `[[{...}, {...}]]`.
- `graph_spec` now only describes *how* to map `real_data` columns into a Plotly figure.  
  The frontend reads this schema, looks up the referenced dataset, and builds the Plotly traces locally—so no raw values live inside `graph_spec`.

### 3.1 Required fields

| Field | Description |
| --- | --- |
| `schema_version` | Optional string (`"1.0"`) to track future changes. |
| `chart_type` | `bar_graph`, `line_graph`, `box_plot`, `scatter_plot`, … |
| `dataset_index` | Which dataset inside `real_data` to read (defaults to `0`). |
| `encodings` | Column mapping definition (see below). |
| `transforms` | Optional array of `{ type, field, ... }` instructions (filter/sort). |
| `layout` / `config` | Passed straight to Plotly after traces are built. |

### 3.2 Encodings

```
"encodings": {
  "x": { "field": "OPER", "type": "categorical" },
  "y": { "field": "DEFECT", "type": "quantitative", "agg": "sum" },
  "series": { "field": "DEVICE" },         // optional (per-trace grouping)
  "category": { "field": "EQ" },           // alias for x when categories make more sense
  "value": { "field": "VALUE" }            // primarily for box plots
}
```

Supported aggregations: `sum`, `avg/mean`, `max`, `min`, `count`, `median`, `identity` (default for line/scatter).
Supported transforms:

```
{ "type": "filter", "field": "CPK", "op": ">", "value": 1.2 }
{ "type": "filter", "field": "OPER", "op": "in", "value": ["1100", "1200"] }
{ "type": "sort", "field": "DATE", "direction": "asc" }
```


## 4. Example Payloads

Send each example as its own SSE chunk (`data: { ... }\n\n`).

### 4.1 Table Result

```json
{
  "data": {
    "analysis_type": "table",
    "file_name": "yield_summary.xlsx",
    "summary": "Lot별 수율/CPK 요약",
    "success_message": "✅ 표 분석 완료",
    "real_data": [
      [
        {"LOT_ID": "L2401", "YIELD": 98.2, "CPK": 1.45},
        {"LOT_ID": "L2402", "YIELD": 96.7, "CPK": 1.32}
      ]
    ],
    "sql": "SELECT lot_id, yield, cpk FROM yield_table LIMIT 50",
    "timestamp": "2025-11-20T09:30:11.123Z"
  }
}
```


### 4.2 Box Plot Result

```json
{
  "data": {
    "analysis_type": "box_plot",
    "file_name": "process_param.xlsx",
    "summary": "EQ별 PARA 분포",
    "success_message": "✅ 박스플롯 생성 완료",
    "real_data": [
      [
        {"PARA": "WIDTH", "VALUE": 1.12, "EQ": "EQ01"},
        {"PARA": "WIDTH", "VALUE": 1.08, "EQ": "EQ02"}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "box_plot",
      "dataset_index": 0,
      "encodings": {
        "category": { "field": "EQ" },
        "value": { "field": "VALUE" },
        "series": { "field": "PARA" }
      },
      "layout": {
        "title": "WIDTH 분포",
        "yaxis": {"title": "Value"},
        "xaxis": {"title": "EQ"}
      },
      "boxpoints": "outliers"
    },
    "timestamp": "2025-11-20T09:30:25.456Z"
  }
}
```


### 4.3 Line Graph Result

```json
{
  "data": {
    "analysis_type": "line_graph",
    "file_name": "trend.xlsx",
    "summary": "Device별 LOT 트렌드",
    "success_message": "✅ 라인차트 생성 완료",
    "real_data": [
      [
        {"DATE": "2025-11-01", "DEVICE": "A1", "CPK": 1.4},
        {"DATE": "2025-11-02", "DEVICE": "A1", "CPK": 1.5},
        {"DATE": "2025-11-01", "DEVICE": "B2", "CPK": 1.2}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "line_graph",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "DATE", "type": "temporal" },
        "y": { "field": "CPK", "type": "quantitative" },
        "series": { "field": "DEVICE" }
      },
      "transforms": [
        { "type": "filter", "field": "CPK", "op": ">", "value": 0 }
      ],
      "layout": {
        "title": "CPK Trend",
        "xaxis": {"title": "Date"},
        "yaxis": {"title": "CPK"}
      }
    },
    "timestamp": "2025-11-20T09:30:40.789Z"
  }
}
```


### 4.4 Bar Graph Result

```json
{
  "data": {
    "analysis_type": "bar_graph",
    "file_name": "defect.xlsx",
    "summary": "공정별 불량 카운트",
    "success_message": "✅ 바차트 생성 완료",
    "real_data": [
      [
        {"OPER": "1100", "DEFECT": 15},
        {"OPER": "1200", "DEFECT": 9}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "bar_graph",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "OPER", "type": "categorical" },
        "y": { "field": "DEFECT", "type": "quantitative", "agg": "sum" }
      },
      "layout": {
        "title": "Defect Count by OPER",
        "xaxis": {"title": "OPER"},
        "yaxis": {"title": "Count"}
      }
    },
    "timestamp": "2025-11-20T09:30:55.101Z"
  }
}
```


### 4.5 Scatter Plot Result

```json
{
  "data": {
    "analysis_type": "scatter_plot",
    "file_name": "correlation_analysis.xlsx",
    "summary": "변수 간 상관관계 분석",
    "success_message": "✅ 산점도 생성 완료",
    "real_data": [
      [
        {"TEMP": 25.3, "YIELD": 98.5, "DEVICE": "A1"},
        {"TEMP": 26.1, "YIELD": 97.8, "DEVICE": "A1"},
        {"TEMP": 24.8, "YIELD": 99.2, "DEVICE": "A1"},
        {"TEMP": 25.5, "YIELD": 96.5, "DEVICE": "B2"},
        {"TEMP": 26.3, "YIELD": 95.8, "DEVICE": "B2"},
        {"TEMP": 24.2, "YIELD": 97.1, "DEVICE": "B2"}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "scatter_plot",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "TEMP", "type": "quantitative" },
        "y": { "field": "YIELD", "type": "quantitative" },
        "series": { "field": "DEVICE" }
      },
      "transforms": [
        { "type": "filter", "field": "YIELD", "op": ">", "value": 0 }
      ],
      "layout": {
        "title": "Temperature vs Yield Correlation",
        "xaxis": {"title": "Temperature (°C)"},
        "yaxis": {"title": "Yield (%)"}
      },
      "config": {
        "mode": "markers"
      }
    },
    "timestamp": "2025-11-26T10:45:30.123Z"
  }
}
```


## 5. Sending Order

1. Optional progress bubbles (`progress_message`) to keep the user informed.
2. Optional error `msg` chunks if validation fails.
3. Final `data` chunk that follows the skeleton above.

Following this structure ensures the frontend automatically:

- Displays meaningful chat bubbles,
- Builds the correct result tab (table or Plotly chart),
- Stores metadata (SQL, summaries, timestamps) for later reuse.

