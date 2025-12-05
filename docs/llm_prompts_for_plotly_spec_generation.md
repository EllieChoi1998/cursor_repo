# LLM Prompts for Plotly Graph Spec Generation

이 문서는 엑셀 데이터 분석에서 PlotlyGraph의 `graph_spec`을 LLM API 호출로 생성하기 위한 프롬프트 템플릿을 제공합니다.

## 📋 공통 가이드라인

### 입력 정보

LLM에게 제공해야 할 정보:
1. **엑셀 데이터 메타정보**
   - 컬럼명 리스트
   - 각 컬럼의 데이터 타입 (숫자형, 문자형, 날짜형)
   - 샘플 데이터 (처음 5-10개 행)
   - 각 컬럼의 고유값 수 (카테고리 판단용)

2. **사용자 요청**
   - 사용자가 입력한 자연어 질문/요청
   - 예: "장비별 불량 개수를 바차트로 보여줘"
   - 예: "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘" (다중 그래프)

### 출력 형식

#### 단일 그래프 (Single Graph)

LLM은 **JSON 형식**으로 `graph_spec` 객체를 반환해야 합니다:

```json
{
  "schema_version": "1.0",
  "chart_type": "bar_graph | line_graph | box_plot | scatter_plot",
  "dataset_index": 0,
  "encodings": { ... },
  "transforms": [ ... ],
  "layout": { ... },
  "config": { ... }
}
```

#### 다중 그래프 (Multiple Graphs)

사용자가 **"각각", "분리", "별도", "나눠서", "개별"** 등의 키워드로 여러 그래프를 요청한 경우:

```json
{
  "graph_specs": [
    {
      "schema_version": "1.0",
      "chart_type": "line_graph",
      "dataset_index": 0,
      "encodings": { ... },
      "transforms": [
        { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" }
      ],
      "layout": {
        "title": "Tech_A CPK Trend",
        ...
      }
    },
    {
      "schema_version": "1.0",
      "chart_type": "line_graph",
      "dataset_index": 0,
      "encodings": { ... },
      "transforms": [
        { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" }
      ],
      "layout": {
        "title": "Tech_B CPK Trend",
        ...
      }
    }
  ]
}
```

**중요:**
- ✅ `graph_specs` 배열을 반환 (단일 `graph_spec`이 아님)
- ✅ 각 spec은 완전한 그래프 스펙 (schema_version, chart_type, encodings, layout 등)
- ✅ 각 spec은 필터를 사용해 데이터를 분리 (동일한 dataset_index 사용)
- ✅ 각 spec의 title을 다르게 설정 (카테고리명 포함)
- ✅ real_data는 변경 없음 (모든 데이터 포함)

### 중요 제약사항

1. ⚠️ **실제 데이터 값을 포함하지 말 것** - 컬럼명 참조만 사용
2. ⚠️ **존재하지 않는 컬럼명 사용 금지** - 제공된 메타정보의 컬럼만 사용
3. ✅ **기본 레이아웃 옵션 적용** - 가독성 향상을 위한 커스터마이징
4. ✅ **한글 사용자 요청 이해** - 자연어 처리 필요
5. ✅ **다중 그래프 키워드 인식** - "각각", "분리", "별도", "나눠서", "개별" 등

---

## 1️⃣ Bar Graph Prompt

### 사용 시나리오
- 카테고리별 값 비교
- 그룹별 집계 (sum, count, average 등)
- 여러 시리즈 비교 (grouped/stacked bar)

### Prompt Template

