# Excel Analysis Streaming Response Guide

This document summarizes the payload requirements and response formats for Excel analysis endpoints.

Last Updated: 2025-12-04

## 1. SSE Chunk Basics

- Each chunk is sent as `data: { ... }\n\n` over the `/excel_analysis_stream` endpoint.
- **Chat bubbles** appear only when the chunk contains either `progress_message` (normal updates) or `msg` (errors).  
  Example success toast: `{"progress_message": "✅ 엑셀 분석이 완료되었습니다. 요약 보고서를 생성했어요."}`
- **Error bubbles** use `msg`: `{"msg": "❌ 엑셀 파일 형식을 확인해주세요. .xlsx/.xls/.csv만 지원됩니다."}`
- Actual analysis content must be delivered in a separate chunk using the `data` key.

## 1.1 Chart Rendering & Layout Improvements

All Plotly charts now include enhanced layout settings for better visibility and user experience:

- **Automatic Margins**: Charts include proper margins to prevent content from being cut off
  - Left margin: 80px (for y-axis labels)
  - Right margin: 80px (for legend/labels)
  - Top margin: 100px (for title)
  - Bottom margin: 120px (for x-axis labels)
  - Padding: 10px
- **X-axis Labels**: Default angle set to 0° (horizontal) for clear readability
- **Responsive Sizing**: `autosize: true` enabled for all charts
- **Spec Lines Support**: Box plots can include specification lines (USL, LSL, TGT, UCL, LCL) rendered as Plotly shapes


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
- `bar_graph`, `line_graph`, `box_plot`, `scatter_plot` → Plotly charts are rendered from `graph_spec`.
- `general_text` → plain text block.
- `excel_analysis`, `excel_chart`, `excel_summary` → specialized Excel cards using `data`, `summary`, and `chart_config`.
  - `excel_chart` can include `plotly_spec` in `chart_config` for direct Plotly rendering.


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


### 4.2 Box Plot Result (with Spec Lines)

```json
{
  "data": {
    "analysis_type": "box_plot",
    "file_name": "process_param.xlsx",
    "summary": "EQ별 PARA 분포",
    "success_message": "✅ 박스플롯 생성 완료 (규격선 포함)",
    "real_data": [
      [
        {"PARA": "WIDTH", "VALUE": 1.12, "EQ": "EQ01", "USL": 1.50, "LSL": 0.80, "TGT": 1.10},
        {"PARA": "WIDTH", "VALUE": 1.08, "EQ": "EQ02", "USL": 1.50, "LSL": 0.80, "TGT": 1.10}
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
        "xaxis": {"title": "EQ", "tickangle": 0},
        "margin": {
          "l": 80,
          "r": 80,
          "t": 100,
          "b": 120,
          "pad": 10
        },
        "autosize": true,
        "shapes": [
          {
            "type": "line",
            "xref": "paper",
            "yref": "y",
            "x0": 0,
            "x1": 1,
            "y0": 1.50,
            "y1": 1.50,
            "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"},
            "name": "USL"
          },
          {
            "type": "line",
            "xref": "paper",
            "yref": "y",
            "x0": 0,
            "x1": 1,
            "y0": 0.80,
            "y1": 0.80,
            "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"},
            "name": "LSL"
          },
          {
            "type": "line",
            "xref": "paper",
            "yref": "y",
            "x0": 0,
            "x1": 1,
            "y0": 1.10,
            "y1": 1.10,
            "line": {"color": "rgba(0, 128, 0, 0.8)", "width": 2, "dash": "solid"},
            "name": "TGT"
          }
        ]
      },
      "boxpoints": "outliers"
    },
    "timestamp": "2025-12-04T09:30:25.456Z"
  }
}
```

**Note on Spec Lines:**
- USL (Upper Spec Limit): Red dashed line
- LSL (Lower Spec Limit): Red dashed line
- TGT (Target): Green solid line
- UCL (Upper Control Limit): Orange dotted line
- LCL (Lower Control Limit): Orange dotted line

