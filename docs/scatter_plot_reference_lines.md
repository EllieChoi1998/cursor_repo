# Scatter Plot Reference Lines 기능

## 📋 개요

산점도(Scatter Plot)에 평균선, 회귀선, 목표값 선 등의 참조선(Reference Lines)을 추가할 수 있는 기능입니다.

## 🎯 해결하는 문제

### Before (문제점)
```
사용자: "산점도에 평균선 추가해줘"
결과: ❌ 평균선만 나오고 산점도 점들이 사라짐
또는
결과: ❌ 평균선이 아예 안 나옴
```

### After (해결)
```
사용자: "산점도에 평균선 추가해줘"
결과: ✅ 산점도 점들 + 평균선 (빨간 점선)
```

## 🔧 사용 방법

### 1. Reference Lines 타입

#### 1️⃣ Mean Line (평균선)
```json
{
  "chart_type": "scatter_plot",
  "reference_lines": [
    {
      "type": "mean",
      "name": "평균",
      "color": "red",
      "width": 2,
      "dash": "dash"
    }
  ]
}
```

**동작:**
- 모든 y 값의 평균을 계산
- x축 전체 범위에 걸쳐 수평선 그리기
- 자동으로 평균값 계산

#### 2️⃣ Regression Line (회귀선)
```json
{
  "chart_type": "scatter_plot",
  "reference_lines": [
    {
      "type": "regression",
      "name": "회귀선",
      "color": "blue",
      "width": 2,
      "dash": "solid"
    }
  ]
}
```

**동작:**
- 단순 선형 회귀 (y = mx + b) 계산
- 최소제곱법(Least Squares) 사용
- 전체 데이터 포인트 기반

**수식:**
```
slope (m) = (n*Σ(xy) - Σx*Σy) / (n*Σ(x²) - (Σx)²)
intercept (b) = (Σy - m*Σx) / n
```

#### 3️⃣ Horizontal Line (수평선 - 목표값/기준값)
```json
{
  "chart_type": "scatter_plot",
  "reference_lines": [
    {
      "type": "horizontal",
      "value": 80,
      "name": "목표값",
      "color": "green",
      "width": 2,
      "dash": "dash"
    }
  ]
}
```

**동작:**
- 지정된 y 값에 수평선 그리기
- `value` 필수

### 2. 스타일 옵션

| 속성 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `type` | string | **필수** | "mean", "regression", "horizontal" |
| `name` | string | 타입별 기본값 | 범례에 표시될 이름 |
| `value` | number | - | horizontal 타입에서 필수 |
| `color` | string | "red" | 선 색상 (CSS 색상) |
| `width` | number | 2 | 선 두께 (픽셀) |
| `dash` | string | "dash" | "solid", "dash", "dot", "dashdot" |

### 3. 여러 참조선 동시 추가

```json
{
  "chart_type": "scatter_plot",
  "reference_lines": [
    {
      "type": "mean",
      "name": "평균",
      "color": "red",
      "dash": "dash"
    },
    {
      "type": "regression",
      "name": "추세선",
      "color": "blue",
      "dash": "solid"
    },
    {
      "type": "horizontal",
      "value": 90,
      "name": "목표 (90%)",
      "color": "green",
      "dash": "dot"
    }
  ]
}
```

**결과:**
- 산점도 점들 + 평균선 (빨간 점선) + 회귀선 (파란 실선) + 목표선 (녹색 점선)
- 각 선이 범례에 표시됨

## 📊 사용 예시

### 예시 1: 온도와 수율 상관관계 분석

**사용자 요청:**
> "온도와 수율의 산점도를 그려주고, 회귀선도 추가해줘"

**LLM이 생성할 graph_spec:**
```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "TEMPERATURE", "type": "quantitative" },
    "y": { "field": "YIELD", "type": "quantitative" }
  },
  "reference_lines": [
    {
      "type": "regression",
      "name": "회귀선",
      "color": "blue",
      "width": 2,
      "dash": "solid"
    }
  ],
  "layout": {
    "title": "온도와 수율의 상관관계",
    "xaxis": { "title": "온도 (°C)" },
    "yaxis": { "title": "수율 (%)" }
  },
  "mode": "markers"
}
```

**결과:**
- 각 데이터 포인트가 점으로 표시
- 파란색 실선 회귀선이 추세를 표시
- 온도 증가에 따른 수율 변화 경향 명확히 파악

### 예시 2: CPK 산점도 + 평균 및 목표

**사용자 요청:**
> "장비별 CPK 산점도 그리고, 평균선이랑 목표값 1.33도 표시해줘"

**LLM이 생성할 graph_spec:**
```json
{
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
    "xaxis": { "title": "장비" },
    "yaxis": { "title": "CPK" }
  },
  "mode": "markers"
}
```

**결과:**
- 각 장비의 CPK 값이 점으로 표시
- 디바이스별로 색상 구분
- 빨간 점선: 전체 평균 CPK
- 녹색 점-대시선: 목표 CPK 1.33

### 예시 3: 시간에 따른 측정값 + 관리 한계선

**사용자 요청:**
> "시간별 측정값 산점도에 상한 100, 하한 50 기준선 추가해줘"