```
You are an expert data analyst specializing in creating Plotly chart specifications from Excel data.

# Task
Generate a `graph_spec` JSON object for a BAR GRAPH based on the user's request and Excel data metadata.

# Input Data

## Excel Columns Metadata
{column_metadata}

Example format:
- Column: "DEVICE" | Type: string | Sample values: ["A1", "B2", "C3"] | Unique count: 5
- Column: "DEFECT_COUNT" | Type: number | Sample values: [15, 23, 8] | Unique count: 50
- Column: "DATE" | Type: date | Sample values: ["2025-11-01", "2025-11-02"] | Unique count: 30

## Sample Data (first 5 rows)
{sample_data}

## User Request (Korean)
"{user_request}"

# Output Requirements

Generate a JSON object with the following structure:

```json
{
  "schema_version": "1.0",
  "chart_type": "bar_graph",
  "dataset_index": 0,
  "encodings": {
    "x": {
      "field": "COLUMN_NAME",
      "type": "categorical"
    },
    "y": {
      "field": "COLUMN_NAME",
      "type": "quantitative",
      "agg": "sum | avg | count | max | min"
    },
    "series": {
      "field": "COLUMN_NAME (optional, for grouped bars)"
    }
  },
  "transforms": [
    {
      "type": "filter",
      "field": "COLUMN_NAME",
      "op": "> | < | >= | <= | == | != | in",
      "value": "VALUE or [VALUES]"
    }
  ],
  "layout": {
    "title": "Chart Title in Korean",
    "height": 500,
    // NOTE: Do NOT specify width - charts auto-fit to container for best trend visibility
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },  // b: 150 for long x-axis labels
    "xaxis": {
      "title": "X Axis Label",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "Y Axis Label",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    },
    "barmode": "group (or stack)"
  }
}
```

# Rules

1. **Column Selection**
   - Choose the most appropriate columns based on user request
   - X-axis: Categorical column (low unique count, string type)
   - Y-axis: Numerical column (number type)
   - Series: Optional grouping column for multi-series bars

2. **Aggregation**
   - Choose aggregation based on request:
     - "합계", "총", "total" → "sum"
     - "평균", "average" → "avg"
     - "개수", "count" → "count"
     - "최대", "max" → "max"
     - "최소", "min" → "min"

3. **Filters**
   - Add filters only if explicitly mentioned in user request
   - Example: "불량이 10개 이상인" → filter with op: ">=", value: 10

4. **Layout Customization**
   - Always include the default layout options shown above
   - Adjust title and axis labels based on data context
   - Use Korean for titles and labels
   - X-axis label handling:
     - Default: `tickangle: -45` with `margin.b: 150`
     - If labels are very long: use `tickangle: -90` with `margin.b: 200-250`
     - If labels are short (<5 chars) and few (<10): can use `tickangle: 0`
   - **DO NOT specify width** - charts automatically fit container width for optimal trend visibility

5. **Bar Mode**
   - Use "group" for side-by-side comparison
   - Use "stack" if user mentions "누적", "stacked"

6. **Constraints**
   - ⚠️ Do NOT include actual data values in the spec
   - ⚠️ Only reference column names that exist in metadata
   - ⚠️ Return only valid JSON, no extra text

# Example Output

For request: "장비별 불량 개수를 바차트로 보여줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "bar_graph",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "DEVICE", "type": "categorical" },
    "y": { "field": "DEFECT_COUNT", "type": "quantitative", "agg": "sum" }
  },
  "transforms": [],
  "layout": {
    "title": "장비별 불량 개수",
    "height": 500,
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },
    "xaxis": {
      "title": "장비",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "불량 개수",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    },
    "barmode": "group"
  }
}
```

Now generate the graph_spec JSON based on the provided data and user request.
```

---

## 2️⃣ Line Graph Prompt

### 사용 시나리오
- 시간에 따른 트렌드 분석
- 연속적인 값의 변화 추적
- 여러 시리즈 트렌드 비교

### Prompt Template

```
You are an expert data analyst specializing in creating Plotly chart specifications from Excel data.

# Task
Generate a `graph_spec` JSON object for a LINE GRAPH based on the user's request and Excel data metadata.

# Input Data

## Excel Columns Metadata
{column_metadata}

Example format:
- Column: "DATE" | Type: date | Sample values: ["2025-11-01", "2025-11-02"] | Unique count: 30
- Column: "CPK" | Type: number | Sample values: [1.45, 1.32, 1.58] | Unique count: 100
- Column: "DEVICE" | Type: string | Sample values: ["A1", "B2"] | Unique count: 3

## Sample Data (first 5 rows)
{sample_data}

## User Request (Korean)
"{user_request}"

# Output Requirements

Generate a JSON object with the following structure:

```json
{
  "schema_version": "1.0",
  "chart_type": "line_graph",
  "dataset_index": 0,
  "encodings": {
    "x": {
      "field": "COLUMN_NAME",
      "type": "temporal | categorical"
    },
    "y": {
      "field": "COLUMN_NAME",
      "type": "quantitative",
      "agg": "identity | avg | sum"
    },
    "series": {
      "field": "COLUMN_NAME (optional, for multi-line)"
    }
  },
  "transforms": [
    {
      "type": "sort",
      "field": "DATE_COLUMN",
      "direction": "asc"
    }
  ],
  "layout": {
    "title": "Chart Title in Korean",
    "height": 500,
    // NOTE: Do NOT specify width - charts auto-fit to container for best trend visibility
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },  // b: 150 for long x-axis labels
    "xaxis": {
      "title": "X Axis Label",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "Y Axis Label",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "griddash": "dot",
      "zeroline": true,
      "zerolinecolor": "#999",
      "range": [min_value, max_value] (optional)
    },
    "shapes": [
      {
        "type": "line",
        "x0": 0, "x1": 1, "xref": "paper",
        "y0": "TARGET_VALUE", "y1": "TARGET_VALUE",
        "line": { "color": "red", "width": 2, "dash": "dash" }
      }
    ]
  }
}
```

# Rules

1. **Column Selection**
   - X-axis: Usually time/date column or sequential categorical column
   - Y-axis: Numerical measurement/metric
   - Series: Grouping column for multiple trend lines

2. **Aggregation**
   - Default to "identity" for line graphs (no aggregation)
   - Use "avg" if multiple values exist per x-value
   - Choose based on context and user request

3. **Sorting**
   - Always add sort transform for x-axis (especially for dates)
   - Direction: "asc" for chronological order

4. **Y-axis Range**
   - Add explicit range if user mentions specific bounds
   - Example: "CPK 0.8부터 2.0까지" → "range": [0.8, 2.0]
   - Helps emphasize trends by zooming into relevant range