If your Excel data includes columns named `USL`, `LSL`, `TGT`, `UCL`, or `LCL`, the service will automatically add them as horizontal lines in the box plot.


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
        "yaxis": {"title": "CPK"},
        "margin": {
          "l": 80,
          "r": 80,
          "t": 100,
          "b": 120,
          "pad": 10
        },
        "autosize": true
      }
    },
    "timestamp": "2025-12-04T09:30:40.789Z"
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
        "xaxis": {"title": "OPER", "tickangle": 0},
        "yaxis": {"title": "Count"},
        "margin": {
          "l": 80,
          "r": 80,
          "t": 100,
          "b": 120,
          "pad": 10
        },
        "autosize": true
      }
    },
    "timestamp": "2025-12-04T09:30:55.101Z"
  }
}
```

### 4.5 Excel Chart with Direct Plotly Spec

For Excel analysis results that use the new `excel_chart` type with embedded Plotly specification:

```json
{
  "data": {
    "analysis_type": "excel_chart",
    "file_name": "measurements.xlsx",
    "summary": "장비별 측정값 분포 분석",
    "success_message": "✅ 엑셀 차트 분석 완료",
    "data": {
      "basic_info": {
        "shape": [150, 5],
        "columns": ["Device", "Measurement", "USL", "LSL", "TGT"]
      },
      "chart_data": [
        {"Device": "DEV1", "Measurement": 1.23, "USL": 1.50, "LSL": 0.80, "TGT": 1.10},
        {"Device": "DEV2", "Measurement": 1.18, "USL": 1.50, "LSL": 0.80, "TGT": 1.10}
      ]
    },
    "chart_config": {
      "chart_type": "box",
      "plotly_spec": {
        "data": [
          {
            "type": "box",
            "name": "Measurement",
            "x": ["DEV1", "DEV2", "DEV1", "DEV2"],
            "y": [1.23, 1.18, 1.25, 1.15],
            "boxmean": "sd"
          }
        ],
        "layout": {
          "title": {"text": "장비별 측정값 분포"},
          "boxmode": "group",
          "yaxis": {"title": {"text": "Measurement"}},
          "xaxis": {"title": {"text": "Device"}, "tickangle": 0},
          "margin": {
            "l": 80,
            "r": 80,
            "t": 100,
            "b": 120,
            "pad": 10
          },
          "autosize": true,
          "shapes": [
            {
              "type": "line",
              "xref": "paper",
              "yref": "y",
              "x0": 0,
              "x1": 1,
              "y0": 1.50,
              "y1": 1.50,
              "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"}
            },
            {
              "type": "line",
              "xref": "paper",
              "yref": "y",
              "x0": 0,
              "x1": 1,
              "y0": 0.80,
              "y1": 0.80,
              "line": {"color": "rgba(255, 0, 0, 0.6)", "width": 2, "dash": "dash"}
            },
            {
              "type": "line",
              "xref": "paper",
              "yref": "y",
              "x0": 0,
              "x1": 1,
              "y0": 1.10,
              "y1": 1.10,
              "line": {"color": "rgba(0, 128, 0, 0.8)", "width": 2, "dash": "solid"}
            }
          ]
        },
        "config": {
          "displaylogo": false,
          "responsive": true,
          "scrollZoom": true
        }
      }
    },
    "timestamp": "2025-12-04T09:31:10.202Z"
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

## 6. Layout Best Practices

### 6.1 Margin Settings

All charts should include proper margin settings to ensure content is not cut off:

```json
"margin": {
  "l": 80,    // Left margin for y-axis labels
  "r": 80,    // Right margin for legend/labels
  "t": 100,   // Top margin for title
  "b": 120,   // Bottom margin for x-axis labels
  "pad": 10   // Padding between plot area and margins
}
```

### 6.2 X-Axis Label Rotation

By default, x-axis labels are displayed horizontally (0°):

```json
"xaxis": {
  "tickangle": 0  // Horizontal labels (default)
}
```

You can adjust this angle if needed for specific cases with long labels.

### 6.3 Responsive Sizing

Enable responsive sizing for all charts:

```json
"autosize": true
```

### 6.4 Specification Lines (Shapes)

For manufacturing or quality control charts, include specification limits as shapes:

```json
"shapes": [
  {
    "type": "line",
    "xref": "paper",
    "yref": "y",
    "x0": 0,
    "x1": 1,
    "y0": <spec_value>,
    "y1": <spec_value>,
    "line": {
      "color": "rgba(255, 0, 0, 0.6)",  // Red for USL/LSL
      "width": 2,
      "dash": "dash"  // "dash" for limits, "solid" for target
    }
  }
]
```

**Color and Style Guide:**
- **USL/LSL**: `rgba(255, 0, 0, 0.6)` (red) with `dash` style
- **TGT**: `rgba(0, 128, 0, 0.8)` (green) with `solid` style
- **UCL/LCL**: `rgba(255, 165, 0, 0.5)` (orange) with `dot` style

## 7. Modal View Considerations

When results are displayed in a fullscreen modal:

- Success messages are automatically hidden to maximize graph/table space
- Graphs are arranged vertically (graph on top, data table below)
- Scroll functionality is enabled for viewing all content
- All layout settings (margins, angles) are preserved

This ensures optimal viewing experience in both the sidebar results panel and fullscreen modal view.

