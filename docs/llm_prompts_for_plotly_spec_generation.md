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

### 출력 형식

LLM은 반드시 **JSON 형식**으로 `graph_spec` 객체를 반환해야 합니다:

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

### 중요 제약사항

1. ⚠️ **실제 데이터 값을 포함하지 말 것** - 컬럼명 참조만 사용
2. ⚠️ **존재하지 않는 컬럼명 사용 금지** - 제공된 메타정보의 컬럼만 사용
3. ✅ **기본 레이아웃 옵션 적용** - 가독성 향상을 위한 커스터마이징
4. ✅ **한글 사용자 요청 이해** - 자연어 처리 필요

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

Now generate the graph_spec JSON based on the provided data and user request.
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
   - "markers": Points only (default for scatter)
   - "lines+markers": Add connecting lines (if temporal or ordered data)
   - "markers+text": Add labels to points (if few points)

3. **Reference Lines (IMPORTANT!)**
   - ⭐ **Scatter plots AUTOMATICALLY include regression line by default**
   - You don't need to add regression line unless user wants different options
   - If user wants ONLY scatter points without regression, use `reference_lines: []`
   - **Additional lines:**
     - Use `reference_lines` array to add MORE lines (in addition to default regression)
   - **Types:**
     - `"mean"` or `"average"`: Horizontal line at mean of y values
     - `"horizontal"`: Fixed horizontal line (requires `value`)
     - `"regression"` or `"linear"`: Linear regression line (already default)
   - **Examples:**
     ```json
     // Default - regression line added automatically
     "reference_lines": null  // or omit this field
     
     // Add mean line (in addition to default regression)
     "reference_lines": [
       { "type": "mean", "name": "평균", "color": "red", "dash": "dash" }
     ]
     
     // Multiple additional lines
     "reference_lines": [
       { "type": "mean", "name": "평균", "color": "red", "dash": "dash" },
       { "type": "horizontal", "value": 80, "name": "목표", "color": "green" }
     ]
     
     // NO regression line (only scatter points)
     "reference_lines": []
     ```
   - **When to use:**
     - Default: Do nothing (regression line auto-added)
     - User mentions: "평균선", "평균", "mean", "average" → ADD type: "mean"
     - User mentions: "목표", "기준", "target", "threshold" + value → ADD type: "horizontal"
     - User mentions: "회귀선 없이", "without regression" → SET reference_lines: []

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

For request: "온도와 수율의 상관관계를 산점도로 보여줘. 장비별로 색깔 구분해줘"

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
  // No reference_lines needed - regression line added automatically!
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
  },
  "mode": "markers"
}
```

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

### 데이터 특성 기반 선택

```
IF 사용자 요청 명시적:
    → 요청한 그래프 타입 사용

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

1. **LLM API 호출 흐름**
```python
def generate_graph_spec(df, user_request):
    # 1. 데이터 메타정보 추출
    column_metadata = extract_column_metadata(df)
    sample_data = df.head(5).to_dict('records')
    
    # 2. 그래프 타입 결정 (키워드 기반 또는 LLM)
    graph_type = determine_graph_type(user_request)
    
    # 3. 해당 그래프 타입의 프롬프트 선택
    prompt = get_prompt_template(graph_type)
    
    # 4. 프롬프트에 데이터 삽입
    filled_prompt = prompt.format(
        column_metadata=column_metadata,
        sample_data=sample_data,
        user_request=user_request
    )
    
    # 5. LLM API 호출
    response = call_llm_api(filled_prompt)
    
    # 6. JSON 파싱 및 검증
    graph_spec = json.loads(response)
    validate_graph_spec(graph_spec, df.columns)
    
    return graph_spec
```

2. **Error Handling**
   - LLM이 잘못된 컬럼명 생성 시 → 가장 유사한 실제 컬럼명으로 대체
   - JSON 파싱 실패 시 → 재시도 또는 기본 스펙 반환
   - 필수 필드 누락 시 → 기본값으로 채우기

3. **Optimization**
   - 샘플 데이터는 최대 5-10행으로 제한
   - 컬럼 메타정보에서 고유값은 최대 10개까지만 표시
   - 프롬프트 토큰 수 최적화

4. **Caching**
   - 동일한 데이터 + 동일한 요청 → 캐시된 결과 재사용
   - TTL: 세션 단위 또는 30분

---

## 📚 References

- [Plotly.js Documentation](https://plotly.com/javascript/)
- [Plotly Layout Reference](https://plotly.com/javascript/reference/layout/)
- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/plotly_customization_changes.md` - 커스터마이징 옵션