5. **Reference Lines (shapes)**
   - Add horizontal lines for targets, thresholds, or limits
   - Example: "목표값 1.33" → add shape at y=1.33
   - Use colors: red (target), green (good), orange (warning)

6. **Layout Customization**
   - Use `griddash: "dot"` for y-axis (better for trends)
   - Increase bottom margin (120) for rotated x-axis labels
   - Consider adding multiple shapes for USL/LSL/Target

7. **Constraints**
   - ⚠️ Do NOT include actual data values in the spec
   - ⚠️ Only reference column names that exist in metadata
   - ⚠️ Return only valid JSON, no extra text

# Example Output

## Example 1: Single Line Graph

For request: "날짜별 CPK 트렌드를 라인차트로 보여줘. 목표값 1.33도 표시해줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "line_graph",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "DATE", "type": "temporal" },
    "y": { "field": "CPK", "type": "quantitative", "agg": "identity" }
  },
  "transforms": [
    { "type": "sort", "field": "DATE", "direction": "asc" }
  ],
  "layout": {
    "title": "날짜별 CPK 트렌드",
    "height": 500,
    "margin": { "l": 80, "r": 80, "t": 100, "b": 120, "pad": 4 },
    "xaxis": {
      "title": "날짜",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "CPK",
      "range": [0.8, 2.0],
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "griddash": "dot",
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
}
```

## Example 2: Multiple Line Graphs (각 Tech별로 분리)

For request: "각 Tech별로 CPK 트렌드를 분리해서 라인그래프 보여줘"

Given metadata shows TECH column has unique values: ["Tech_A", "Tech_B", "Tech_C"]

```json
{
  "graph_specs": [
    {
      "schema_version": "1.0",
      "chart_type": "line_graph",
      "dataset_index": 0,
      "encodings": {
        "x": { "field": "DATE", "type": "temporal" },
        "y": { "field": "CPK", "type": "quantitative", "agg": "identity" }
      },
      "transforms": [
        { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_A" },
        { "type": "sort", "field": "DATE", "direction": "asc" }
      ],
      "layout": {
        "title": "Tech_A CPK 트렌드",
        "height": 400,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120, "pad": 4 },
        "xaxis": {
          "title": "날짜",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true
        },
        "yaxis": {
          "title": "CPK",
          "range": [0.8, 2.0],
          "showgrid": true,
          "griddash": "dot"
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
        "y": { "field": "CPK", "type": "quantitative", "agg": "identity" }
      },
      "transforms": [
        { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_B" },
        { "type": "sort", "field": "DATE", "direction": "asc" }
      ],
      "layout": {
        "title": "Tech_B CPK 트렌드",
        "height": 400,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120, "pad": 4 },
        "xaxis": {
          "title": "날짜",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true
        },
        "yaxis": {
          "title": "CPK",
          "range": [0.8, 2.0],
          "showgrid": true,
          "griddash": "dot"
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
        "y": { "field": "CPK", "type": "quantitative", "agg": "identity" }
      },
      "transforms": [
        { "type": "filter", "field": "TECH", "op": "==", "value": "Tech_C" },
        { "type": "sort", "field": "DATE", "direction": "asc" }
      ],
      "layout": {
        "title": "Tech_C CPK 트렌드",
        "height": 400,
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120, "pad": 4 },
        "xaxis": {
          "title": "날짜",
          "tickangle": -45,
          "tickfont": { "size": 10 },
          "showgrid": true
        },
        "yaxis": {
          "title": "CPK",
          "range": [0.8, 2.0],
          "showgrid": true,
          "griddash": "dot"
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
  ]
}
```

**Important for Multiple Graphs:**
- ✅ Return `graph_specs` array (not single `graph_spec`)
- ✅ Check metadata for unique values in the grouping column (TECH)
- ✅ Create one spec per unique value
- ✅ Each spec uses same encodings but different filter
- ✅ Each spec has unique title with category name
- ✅ Use consistent layout/styling across all specs

## Example 3: Multiple Graphs - Different Y-axis Columns

For request: "WIDTH, THICKNESS, DEPTH 각각에 대해 장비별 트렌드를 라인그래프로 보여줘"

Given metadata shows columns: DATE, EQ, WIDTH, THICKNESS, DEPTH

```json
{
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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120 },
        "xaxis": { "title": "날짜", "tickangle": -45 },
        "yaxis": { "title": "WIDTH (μm)", "showgrid": true }
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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120 },
        "xaxis": { "title": "날짜", "tickangle": -45 },
        "yaxis": { "title": "THICKNESS (μm)", "showgrid": true }
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
        "margin": { "l": 80, "r": 80, "t": 100, "b": 120 },
        "xaxis": { "title": "날짜", "tickangle": -45 },
        "yaxis": { "title": "DEPTH (μm)", "showgrid": true }
      }
    }
  ]
}
```

**Key differences from Example 2:**
- ✅ Different `y.field` for each spec (WIDTH, THICKNESS, DEPTH)
- ✅ No filters needed (all data used for each graph)
- ✅ Same `series.field` (EQ) for all graphs
- ✅ Different y-axis titles for each measurement

## Example 4: Multiple Graphs - Combination Pattern

For request: "Tech_A와 Tech_B 각각에 대해 CPK와 YIELD 트렌드를 각각 보여줘"

This creates 2 techs × 2 metrics = 4 graphs

```json
{
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
  ]
}
```

**Combination pattern:**
- ✅ Combines filter (TECH) + different encodings (CPK vs YIELD)
- ✅ Creates matrix: categories × measurements
- ✅ Each graph is fully independent
- ✅ Different y-axis ranges for different metrics

Now generate the graph_spec (or graph_specs) JSON based on the provided data and user request.
```

