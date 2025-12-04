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
    "graph_spec": { ... },         // Declarative spec, see section 3
    "sql": "string | null",
    "timestamp": "ISO-8601 string",
    "additional_fields": "pass anything else the frontend might need"
  }
}
```

The frontend (`src/App.vue`) reads `analysis_type` to decide how to render the result tab:

- `table` → `result.data` becomes the primary table rows.
- `bar_graph`, `line_graph`, `box_plot` → Plotly charts are rendered from `graph_spec`.
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
| `chart_type` | `bar_graph`, `line_graph`, `box_plot`, `scatter`, … |
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
  "height": 600,           // Chart height in pixels (default: 480)
  "width": 1000,           // Chart width in pixels (auto by default)
  "autosize": true,        // Auto-resize to container
  "margin": {
    "l": 80,               // Left margin in pixels
    "r": 80,               // Right margin in pixels  
    "t": 100,              // Top margin in pixels
    "b": 120,              // Bottom margin in pixels
    "pad": 4               // Padding between plot and axes
  }
}
```

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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 100 },
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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120 },
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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 100 },
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


## 5. Sending Order

1. Optional progress bubbles (`progress_message`) to keep the user informed.
2. Optional error `msg` chunks if validation fails.
3. Final `data` chunk that follows the skeleton above.

Following this structure ensures the frontend automatically:

- Displays meaningful chat bubbles,
- Builds the correct result tab (table or Plotly chart),
- Stores metadata (SQL, summaries, timestamps) for later reuse.

