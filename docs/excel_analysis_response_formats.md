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
    "analysis_type": "table | bar_graph | line_graph | box_plot | general_text | excel_analysis | excel_chart | excel_summary",
    "file_name": "string",
    "summary": "string",
    "success_message": "string",
    "real_data": [ ... ],          // see section 3
    "graph_spec": { ... },         // Declarative spec for single graph, see section 3
    "graph_specs": [ { ... }, { ... } ],  // Optional: Array of graph specs for multiple graphs
    "sql": "string | null",
    "timestamp": "ISO-8601 string",
    "additional_fields": "pass anything else the frontend might need"
  }
}
```

The frontend (`src/App.vue`) reads `analysis_type` to decide how to render the result tab:

- `table` → `result.data` becomes the primary table rows.
- `bar_graph`, `line_graph`, `box_plot`, `scatter_plot` → Plotly charts are rendered from `graph_spec` (single) or `graph_specs` (multiple).
- `general_text` → plain text block.
- `excel_analysis`, `excel_chart`, `excel_summary` → specialized Excel cards using `data`, `summary`, and `chart_config`.

### 2.1 Multiple Graphs Support

When generating multiple graphs of the same type (e.g., separate line graphs for each category):

- Use `graph_specs` (array) instead of `graph_spec` (single object)
- Each graph spec in the array should be a complete declarative spec
- The `real_data` remains the same (single dataset shared by all graphs)
- Each graph can apply different filters or transformations on the same dataset
- Frontend will render multiple graph components side by side or stacked

**Example use case:** "Show line graph for each Tech category separately"
- `real_data`: Contains all data with Tech column
- `graph_specs`: Array of specs, each filtering different Tech value


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
| `layout` / `config` | Passed straight to Plotly after traces are built. See section 3.3 for customization options. |

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

### 3.3 Layout Customization Options

The `layout` object supports extensive customization for chart appearance. Below are commonly used options:

#### 📐 Chart Size & Margins (1, 2)

```json
"layout": {
  "height": 600,           // Chart height in pixels (default: 500)
  "width": 1000,           // Chart width in pixels (default: auto-calculated based on data)
  "autosize": false,       // Fixed size to enable scrolling (default: false)
  "margin": {
    "l": 80,               // Left margin in pixels
    "r": 80,               // Right margin in pixels  
    "t": 100,              // Top margin in pixels
    "b": 120,              // Bottom margin in pixels
    "pad": 4               // Padding between plot and axes
  }
}
```

**Note on Width:**
- Width is automatically set to fit container (responsive)
- Charts adapt to screen width for optimal trend visibility
- Do NOT specify width unless you have a specific requirement

**Note on Height & Margins:**
- Default height: 500px
- Bottom margin: 150px (increased to accommodate long x-axis labels)
- Adjust `margin.b` if labels are very long (200-250px recommended for -90° rotation)

#### 📊 X-Axis Customization (3)

```json
"layout": {
  "xaxis": {
    "title": {
      "text": "X Axis Label",
      "font": {
        "size": 14,
        "family": "Arial",
        "color": "#333"
      }
    },
    "tickangle": -45,      // Label rotation angle (-90 to 90)
    "tickfont": {
      "size": 10,          // Tick label font size (useful for long labels)
      "family": "Arial",
      "color": "#666"
    },
    "tickmode": "auto",    // "auto", "linear", "array"
    "nticks": 20,          // Maximum number of ticks
    "showticklabels": true,
    "showgrid": true,      // Show vertical grid lines
    "gridcolor": "#e0e0e0",
    "gridwidth": 1,
    "griddash": "solid"    // "solid", "dot", "dash"
  }
}
```

#### 📈 Y-Axis Customization (4)

```json
"layout": {
  "yaxis": {
    "title": {
      "text": "Y Axis Label",
      "font": {
        "size": 14,
        "color": "#333"
      }
    },
    "range": [0, 100],     // Explicit range [min, max] for better trend visibility
    "autorange": true,     // Or use auto-range
    "tickfont": {
      "size": 11
    },
    "showgrid": true,      // Show horizontal grid lines
    "gridcolor": "#d3d3d3",
    "gridwidth": 1,
    "griddash": "dot",
    "zeroline": true,      // Show zero baseline
    "zerolinecolor": "#999",
    "zerolinewidth": 2
  }
}
```

#### 📍 Reference Lines & Shapes (6)

Add horizontal/vertical reference lines (e.g., target values, thresholds):

```json
"layout": {
  "shapes": [
    {
      "type": "line",
      "x0": 0,
      "x1": 1,
      "xref": "paper",     // "paper" spans full chart width, "x" uses data coordinates
      "y0": 80,            // Y-coordinate for horizontal line
      "y1": 80,
      "line": {
        "color": "red",
        "width": 2,
        "dash": "dash"     // "solid", "dot", "dash", "dashdot"
      }
    },
    {
      "type": "line",      // Vertical line example
      "x0": "2025-11-15",
      "x1": "2025-11-15",
      "y0": 0,
      "y1": 1,
      "yref": "paper",
      "line": {
        "color": "green",
        "width": 1,
        "dash": "dot"
      }
    }
  ]
}
```

#### 🎨 Complete Example with All Customizations

```json
"layout": {
  "title": {
    "text": "CPK Trend Analysis",
    "font": { "size": 18, "color": "#1f77b4" },
    "x": 0.5,
    "xanchor": "center"
  },
  "height": 500,
  "width": 1000,
  "margin": { "l": 100, "r": 100, "t": 80, "b": 120, "pad": 4 },
  "xaxis": {
    "title": { "text": "Date", "font": { "size": 14 } },
    "tickangle": -45,
    "tickfont": { "size": 10, "color": "#666" },
    "showgrid": true,
    "gridcolor": "#e5e5e5",
    "gridwidth": 1
  },
  "yaxis": {
    "title": { "text": "CPK Value", "font": { "size": 14 } },
    "range": [0.8, 2.0],
    "tickfont": { "size": 11 },
    "showgrid": true,
    "gridcolor": "#d3d3d3",
    "gridwidth": 1,
    "griddash": "dot",
    "zeroline": true,
    "zerolinecolor": "#999",
    "zerolinewidth": 2
  },
  "shapes": [
    {
      "type": "line",
      "x0": 0, "x1": 1, "xref": "paper",
      "y0": 1.33, "y1": 1.33,
      "line": { "color": "red", "width": 2, "dash": "dash" }
    }
  ],
  "paper_bgcolor": "white",
  "plot_bgcolor": "#fafafa",
  "font": { "family": "Arial, sans-serif", "size": 12 }
}
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
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
        "xaxis": {
          "title": "EQ",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true,
          "gridcolor": "#e5e5e5"
        },
        "yaxis": {
          "title": "Value",
          "showgrid": true,
          "gridcolor": "#d3d3d3",
          "zeroline": true,
          "zerolinecolor": "#999"
        }
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
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
        "xaxis": {
          "title": "Date",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true,
          "gridcolor": "#e5e5e5"
        },
        "yaxis": {
          "title": "CPK",
          "range": [0.8, 2.0],
          "showgrid": true,
          "gridcolor": "#d3d3d3",
          "zeroline": true,
          "zerolinecolor": "#999"
        },
        "shapes": [
          {
            "type": "line",
            "x0": 0, "x1": 1, "xref": "paper",
            "y0": 1.33, "y1": 1.33,
            "line": { "color": "red", "width": 2, "dash": "dash" }
          }
        ]
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
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
        "xaxis": {
          "title": "OPER",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true,
          "gridcolor": "#e5e5e5"
        },
        "yaxis": {
          "title": "Count",
          "showgrid": true,
          "gridcolor": "#d3d3d3",
          "zeroline": true,
          "zerolinecolor": "#999"
        }
      }
    },
    "timestamp": "2025-11-20T09:30:55.101Z"
  }
}
```


### 4.5 Scatter Plot Result (산점도)

**⭐ 중요: Scatter plot은 기본적으로 회귀선이 자동으로 추가됩니다!**

#### 4.5.1 기본 산점도 (회귀선 자동 추가)

```json
{
  "data": {
    "analysis_type": "scatter_plot",
    "file_name": "correlation.xlsx",
    "summary": "온도와 수율의 상관관계 분석",
    "success_message": "✅ 산점도 생성 완료",
    "real_data": [
      [
        {"TEMPERATURE": 25.5, "YIELD": 98.2, "DEVICE": "A1"},
        {"TEMPERATURE": 26.1, "YIELD": 97.5, "DEVICE": "A1"},
        {"TEMPERATURE": 24.8, "YIELD": 99.0, "DEVICE": "B2"},
        {"TEMPERATURE": 25.9, "YIELD": 98.1, "DEVICE": "B2"}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "scatter_plot",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "TEMPERATURE", "type": "quantitative" },
        "y": { "field": "YIELD", "type": "quantitative" }
      },
      "layout": {
        "title": "온도와 수율의 상관관계",
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
        "xaxis": {
          "title": "온도 (°C)",
          "showgrid": true,
          "gridcolor": "#e5e5e5",
          "zeroline": true
        },
        "yaxis": {
          "title": "수율 (%)",
          "showgrid": true,
          "gridcolor": "#d3d3d3",
          "zeroline": true
        }
      }
    },
    "timestamp": "2025-12-04T10:15:30.123Z"
  }
}
```

**중요:** `reference_lines` 필드가 없음 (또는 `null`, `""`, `[]`) → 회귀선 자동 추가!
**결과:** 산점도 점들 + 파란색 실선 회귀선이 자동으로 표시됨

#### 4.5.2 산점도 + 시리즈별 색상 구분

```json
{
  "data": {
    "analysis_type": "scatter_plot",
    "file_name": "correlation.xlsx",
    "summary": "장비별 온도와 수율의 상관관계",
    "success_message": "✅ 산점도 생성 완료",
    "real_data": [
      [
        {"TEMPERATURE": 25.5, "YIELD": 98.2, "DEVICE": "A1"},
        {"TEMPERATURE": 26.1, "YIELD": 97.5, "DEVICE": "A1"},
        {"TEMPERATURE": 24.8, "YIELD": 99.0, "DEVICE": "B2"},
        {"TEMPERATURE": 25.9, "YIELD": 98.1, "DEVICE": "B2"}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "scatter_plot",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "TEMPERATURE", "type": "quantitative" },
        "y": { "field": "YIELD", "type": "quantitative" },
        "series": { "field": "DEVICE" }
      },
      "layout": {
        "title": "장비별 온도-수율 상관관계",
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 }
      }
    },
    "timestamp": "2025-12-04T10:15:30.123Z"
  }
}
```

**결과:** 장비별로 색상이 다른 점들 + 전체 데이터 기반 회귀선

#### 4.5.3 산점도 + 추가 참조선 (평균, 목표값)

```json
{
  "data": {
    "analysis_type": "scatter_plot",
    "file_name": "cpk_analysis.xlsx",
    "summary": "CPK 산점도 with 평균 및 목표값",
    "success_message": "✅ 산점도 생성 완료",
    "real_data": [
      [
        {"EQUIPMENT": "EQ01", "CPK": 1.45, "DEVICE": "A1"},
        {"EQUIPMENT": "EQ02", "CPK": 1.32, "DEVICE": "A1"},
        {"EQUIPMENT": "EQ03", "CPK": 1.58, "DEVICE": "B2"}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "scatter_plot",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "EQUIPMENT", "type": "categorical" },
        "y": { "field": "CPK", "type": "quantitative" },
        "series": { "field": "DEVICE" }
      },
      "reference_lines": [
        {
          "type": "regression",
          "name": "회귀선",
          "color": "blue",
          "width": 2,
          "dash": "solid"
        },
        {
          "type": "mean",
          "name": "평균 CPK",
          "color": "red",
          "width": 2,
          "dash": "dash"
        },
        {
          "type": "horizontal",
          "value": 1.33,
          "name": "목표 (1.33)",
          "color": "green",
          "width": 2,
          "dash": "dashdot"
        }
      ],
      "layout": {
        "title": "장비별 CPK 분포",
        "height": 500,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 150 }
      }
    },
    "timestamp": "2025-12-04T10:15:30.123Z"
  }
}
```

**중요:** 추가 선을 요청했으므로 `reference_lines` 배열에 **회귀선도 명시적으로 포함**해야 함!
**결과:** 산점도 + 회귀선 + 평균선 + 목표값 선

#### 4.5.4 평균선만 있는 산점도 (회귀선 없이)

```json
{
  "data": {
    "analysis_type": "scatter_plot",
    "file_name": "data.xlsx",
    "summary": "산점도 with 평균선 (회귀선 없음)",
    "success_message": "✅ 산점도 생성 완료",
    "real_data": [
      [
        {"X": 1, "Y": 10},
        {"X": 2, "Y": 15}
      ]
    ],
    "graph_spec": {
      "schema_version": "1.0",
      "chart_type": "scatter_plot",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "X", "type": "quantitative" },
        "y": { "field": "Y", "type": "quantitative" }
      },
      "reference_lines": [
        {
          "type": "mean",
          "name": "평균",
          "color": "red",
          "width": 2,
          "dash": "dash"
        }
      ],
      "layout": {
        "title": "산점도",
        "height": 500
      }
    },
    "timestamp": "2025-12-04T10:15:30.123Z"
  }
}
```

**중요:** 배열에 값이 있으면 그 내용만 표시됩니다 (회귀선 포함 안 됨)
**결과:** 산점도 점들 + 평균선 (회귀선 없음)

### 4.6 Multiple Graphs Examples (여러 그래프 생성)

## 📊 다중 그래프 생성 케이스

### Case 1: 특정 컬럼 값별로 분리 (Filter-based)

**Use Case:** 하나의 카테고리 컬럼의 각 값별로 별도 그래프 생성

**Request:** "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"

```json
{
  "data": {
    "analysis_type": "line_graph",
    "file_name": "trend_data.xlsx",
    "summary": "Tech별 CPK 트렌드 분리 분석",
    "success_message": "✅ Tech별 라인차트 생성 완료 (3개)",
    "real_data": [
      [
        {"DATE": "2025-11-01", "TECH": "Tech_A", "CPK": 1.4},
        {"DATE": "2025-11-02", "TECH": "Tech_A", "CPK": 1.5},
        {"DATE": "2025-11-01", "TECH": "Tech_B", "CPK": 1.2},
        {"DATE": "2025-11-02", "TECH": "Tech_B", "CPK": 1.3},
        {"DATE": "2025-11-01", "TECH": "Tech_C", "CPK": 1.6},
        {"DATE": "2025-11-02", "TECH": "Tech_C", "CPK": 1.7}
      ]
    ],
    "graph_specs": [
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "CPK", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_A CPK Trend",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "xaxis": {
            "title": "Date",
            "tickangle": -45,
            "tickfont": { "size": 10 },
            "showgrid": true
          },
          "yaxis": {
            "title": "CPK",
            "range": [0.8, 2.0],
            "showgrid": true
          },
          "shapes": [
            {
              "type": "line",
              "x0": 0, "x1": 1, "xref": "paper",
              "y0": 1.33, "y1": 1.33,
              "line": { "color": "red", "width": 2, "dash": "dash" }
            }
          ]
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "CPK", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_B CPK Trend",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "xaxis": {
            "title": "Date",
            "tickangle": -45,
            "tickfont": { "size": 10 },
            "showgrid": true
          },
          "yaxis": {
            "title": "CPK",
            "range": [0.8, 2.0],
            "showgrid": true
          },
          "shapes": [
            {
              "type": "line",
              "x0": 0, "x1": 1, "xref": "paper",
              "y0": 1.33, "y1": 1.33,
              "line": { "color": "red", "width": 2, "dash": "dash" }
            }
          ]
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "CPK", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_C" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_C CPK Trend",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "xaxis": {
            "title": "Date",
            "tickangle": -45,
            "tickfont": { "size": 10 },
            "showgrid": true
          },
          "yaxis": {
            "title": "CPK",
            "range": [0.8, 2.0],
            "showgrid": true
          },
          "shapes": [
            {
              "type": "line",
              "x0": 0, "x1": 1, "xref": "paper",
              "y0": 1.33, "y1": 1.33,
              "line": { "color": "red", "width": 2, "dash": "dash" }
            }
          ]
        }
      }
    ],
    "timestamp": "2025-12-05T10:00:00.000Z"
  }
}
```

**Key Points:**
- ✅ `real_data` contains all data (no changes)
- ✅ `graph_specs` is an array of complete graph specifications
- ✅ Each spec applies its own filter (`TECH == "Tech_A"`, etc.)
- ✅ **Same encodings** for all graphs (only filter differs)
- ✅ Each spec has its own title
- ✅ Frontend renders multiple graphs vertically stacked

---

### Case 2: 여러 Y축 컬럼별로 분리 (Encoding-based)

**Use Case:** 각기 다른 Y축 컬럼에 대해 별도 그래프 생성

**Request:** "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드를 라인그래프로 보여줘"

```json
{
  "data": {
    "analysis_type": "line_graph",
    "file_name": "params.xlsx",
    "summary": "파라미터별 장비 트렌드 분석",
    "success_message": "✅ 3개의 파라미터 트렌드 차트 생성 완료",
    "real_data": [
      [
        {"DATE": "2025-11-01", "EQ": "EQ01", "WIDTH": 1.12, "THICKNESS": 0.85, "DEPTH": 2.34},
        {"DATE": "2025-11-02", "EQ": "EQ01", "WIDTH": 1.15, "THICKNESS": 0.87, "DEPTH": 2.36},
        {"DATE": "2025-11-01", "EQ": "EQ02", "WIDTH": 1.10, "THICKNESS": 0.83, "DEPTH": 2.30}
      ]
    ],
    "graph_specs": [
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "WIDTH", "type": "quantitative" },
          "series": { "field": "EQ" }
        },
        "transforms": [
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "WIDTH Trend by Equipment",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "yaxis": { "title": "WIDTH (μm)" }
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "THICKNESS", "type": "quantitative" },
          "series": { "field": "EQ" }
        },
        "transforms": [
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "THICKNESS Trend by Equipment",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "yaxis": { "title": "THICKNESS (μm)" }
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "DEPTH", "type": "quantitative" },
          "series": { "field": "EQ" }
        },
        "transforms": [
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "DEPTH Trend by Equipment",
          "height": 400,
          "margin": { "l": 80, "r": 80, "t": 100, "b": 150 },
          "yaxis": { "title": "DEPTH (μm)" }
        }
      }
    ],
    "timestamp": "2025-12-05T10:00:00.000Z"
  }
}
```

**Key Points:**
- ✅ `real_data` contains all columns (WIDTH, THICKNESS, DEPTH)
- ✅ **Different encodings** for each graph (different y.field)
- ✅ Same series field (EQ) for all graphs
- ✅ No filters needed (using all data)
- ✅ Each graph shows different measurement

---

### Case 3: 특정 값들만 선택적으로 분리 (Selective Filter)

**Use Case:** 전체가 아닌 특정 값들만 골라서 그래프 생성

**Request:** "EQ01, EQ02, EQ03 각각에 대해 WIDTH 분포를 박스플롯으로 보여줘. 다른 장비는 제외"

```json
{
  "data": {
    "analysis_type": "box_plot",
    "file_name": "equipment.xlsx",
    "summary": "주요 3개 장비 WIDTH 분포 분석",
    "success_message": "✅ 3개 장비 박스플롯 생성 완료",
    "real_data": [
      [
        {"EQ": "EQ01", "WIDTH": 1.12},
        {"EQ": "EQ02", "WIDTH": 1.10},
        {"EQ": "EQ03", "WIDTH": 1.15},
        {"EQ": "EQ04", "WIDTH": 1.08},
        {"EQ": "EQ05", "WIDTH": 1.20}
      ]
    ],
    "graph_specs": [
      {
        "schema_version": "1.0",
        "chart_type": "box_plot",
        "dataset_index": 0,
        "encodings": {
          "category": { "field": "EQ" },
          "value": { "field": "WIDTH" }
        },
        "transforms": [
          { "type": "filter", "field": "EQ", "op": "==", "value": "EQ01" }
        ],
        "layout": {
          "title": "EQ01 WIDTH Distribution",
          "height": 400
        },
        "boxpoints": "outliers"
      },
      {
        "schema_version": "1.0",
        "chart_type": "box_plot",
        "dataset_index": 0,
        "encodings": {
          "category": { "field": "EQ" },
          "value": { "field": "WIDTH" }
        },
        "transforms": [
          { "type": "filter", "field": "EQ", "op": "==", "value": "EQ02" }
        ],
        "layout": {
          "title": "EQ02 WIDTH Distribution",
          "height": 400
        },
        "boxpoints": "outliers"
      },
      {
        "schema_version": "1.0",
        "chart_type": "box_plot",
        "dataset_index": 0,
        "encodings": {
          "category": { "field": "EQ" },
          "value": { "field": "WIDTH" }
        },
        "transforms": [
          { "type": "filter", "field": "EQ", "op": "==", "value": "EQ03" }
        ],
        "layout": {
          "title": "EQ03 WIDTH Distribution",
          "height": 400
        },
        "boxpoints": "outliers"
      }
    ],
    "timestamp": "2025-12-05T10:00:00.000Z"
  }
}
```

**Key Points:**
- ✅ `real_data` contains all equipment (including EQ04, EQ05)
- ✅ Only EQ01, EQ02, EQ03 graphs are created
- ✅ Selective filtering based on user specification
- ✅ Other values (EQ04, EQ05) are ignored

---

### Case 4: 조합 케이스 (Filter + Different Encodings)

**Use Case:** 특정 조건별로 필터링하면서 동시에 다른 측정값들을 비교

**Request:** "Tech_A와 Tech_B 각각에 대해 CPK와 YIELD 트렌드를 각각 보여줘 (총 4개 그래프)"

```json
{
  "data": {
    "analysis_type": "line_graph",
    "file_name": "tech_comparison.xlsx",
    "summary": "Tech별 CPK/YIELD 트렌드 비교",
    "success_message": "✅ 4개의 트렌드 차트 생성 완료",
    "real_data": [
      [
        {"DATE": "2025-11-01", "TECH": "Tech_A", "CPK": 1.4, "YIELD": 98.2},
        {"DATE": "2025-11-02", "TECH": "Tech_A", "CPK": 1.5, "YIELD": 98.5},
        {"DATE": "2025-11-01", "TECH": "Tech_B", "CPK": 1.2, "YIELD": 97.5},
        {"DATE": "2025-11-02", "TECH": "Tech_B", "CPK": 1.3, "YIELD": 97.8}
      ]
    ],
    "graph_specs": [
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "CPK", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_A CPK Trend",
          "height": 400,
          "yaxis": { "title": "CPK", "range": [0.8, 2.0] }
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "YIELD", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_A YIELD Trend",
          "height": 400,
          "yaxis": { "title": "YIELD (%)", "range": [95, 100] }
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "CPK", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_B CPK Trend",
          "height": 400,
          "yaxis": { "title": "CPK", "range": [0.8, 2.0] }
        }
      },
      {
        "schema_version": "1.0",
        "chart_type": "line_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "DATE", "type": "temporal" },
          "y": { "field": "YIELD", "type": "quantitative" }
        },
        "transforms": [
          { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" },
          { "type": "sort", "field": "DATE", "direction": "asc" }
        ],
        "layout": {
          "title": "Tech_B YIELD Trend",
          "height": 400,
          "yaxis": { "title": "YIELD (%)", "range": [95, 100] }
        }
      }
    ],
    "timestamp": "2025-12-05T10:00:00.000Z"
  }
}
```

**Key Points:**
- ✅ Combines filter (TECH) + different encodings (CPK vs YIELD)
- ✅ Matrix-style generation: 2 techs × 2 metrics = 4 graphs
- ✅ Each graph has unique filter + encoding combination
- ✅ Different y-axis ranges for different metrics

---

### Case 5: 혼합 그래프 타입 (Advanced)

**Use Case:** 같은 데이터에 대해 다른 그래프 타입으로 여러 뷰 생성

**Request:** "장비별 WIDTH를 박스플롯과 바차트로 각각 보여줘"

```json
{
  "data": {
    "analysis_type": "box_plot",
    "file_name": "width_analysis.xlsx",
    "summary": "장비별 WIDTH 다각도 분석",
    "success_message": "✅ 박스플롯 및 바차트 생성 완료",
    "real_data": [
      [
        {"EQ": "EQ01", "WIDTH": 1.12},
        {"EQ": "EQ01", "WIDTH": 1.15},
        {"EQ": "EQ02", "WIDTH": 1.10},
        {"EQ": "EQ02", "WIDTH": 1.08}
      ]
    ],
    "graph_specs": [
      {
        "schema_version": "1.0",
        "chart_type": "box_plot",
        "dataset_index": 0,
        "encodings": {
          "category": { "field": "EQ" },
          "value": { "field": "WIDTH" }
        },
        "layout": {
          "title": "WIDTH Distribution by Equipment (Box Plot)",
          "height": 400
        },
        "boxpoints": "outliers"
      },
      {
        "schema_version": "1.0",
        "chart_type": "bar_graph",
        "dataset_index": 0,
        "encodings": {
          "x": { "field": "EQ", "type": "categorical" },
          "y": { "field": "WIDTH", "type": "quantitative", "agg": "avg" }
        },
        "layout": {
          "title": "Average WIDTH by Equipment (Bar Chart)",
          "height": 400
        }
      }
    ],
    "timestamp": "2025-12-05T10:00:00.000Z"
  }
}
```

**Key Points:**
- ✅ Different chart_type for each spec
- ✅ Same data, different visualization perspectives
- ✅ Box plot shows distribution, bar chart shows average
- ✅ `analysis_type` can be the primary type or generic

---

## 📋 다중 그래프 생성 패턴 요약

| 케이스 | 변경 요소 | 사용 예시 |
|--------|----------|----------|
| **Case 1** | Filter only | "각 Tech별로 트렌드" |
| **Case 2** | Encoding (y-axis) | "WIDTH, THICKNESS 각각 트렌드" |
| **Case 3** | Selective filter | "EQ01, EQ02만 분리해서" |
| **Case 4** | Filter + Encoding | "Tech_A와 B 각각의 CPK/YIELD" |
| **Case 5** | Chart type | "박스플롯과 바차트로 각각" |

**공통 원칙:**
- ✅ `real_data`는 항상 모든 데이터 포함
- ✅ 각 `graph_spec`은 완전히 독립적
- ✅ `transforms`, `encodings`, `layout`, `chart_type` 모두 다를 수 있음
- ✅ Frontend는 각 spec을 개별적으로 빌드 및 렌더링
- ✅ Works with all graph types: `bar_graph`, `line_graph`, `box_plot`, `scatter_plot`

### 4.7 Reference Lines 상세 스펙

산점도에서 사용 가능한 `reference_lines` 옵션:

#### Mean Line (평균선)
```json
{
  "type": "mean",
  "name": "평균",
  "color": "red",
  "width": 2,
  "dash": "dash"
}
```

#### Regression Line (회귀선)
```json
{
  "type": "regression",
  "name": "회귀선",
  "color": "blue",
  "width": 2,
  "dash": "solid"
}
```

#### Horizontal Line (수평 기준선)
```json
{
  "type": "horizontal",
  "value": 80,
  "name": "목표값",
  "color": "green",
  "width": 2,
  "dash": "dashdot"
}
```

**Dash 스타일:**
- `"solid"` - 실선 ────────
- `"dash"` - 점선 ─ ─ ─ ─ ─
- `"dot"` - 짧은 점선 ∙∙∙∙∙∙∙∙
- `"dashdot"` - 점-대시 ─∙─∙─∙─


## 5. Sending Order

1. Optional progress bubbles (`progress_message`) to keep the user informed.
2. Optional error `msg` chunks if validation fails.
3. Final `data` chunk that follows the skeleton above.

Following this structure ensures the frontend automatically:

- Displays meaningful chat bubbles,
- Builds the correct result tab (table or Plotly chart),
- Stores metadata (SQL, summaries, timestamps) for later reuse.