---

## 3️⃣ Box Plot Prompt

### 사용 시나리오
- 데이터 분포 분석
- 카테고리별 변동성 비교
- 이상치(outlier) 탐지
- 여러 그룹의 통계적 비교

### Prompt Template

```
You are an expert data analyst specializing in creating Plotly chart specifications from Excel data.

# Task
Generate a `graph_spec` JSON object for a BOX PLOT based on the user's request and Excel data metadata.

# Input Data

## Excel Columns Metadata
{column_metadata}

Example format:
- Column: "EQ" | Type: string | Sample values: ["EQ01", "EQ02", "EQ03"] | Unique count: 8
- Column: "PARA" | Type: string | Sample values: ["WIDTH", "THICKNESS"] | Unique count: 5
- Column: "VALUE" | Type: number | Sample values: [1.12, 1.08, 1.15] | Unique count: 200

## Sample Data (first 5 rows)
{sample_data}

## User Request (Korean)
"{user_request}"

# Output Requirements

Generate a JSON object with the following structure:

```json
{
  "schema_version": "1.0",
  "chart_type": "box_plot",
  "dataset_index": 0,
  "encodings": {
    "category": {
      "field": "COLUMN_NAME (for x-axis grouping)"
    },
    "value": {
      "field": "COLUMN_NAME (numerical values)"
    },
    "series": {
      "field": "COLUMN_NAME (optional, for sub-grouping)"
    }
  },
  "transforms": [],
  "layout": {
    "title": "Chart Title in Korean",
    "height": 500,
    // NOTE: Do NOT specify width - charts auto-fit to container
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },  // b: 150 for long x-axis labels
    "xaxis": {
      "title": "X Axis Label",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "Y Axis Label (Measurement)",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    }
  },
  "boxpoints": "outliers | all | false"
}
```

# Rules

1. **Column Selection**
   - category: Categorical column for x-axis (groups to compare)
   - value: Numerical column containing measurements
   - series: Optional second grouping dimension

2. **Box Points**
   - "outliers": Show only outlier points (default, recommended)
   - "all": Show all data points overlaid on boxes
   - false: Show only boxes without points

3. **Grouping Strategy**
   - Single grouping: Use only `category` field
     - Example: "장비별 분포" → category: "EQ"
   - Double grouping: Use both `category` and `series`
     - Example: "장비별, 파라미터별 분포" → category: "EQ", series: "PARA"
     - This creates multiple boxes per category

4. **Layout Customization**
   - Box plots benefit from grid lines for reading quartiles
   - Consider adding shapes for specification limits (USL/LSL)
   - Adjust x-axis tickangle if many categories
   - **DO NOT specify width** - charts auto-fit to container

5. **Filters**
   - Add filters to focus on specific subsets
   - Example: "불량이 있는 것만" → filter on defect > 0

6. **Common Use Cases**
   - "분포": Show distribution using box plot
   - "산포도": Could be box plot or scatter plot (ask for clarification)
   - "변동성": Box plot is ideal
   - "이상치": Use boxpoints: "outliers"

7. **Constraints**
   - ⚠️ Do NOT include actual data values in the spec
   - ⚠️ Only reference column names that exist in metadata
   - ⚠️ Return only valid JSON, no extra text

# Example Output

For request: "장비별 WIDTH 분포를 박스플롯으로 보여줘. 이상치도 표시해줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "box_plot",
  "dataset_index": 0,
  "encodings": {
    "category": { "field": "EQ" },
    "value": { "field": "WIDTH" }
  },
  "transforms": [],
  "layout": {
    "title": "장비별 WIDTH 분포",
    "height": 500,
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },
    "xaxis": {
      "title": "장비",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "WIDTH",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    }
  },
  "boxpoints": "outliers"
}
```

Now generate the graph_spec JSON based on the provided data and user request.
```

---

## 4️⃣ Scatter Plot Prompt

### 사용 시나리오
- 두 변수 간 상관관계 분석
- 패턴 및 클러스터 탐지
- 이상치 식별
- 회귀 분석 시각화

### Prompt Template

```
You are an expert data analyst specializing in creating Plotly chart specifications from Excel data.

# Task
Generate a `graph_spec` JSON object for a SCATTER PLOT based on the user's request and Excel data metadata.

# Input Data

## Excel Columns Metadata
{column_metadata}

Example format:
- Column: "TEMPERATURE" | Type: number | Sample values: [25.3, 26.1, 24.8] | Unique count: 150
- Column: "YIELD" | Type: number | Sample values: [98.5, 97.2, 99.1] | Unique count: 145
- Column: "DEVICE" | Type: string | Sample values: ["A1", "B2"] | Unique count: 3