**LLM이 생성할 graph_spec:**
```json
{
  "schema_version": "1.0",
  "chart_type": "scatter_plot",
  "dataset_index": 0,
  "encodings": {
    "x": { "field": "TIMESTAMP", "type": "temporal" },
    "y": { "field": "MEASUREMENT", "type": "quantitative" }
  },
  "reference_lines": [
    {
      "type": "horizontal",
      "value": 100,
      "name": "UCL (상한)",
      "color": "red",
      "width": 2,
      "dash": "dash"
    },
    {
      "type": "horizontal",
      "value": 50,
      "name": "LCL (하한)",
      "color": "red",
      "width": 2,
      "dash": "dash"
    }
  ],
  "layout": {
    "title": "시간별 측정값 분포",
    "xaxis": { "title": "시간" },
    "yaxis": { "title": "측정값" }
  },
  "mode": "markers"
}
```

## 🎨 색상 및 스타일 가이드

### 권장 색상

| 선 타입 | 권장 색상 | 이유 |
|--------|----------|------|
| 평균선 (mean) | red | 주의를 끌기 쉬움 |
| 회귀선 (regression) | blue | 전통적인 추세선 색상 |
| 목표값 (target) | green | 달성해야 할 값 |
| 상한 (UCL) | red | 경고 |
| 하한 (LCL) | red | 경고 |
| 기준값 (reference) | orange | 중립적 참조 |

### Dash 스타일

```
"solid"    ────────────  실선 (회귀선, 주요 기준선)
"dash"     ─ ─ ─ ─ ─ ─  긴 점선 (평균선, 목표값)
"dot"      ∙∙∙∙∙∙∙∙∙∙∙∙  점선 (보조 기준선)
"dashdot"  ─∙─∙─∙─∙─∙  점-대시 (복합 기준선)
```

## 🔧 구현 상세

### App.vue의 buildLineFigure 함수

```javascript
// 산점도 trace 생성 (기본)
const traces = [...scatter points...]

// reference_lines 처리
if (chartType === 'scatter' && spec.reference_lines) {
  spec.reference_lines.forEach((refLine) => {
    if (refLine.type === 'mean') {
      // 평균 계산 및 수평선 trace 추가
    } else if (refLine.type === 'horizontal') {
      // 고정값 수평선 trace 추가
    } else if (refLine.type === 'regression') {
      // 선형 회귀 계산 및 선 trace 추가
    }
  })
}

return { data: traces, layout, config }
```

### 작동 원리

1. **산점도 trace 생성**
   - mode: 'markers'
   - 각 데이터 포인트를 점으로 표시

2. **참조선 trace 추가**
   - mode: 'lines'
   - 계산된 값으로 선 그리기
   - 범례에 이름 표시

3. **최종 data 배열**
   ```javascript
   data: [
     { /* scatter trace 1 */ },
     { /* scatter trace 2 */ },
     { /* mean line trace */ },
     { /* regression line trace */ }
   ]
   ```

## ⚠️ 주의사항

### 1. X축 값 타입
- **숫자형 X**: 문제없음
- **카테고리형 X**: 선이 전체 범위에 걸쳐 그려짐
- **날짜형 X**: 현재 구현에서는 제한적 지원

### 2. 회귀선 계산
- 단순 선형 회귀만 지원
- 다항식 회귀나 비선형 회귀는 미지원
- 모든 데이터 포인트 기반 (series 구분 없음)

### 3. 데이터 개수
- 데이터가 너무 적으면 회귀선이 부정확
- 최소 10개 이상의 데이터 권장

### 4. 범례
- 모든 참조선이 범례에 표시됨
- 이름을 명확하게 지정하는 것이 중요

## 🐛 문제 해결

### Q: 산점도는 안 나오고 선만 나와요
**A:** 이제 해결되었습니다! `reference_lines` 배열을 사용하면 산점도와 선이 함께 표시됩니다.

### Q: 회귀선이 이상해요
**A:** 데이터에 이상치(outlier)가 있거나 데이터가 너무 적을 수 있습니다. 데이터 전처리 또는 필터링을 권장합니다.

### Q: 평균선이 틀려요
**A:** 모든 시리즈의 y 값을 합쳐서 평균을 계산합니다. 시리즈별 평균이 필요하면 별도 구현 필요합니다.

### Q: 여러 개의 회귀선을 그릴 수 있나요? (시리즈별)
**A:** 현재는 전체 데이터 기반 회귀선만 지원합니다. 향후 업데이트 예정입니다.

## 🚀 향후 개선 계획

### 단기 (1-2주)
- [ ] 시리즈별 회귀선 지원
- [ ] 다항식 회귀 (2차, 3차)
- [ ] 중앙값(median) 선

### 중기 (1-2개월)
- [ ] 신뢰구간(confidence interval) 표시
- [ ] 사분위수 선
- [ ] 커스텀 수식 지원

### 장기 (3개월+)
- [ ] 로그/지수 회귀
- [ ] 다변량 회귀
- [ ] 이동평균선

## 📚 관련 문서

- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/llm_prompts_for_plotly_spec_generation.md` - LLM 프롬프트 (Scatter Plot 섹션)
- `/docs/plotly_customization_changes.md` - 기본 커스터마이징

## 🎉 요약

**핵심 기능:**
- ✅ 산점도 + 평균선
- ✅ 산점도 + 회귀선
- ✅ 산점도 + 목표값/기준선
- ✅ 여러 참조선 동시 표시
- ✅ 범례 자동 생성

**장점:**
- 데이터 패턴 파악 용이
- 목표 대비 현황 비교
- 상관관계 시각화
- 통계적 분석 지원

---

**Last Updated:** 2025-12-04  
**Version:** 1.0  
**Feature:** Scatter Plot Reference Lines