## Sample Data (first 5 rows)
{sample_data}

## User Request (Korean)
"{user_request}"

# Output Requirements

Generate a JSON object with the following structure:

```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": {
      "field": "COLUMN_NAME",
      "type": "quantitative"
    },
    "y": {
      "field": "COLUMN_NAME",
      "type": "quantitative"
    },
    "series": {
      "field": "COLUMN_NAME (optional, for colored groups)"
    }
  },
  "transforms": [],
  "reference_lines": [
    {
      "type": "mean | average | horizontal | regression | linear",
      "name": "Line Name (optional)",
      "value": "number (for horizontal line)",
      "color": "red | blue | green | ...",
      "width": 2,
      "dash": "solid | dash | dot | dashdot"
    }
  ],
  "layout": {
    "title": "Chart Title in Korean",
    "height": 500,
    // NOTE: Do NOT specify width - charts auto-fit to container
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },  // b: 150 for consistency
    "xaxis": {
      "title": "X Axis Label",
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5",
      "zeroline": true,
      "zerolinecolor": "#999"
    },
    "yaxis": {
      "title": "Y Axis Label",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    }
  },
  "mode": "markers"
}
```

# Rules

1. **Column Selection**
   - X-axis: First numerical variable (independent variable)
   - Y-axis: Second numerical variable (dependent variable)
   - Series: Optional categorical variable for color-coding points

2. **Mode**
   - ⚠️ **DO NOT specify `mode` field for scatter plots!** Frontend automatically uses `"markers"`
   - If you specify `mode`, it will be ignored for scatter plots
   - Scatter plots ALWAYS use `"markers"` mode (points only, no lines)

3. **⭐ Reference Lines (CRITICAL - DEFAULT BEHAVIOR!)**
   
   **기본 동작: 모든 산점도에 회귀선이 자동으로 추가됩니다!**
   
   - 프론트엔드(App.vue)가 자동으로 기본 회귀선을 추가합니다
   - ⚠️ **IMPORTANT: LLM은 기본적으로 `reference_lines` 필드를 생략해야 합니다!**
   - 사용자가 명시적으로 추가 선을 요청한 경우에만 `reference_lines`를 포함하세요
   
   **사용자 요청에 따른 처리:**
   
   | 사용자 요청 | reference_lines 값 | 결과 |
   |-----------|-------------------|------|
   | 산점도만 요청 (기본) | **필드 생략** or `[]` | 산점도 + 회귀선 (자동) ✅ |
   | "평균선도 추가해줘" | `[{"type": "mean", ...}]` | 산점도 + 평균선만 (회귀선 없음) |
   | "회귀선과 평균선" | `[{"type": "regression", ...}, {"type": "mean", ...}]` | 산점도 + 회귀선 + 평균선 |
   | "목표값 80도 표시해줘" | `[{"type": "horizontal", "value": 80, ...}]` | 산점도 + 목표선만 (회귀선 없음) |
   | "회귀선과 목표값" | `[{"type": "regression", ...}, {"type": "horizontal", ...}]` | 산점도 + 회귀선 + 목표선 |
   
   **Available Line Types:**
   - `"regression"`: Linear regression line (자동 추가, 명시 불필요)
   - `"mean"` or `"average"`: Horizontal line at mean of y-values
   - `"horizontal"`: Fixed horizontal line (requires `value` parameter)
   
   **Styling Options:**
   ```json
   {
     "type": "mean | regression | horizontal",
     "name": "선 이름 (범례에 표시)",
     "value": 80,  // horizontal 타입만 필수
     "color": "red | blue | green | orange | purple | ...",
     "width": 2,   // 선 두께 (1-4 권장)
     "dash": "solid | dash | dot | dashdot"
   }
   ```
   
   **Examples:**
   ```json
   // ✅ RECOMMENDED: 기본 산점도 (회귀선 자동 추가)
   // reference_lines 필드를 아예 생략하거나 빈 배열로 보내세요!
   {
     "chart_type": "scatter_plot",
     "encodings": { ... }
     // reference_lines 필드 없음 or "reference_lines": []
   }
   
   // ✅ 평균선만 추가 (회귀선 없이)
   "reference_lines": [
     {
       "type": "mean",
       "name": "평균 수율",
       "color": "red",
       "width": 2,
       "dash": "dash"
     }
   ]
   
   // ✅ 회귀선 + 평균선 (명시적으로 둘 다)
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
       "name": "평균",
       "color": "red",
       "dash": "dash"
     }
   ]
   
   // ✅ 여러 참조선 (회귀선 + 평균선 + 목표선)
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
       "name": "평균",
       "color": "red",
       "dash": "dash"
     },
     {
       "type": "horizontal",
       "value": 80,
       "name": "목표 수율 (80%)",
       "color": "green",
       "width": 2,
       "dash": "dashdot"
     }
   ]
   ```
   
   **Keywords to Watch:**
   - No mention of lines → **OMIT `reference_lines` field** or USE `[]` (회귀선 자동 추가)
   - "평균", "평균선", "mean", "average" 만 언급 → ADD only `type: "mean"` in array (회귀선 없음)
   - "회귀선", "regression" 명시적 언급 → ADD `type: "regression"` in array
   - "목표", "기준", "목표값", "target", "threshold" 만 언급 → ADD only `type: "horizontal"` in array (회귀선 없음)
   - "회귀선과 평균선", "회귀선도" → ADD both `type: "regression"` and others in array

4. **Correlation Analysis**
   - Scatter plot is ideal for checking correlation
   - Keywords: "상관관계", "관계", "영향", "correlation"
   - If correlation mentioned, consider adding regression line

5. **Grouping by Series**
   - Use series field to color-code by category
   - Example: "장비별로 색깔 구분해서" → series: "DEVICE"
   - Creates separate trace for each unique series value

6. **Axis Configuration**
   - Don't use tickangle for scatter plots (numbers don't need rotation)
   - Both axes should show zeroline for reference
   - Grid lines help read exact values

7. **Layout Customization**
   - Keep margins balanced (scatter plots are usually square-ish)
   - Consider equal aspect ratio if variables have similar scales
   - **DO NOT specify width** - charts auto-fit to container

8. **Common Use Cases**
   - "산점도": Scatter plot
   - "상관관계": Scatter plot with regression line
   - "평균선 추가": Add mean reference line
   - "회귀선 그려줘": Add regression line
   - "분포도": Could be scatter or box plot (context dependent)
   - "관계 분석": Scatter plot

9. **Constraints**
   - ⚠️ Do NOT include actual data values in the spec
   - ⚠️ Only reference column names that exist in metadata
   - ⚠️ Return only valid JSON, no extra text

# Example Output

## Example 1: Basic Scatter Plot (회귀선 자동 추가)
**Request:** "온도와 수율의 상관관계를 산점도로 보여줘. 장비별로 색깔 구분해줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "TEMPERATURE", "type": "quantitative" },
    "y": { "field": "YIELD", "type": "quantitative" },
    "series": { "field": "DEVICE" }
  },
  "transforms": [],
  "layout": {
    "title": "온도와 수율의 상관관계",
    "height": 500,
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },
    "xaxis": {
      "title": "온도 (°C)",
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5",
      "zeroline": true,
      "zerolinecolor": "#999"
    },
    "yaxis": {
      "title": "수율 (%)",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true,
      "zerolinecolor": "#999"
    }
  }
}
```
**NOTE:** 
- `reference_lines` 필드가 없음 → 프론트엔드에서 회귀선 자동 추가!
- `mode` 필드 없음 → 프론트엔드에서 자동으로 `"markers"` 설정 (산점도는 점만 표시)
**Result:** Scatter points (by DEVICE) + automatic blue regression line

---

## Example 2: Scatter Plot with Additional Reference Lines
**Request:** "CPK 산점도 그려줘. 평균선이랑 목표값 1.33도 표시해줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "EQUIPMENT", "type": "categorical" },
    "y": { "field": "CPK", "type": "quantitative" }
  },
  "transforms": [],
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
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },
    "xaxis": {
      "title": "장비",
      "tickangle": -45,
      "tickfont": { "size": 10, "color": "#666" },
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "CPK",
      "showgrid": true,
      "gridcolor": "#d3d3d3",
      "zeroline": true
    }
  }
}
```
**NOTE:** 
- 추가 선을 요청했으므로 `reference_lines` 배열에 **회귀선도 명시적으로 포함**!
- `mode` 필드를 명시하지 마세요 (프론트엔드가 자동 처리)
**Result:** Scatter points + regression line (blue) + mean line (red) + target line (green)

---

## Example 3: Scatter Plot with Mean Line Only (회귀선 없이)
**Request:** "온도와 압력 산점도 그려줘. 평균선만 표시해줘"

```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "TEMPERATURE", "type": "quantitative" },
    "y": { "field": "PRESSURE", "type": "quantitative" }
  },
  "transforms": [],
  "reference_lines": [
    {
      "type": "mean",
      "name": "평균 압력",
      "color": "red",
      "width": 2,
      "dash": "dash"
    }
  ],
  "layout": {
    "title": "온도-압력 산점도",
    "height": 500,
    "margin": { "l": 80, "r": 80, "t": 100, "b": 150, "pad": 4 },
    "xaxis": {
      "title": "온도 (°C)",
      "showgrid": true,
      "gridcolor": "#e5e5e5"
    },
    "yaxis": {
      "title": "압력 (Pa)",
      "showgrid": true,
      "gridcolor": "#d3d3d3"
    }
  }
}
```
**NOTE:** `mode` 필드를 명시하지 마세요 (프론트엔드가 자동 처리)
**Result:** Scatter points + mean line only (no regression line)

---

Now generate the graph_spec JSON based on the provided data and user request.
```

---

## 📊 Graph Type Selection Guide

LLM이 적절한 그래프 타입을 선택하도록 돕는 가이드:

### 키워드 매핑

| 사용자 키워드 | 추천 그래프 타입 | 이유 |
|-------------|----------------|------|
| 바차트, 막대그래프, bar | Bar Graph | 명시적 요청 |
| 비교, 대비, compare | Bar Graph | 카테고리 간 비교 |
| 라인차트, 선그래프, line, 트렌드, trend | Line Graph | 명시적 요청 또는 시계열 |
| 변화, 추이, 시간에 따른 | Line Graph | 시간 순서 데이터 |
| 박스플롯, box, 분포, distribution | Box Plot | 통계적 분포 |
| 변동성, 산포, 이상치, outlier | Box Plot | 분산 및 이상치 분석 |
| 산점도, scatter, 상관관계, correlation | Scatter Plot | 변수 간 관계 |
| 관계, 영향 | Scatter Plot | 두 변수 비교 |

### 다중 그래프 키워드 인식

| 사용자 키워드 | 의미 | 처리 방법 |
|-------------|------|----------|
| 각각, 각, each | 카테고리별 개별 그래프 | `graph_specs` 배열 생성 |
| 분리, 분리해서, separate | 분리된 그래프 | `graph_specs` 배열 생성 |
| 별도, 별도로, individually | 개별 그래프 | `graph_specs` 배열 생성 |
| 나눠서, 나누어, split | 나뉜 그래프 | `graph_specs` 배열 생성 |
| 개별, 개별적으로, per | 각각의 그래프 | `graph_specs` 배열 생성 |
| ~별로 (Tech별로, 장비별로) | 카테고리별 | `graph_specs` 배열 생성 |

**다중 그래프 요청 패턴 분석:**

#### Pattern 1: 카테고리 값별 분리
- "각 Tech별로 트렌드를 보여줘" → 다중 그래프 (Tech 값별)
- "Tech별로 분리해서 그래프 그려줘" → 다중 그래프 (Tech 값별)
- "장비별로 개별 라인차트 생성해줘" → 다중 그래프 (장비별)
- "각 DEVICE마다 별도 그래프로" → 다중 그래프 (DEVICE별)

#### Pattern 2: 여러 컬럼별 분리
- "WIDTH, THICKNESS, DEPTH 각각에 대해 트렌드" → 다중 그래프 (Y축 컬럼별)
- "CPK와 YIELD를 각각 그래프로" → 다중 그래프 (측정값별)
- "A컬럼, B컬럼, C컬럼 각각 비교" → 다중 그래프 (컬럼별)

#### Pattern 3: 특정 값들만 선택
- "EQ01, EQ02, EQ03 각각에 대해" → 다중 그래프 (명시된 값들만)
- "Tech_A와 Tech_B만 분리해서" → 다중 그래프 (선택된 값들)

#### Pattern 4: 조합 패턴
- "Tech_A와 B 각각의 CPK와 YIELD" → 다중 그래프 (카테고리 × 측정값)
- "각 장비별로 WIDTH와 THICKNESS" → 다중 그래프 (장비 × 파라미터)

**vs. 단일 그래프 (Series 사용):**
- "Tech별 트렌드를 보여줘" → 단일 그래프 (series: TECH)
- "장비별 비교 그래프" → 단일 그래프 (series: 장비)
- "모든 Tech를 한 그래프에" → 단일 그래프 (series 사용)

### 데이터 특성 기반 선택

```
IF 사용자가 다중 그래프 키워드 사용 ("각각", "분리", "별도" 등):
    → graph_specs 배열 생성
    → 각 카테고리별로 필터 적용한 개별 스펙 생성
    → 각 스펙의 title에 카테고리명 포함

ELSE IF 사용자 요청 명시적:
    → 요청한 그래프 타입 사용 (단일 graph_spec)

ELSE IF x축이 날짜/시간 타입:
    → Line Graph

ELSE IF x축 카테고리 + y축 숫자 (집계):
    → Bar Graph

ELSE IF 분포 분석 요청 OR 이상치 탐지:
    → Box Plot

ELSE IF 두 개의 숫자형 컬럼 비교:
    → Scatter Plot

ELSE:
    → Bar Graph (기본값)
```

---

## 🔧 Implementation Notes

### 백엔드 구현 시 고려사항

1. **LLM API 호출 흐름 (개선)**
```python
def generate_graph_spec(df, user_request):
    # 1. 데이터 메타정보 추출
    column_metadata = extract_column_metadata(df)
    sample_data = df.head(5).to_dict('records')
    
    # 2. 다중 그래프 여부 판단
    is_multiple = should_create_multiple_graphs(user_request, column_metadata)
    
    # 3. 그래프 타입 결정
    graph_type = determine_graph_type(user_request)
    
    # 4. 적절한 프롬프트 선택
    if is_multiple:
        prompt = get_multiple_graphs_prompt_template(graph_type)
    else:
        prompt = get_single_graph_prompt_template(graph_type)
    
    # 5. 프롬프트에 데이터 삽입
    filled_prompt = prompt.format(
        column_metadata=column_metadata,
        sample_data=sample_data,
        user_request=user_request
    )
    
    # 6. LLM API 호출
    response = call_llm_api(filled_prompt)
    
    # 7. JSON 파싱 및 검증
    result = json.loads(response)
    
    if "graph_specs" in result:
        # 다중 그래프: 각 spec 검증
        for spec in result["graph_specs"]:
            validate_graph_spec(spec, df.columns)
        return result
    else:
        # 단일 그래프: spec 검증
        validate_graph_spec(result, df.columns)
        return {"graph_spec": result}
```

2. **다중 그래프 판단 로직**
```python
def should_create_multiple_graphs(user_request: str, column_metadata: dict) -> bool:
    """
    사용자 요청을 분석하여 다중 그래프 생성이 필요한지 판단
    """
    # Pattern 1: 카테고리 값별 분리 키워드
    category_keywords = ["각각", "각", "분리", "별도", "나눠서", "개별", "따로"]
    if any(keyword in user_request for keyword in category_keywords):
        return True
    
    # Pattern 2: 여러 컬럼 명시 ("A, B, C 각각")
    # 예: "WIDTH, THICKNESS, DEPTH 각각"
    columns = [col["name"] for col in column_metadata["columns"]]
    mentioned_columns = [col for col in columns if col in user_request]
    if len(mentioned_columns) >= 2 and any(k in user_request for k in ["각각", "각"]):
        return True
    
    # Pattern 3: 특정 값들 나열 ("EQ01, EQ02, EQ03 각각")
    # LLM에게 판단 위임 가능
    
    return False

def determine_multiple_graph_type(user_request: str, column_metadata: dict) -> str:
    """
    다중 그래프의 타입 결정: filter-based, encoding-based, combination 등
    """
    # Pattern A: 컬럼명이 여러 개 언급되면 encoding-based
    columns = [col["name"] for col in column_metadata["columns"]]
    mentioned_columns = [col for col in columns if col in user_request]
    
    if len(mentioned_columns) >= 2:
        return "encoding-based"  # Y축 컬럼이 다른 여러 그래프
    
    # Pattern B: "각 XXX별로" → filter-based
    category_pattern = r"각\s+(\w+)별로"
    if re.search(category_pattern, user_request):
        return "filter-based"  # 카테고리 값별로 필터링
    
    # Pattern C: 조합 키워드 감지
    if "각각" in user_request and "대해" in user_request:
        return "combination"  # 복합 패턴 (LLM에 위임)
    
    return "filter-based"  # 기본값
```

2. **다중 그래프 생성 전략**
```python
def create_multiple_graph_specs(df, user_request, graph_type, pattern_type):
    """
    다중 그래프 스펙 생성
    """
    if pattern_type == "filter-based":
        # 카테고리 값별 분리
        category_col = extract_category_column(user_request, df.columns)
        unique_values = df[category_col].unique()[:10]  # 최대 10개
        
        specs = []
        for value in unique_values:
            spec = create_single_spec(
                graph_type=graph_type,
                encodings=get_base_encodings(df, user_request),
                transforms=[
                    {"type": "filter", "field": category_col, "op": "==", "value": value}
                ],
                title=f"{value} Analysis"
            )
            specs.append(spec)
        return specs
    
    elif pattern_type == "encoding-based":
        # 여러 Y축 컬럼별 분리
        y_columns = extract_y_columns(user_request, df.columns)
        
        specs = []
        for col in y_columns:
            spec = create_single_spec(
                graph_type=graph_type,
                encodings={
                    "x": get_x_encoding(df),
                    "y": {"field": col, "type": "quantitative"},
                    "series": get_series_encoding(df) if needed else None
                },
                transforms=[{"type": "sort", ...}],
                title=f"{col} Analysis"
            )
            specs.append(spec)
        return specs
    
    elif pattern_type == "combination":
        # 조합: LLM에 위임하거나 매트릭스 생성
        categories = extract_categories(user_request, df)
        metrics = extract_metrics(user_request, df)
        
        specs = []
        for cat in categories:
            for metric in metrics:
                spec = create_single_spec(
                    graph_type=graph_type,
                    encodings={"y": {"field": metric, ...}},
                    transforms=[
                        {"type": "filter", "field": cat["field"], "op": "==", "value": cat["value"]}
                    ],
                    title=f"{cat['value']} {metric} Analysis"
                )
                specs.append(spec)
        return specs
    
    return []
```

3. **Error Handling**
   - LLM이 잘못된 컬럼명 생성 시 → 가장 유사한 실제 컬럼명으로 대체
   - JSON 파싱 실패 시 → 재시도 또는 기본 스펙 반환
   - 필수 필드 누락 시 → 기본값으로 채우기
   - 다중 그래프 개수 제한 → 최대 10개 (성능 고려)

4. **Optimization**
   - 샘플 데이터는 최대 5-10행으로 제한
   - 컬럼 메타정보에서 고유값은 최대 10개까지만 표시
   - 다중 그래프 시 고유값이 너무 많으면 (>15개) 경고 또는 상위 10개만 선택
   - 프롬프트 토큰 수 최적화

5. **Caching**
   - 동일한 데이터 + 동일한 요청 → 캐시된 결과 재사용
   - TTL: 세션 단위 또는 30분

---

## 📚 References

- [Plotly.js Documentation](https://plotly.com/javascript/)
- [Plotly Layout Reference](https://plotly.com/javascript/reference/layout/)
- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/plotly_customization_changes.md` - 커스터마이징 옵션
