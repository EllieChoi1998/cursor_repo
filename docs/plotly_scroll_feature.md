# PlotlyGraph 스크롤 기능 추가

## 📋 개요

엑셀 데이터 분석에서 생성되는 PlotlyGraph에 가로/세로 스크롤 기능을 추가했습니다. x축 라벨이 너무 많거나 길 때, 차트가 자동으로 너비를 늘리고 사용자가 스크롤해서 전체 데이터를 볼 수 있습니다.

## 🎯 해결하는 문제

### Before (문제점)
- ❌ x축 카테고리가 많을 때 라벨이 겹쳐서 읽기 어려움
- ❌ 모든 데이터를 한 화면에 우겨넣어서 차트가 복잡해짐
- ❌ 긴 x축 라벨이 잘리거나 가독성이 떨어짐
- ❌ 100개 이상의 데이터 포인트가 있을 때 시각화 품질 저하

### After (해결)
- ✅ 데이터 포인트 수에 따라 차트 너비 자동 증가
- ✅ 가로 스크롤로 모든 데이터를 명확하게 확인 가능
- ✅ 각 라벨/데이터 포인트가 충분한 공간 확보
- ✅ 세련된 스크롤바 스타일링
- ✅ 부드러운 스크롤 경험

## 🔧 구현 상세

### 1. PlotlyGraph.vue 변경사항

#### 1.1 템플릿 구조 변경

**스크롤 가능한 래퍼 추가:**

```vue
<template>
  <div class="plotly-graph-wrapper">
    <!-- ... file name, messages ... -->
    
    <!-- NEW: Scrollable container wrapper -->
    <div class="plotly-scroll-wrapper">
      <div ref="chartContainer" class="plotly-container"></div>
    </div>
  </div>
</template>
```

**변경 이유:**
- `plotly-scroll-wrapper`: 스크롤바를 표시할 외부 컨테이너
- `plotly-container`: 실제 차트가 렌더링되는 내부 컨테이너

#### 1.2 Plotly Config 변경

```javascript
// Before
const config = {
  displaylogo: false,
  responsive: true,  // ❌ 스크롤과 충돌
  scrollZoom: true,
  ...parsedSpec.value.config
}

// After
const config = {
  displaylogo: false,
  responsive: false,  // ✅ 고정 크기로 스크롤 활성화
  scrollZoom: true,
  ...parsedSpec.value.config
}
```

**변경 이유:**
- `responsive: true`는 차트를 컨테이너에 맞춰 자동 조절 → 스크롤 불가능
- `responsive: false`로 설정하면 `layout.width`에 지정된 크기 유지 → 스크롤 가능

#### 1.3 CSS 스타일 추가

```css
/* Scrollable wrapper for the chart */
.plotly-scroll-wrapper {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;      /* 가로 스크롤 */
  overflow-y: auto;      /* 세로 스크롤 */
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  scroll-behavior: smooth;  /* 부드러운 스크롤 */
  
  /* 커스텀 스크롤바 (Firefox) */
  scrollbar-width: thin;
  scrollbar-color: #999 #f1f1f1;
}

/* 커스텀 스크롤바 (Chrome, Safari, Edge) */
.plotly-scroll-wrapper::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.plotly-scroll-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.plotly-scroll-wrapper::-webkit-scrollbar-thumb {
  background: #999;
  border-radius: 4px;
}

.plotly-scroll-wrapper::-webkit-scrollbar-thumb:hover {
  background: #666;
}

.plotly-container {
  min-width: 100%;       /* 최소한 부모 너비만큼 */
  min-height: 360px;
  background: #fff;
}
```

**특징:**
- 스크롤바 스타일링: 얇고 세련된 디자인
- 브라우저 호환성: Chrome/Safari (webkit), Firefox (표준)
- 부드러운 스크롤: `scroll-behavior: smooth`

### 2. App.vue 변경사항

#### 2.1 동적 너비 계산 로직 추가

각 그래프 타입별로 데이터 포인트 수에 따라 차트 너비를 자동 계산합니다.

**Bar Graph (`buildBarFigure`)**

```javascript
// Calculate dynamic width based on number of x-axis categories
const uniqueXValues = new Set()
data.forEach(trace => trace.x.forEach(x => uniqueXValues.add(x)))
const xCount = uniqueXValues.size

const minWidth = 800                    // 최소 너비
const widthPerCategory = 60             // 카테고리당 60px
const calculatedWidth = Math.max(minWidth, xCount * widthPerCategory)

const defaultLayout = {
  height: 500,
  width: calculatedWidth,  // 동적 너비 적용
  // ...
}
```

**계산 공식:**
- 최소 너비: 800px (화면에 딱 맞음)
- x축 카테고리 20개: 800px (최소값 유지)
- x축 카테고리 50개: 3000px (스크롤 필요)
- 카테고리당 60px씩 공간 확보

**Line Graph (`buildLineFigure`)**

```javascript
const uniqueXValues = new Set()
traces.forEach(trace => trace.x.forEach(x => uniqueXValues.add(x)))
const xCount = uniqueXValues.size

const minWidth = 800
const widthPerPoint = 40                // 포인트당 40px (바차트보다 작음)
const calculatedWidth = Math.max(minWidth, xCount * widthPerPoint)
```

**차이점:**
- 라인 그래프는 포인트가 연속적이므로 40px만 할당
- 바차트보다 공간 효율적

**Box Plot (`buildBoxFigure`)**

```javascript
const boxCount = data.length

const minWidth = 800
const widthPerBox = 80                  // 박스당 80px (가장 넓음)
const calculatedWidth = Math.max(minWidth, boxCount * widthPerBox)
```

**차이점:**
- 박스 플롯은 각 박스가 넓은 공간 필요
- 박스당 80px 할당

#### 2.2 너비 계산 비교표

| 그래프 타입 | 최소 너비 | 단위당 공간 | 30개 데이터 시 너비 | 100개 데이터 시 너비 |
|------------|---------|-----------|------------------|-------------------|
| Bar Graph | 800px | 60px | 1800px | 6000px |
| Line Graph | 800px | 40px | 1200px | 4000px |
| Box Plot | 800px | 80px | 2400px | 8000px |

### 3. 동작 원리

```
1. App.vue: 데이터 분석
   └─> x축 카테고리/포인트 개수 계산
   └─> 동적 너비 계산 (예: 50개 × 60px = 3000px)

2. graph_spec.layout.width = 3000px
   └─> PlotlyGraph.vue로 전달

3. PlotlyGraph.vue
   ├─> responsive: false 설정
   ├─> Plotly가 3000px 너비로 차트 렌더링
   └─> plotly-container 실제 너비 = 3000px

4. plotly-scroll-wrapper
   ├─> max-width: 100% (부모 컨테이너 너비)
   ├─> overflow-x: auto
   └─> 3000px > 부모 너비 → 가로 스크롤바 표시 ✅

5. 사용자
   └─> 스크롤로 전체 차트 탐색 가능 🎉
```

## 📊 사용 예시

### 예시 1: 장비가 50개인 바차트

**Before:**
```
[============================] 800px
장비1 장비2 장비3 ... 장비50
↑ 겹쳐서 읽기 어려움
```

**After:**
```
[=========      ] 화면 800px
← 스크롤 →
[====================] 차트 3000px
장비1  장비2  장비3  ...  장비50
↑ 각 라벨이 명확하게 보임
```

### 예시 2: 100일치 트렌드 라인차트

**Before:**
```
모든 점이 뭉개져서 트렌드 파악 어려움
```

**After:**
```
차트 너비 4000px로 확장
→ 각 날짜별 포인트가 명확
→ 스크롤로 전체 기간 탐색
```

## 🎨 스크롤바 스타일

### 데스크톱 브라우저

- **Chrome/Edge/Safari**: 커스텀 webkit 스크롤바
  - 너비: 10px
  - 색상: 회색 (#999)
  - Hover: 진한 회색 (#666)
  - 배경: 연한 회색 (#f1f1f1)

- **Firefox**: 표준 스크롤바
  - `scrollbar-width: thin`
  - `scrollbar-color: #999 #f1f1f1`

### 모바일

- 터치 스크롤 자동 지원
- 스크롤바는 스크롤 중에만 표시 (OS 기본 동작)

## ⚙️ 커스터마이징 옵션

### 백엔드에서 너비 직접 지정

LLM 또는 백엔드에서 `graph_spec.layout.width`를 명시하면 자동 계산을 덮어씁니다:

```python
graph_spec = {
    "layout": {
        "width": 1500,  # 강제로 1500px 너비 사용
        "height": 600,
        # ...
    }
}
```

### 프론트엔드에서 최소/최대 너비 조정

`App.vue`에서 상수 수정:

```javascript
// Bar Graph
const minWidth = 800        // 최소 너비 조정
const widthPerCategory = 60 // 카테고리당 공간 조정
const maxWidth = 10000      // 최대 너비 제한 (선택사항)
```

### 스크롤 비활성화

특정 상황에서 스크롤을 원하지 않으면:

```css
.plotly-scroll-wrapper {
  overflow-x: hidden;  /* 가로 스크롤 끄기 */
  overflow-y: hidden;  /* 세로 스크롤 끄기 */
}
```

또는 `responsive: true`로 복구:

```javascript
const config = {
  responsive: true,  // 원래대로 복구
  // ...
}
```

## 🧪 테스트 시나리오

### 시나리오 1: 적은 데이터 (10개 미만)
- ✅ 차트 너비 800px 유지 (최소값)
- ✅ 스크롤바 표시 안 됨
- ✅ 기존과 동일한 UX

### 시나리오 2: 중간 데이터 (10-30개)
- ✅ 차트 너비 자동 증가 (800px ~ 1800px)
- ✅ 화면 크기에 따라 스크롤바 표시 여부 결정
- ✅ 큰 모니터에서는 스크롤 없이 전체 표시 가능

### 시나리오 3: 많은 데이터 (50개 이상)
- ✅ 차트 너비 크게 증가 (3000px+)
- ✅ 가로 스크롤바 표시
- ✅ 각 데이터 포인트가 충분한 공간 확보
- ✅ 부드러운 스크롤 경험

### 시나리오 4: 매우 긴 x축 라벨
- ✅ tickangle: -45도로 라벨 기울임
- ✅ 카테고리당 60px 공간 확보
- ✅ 하단 마진 증가로 라벨 잘림 방지
- ✅ 스크롤로 모든 라벨 읽기 가능

## 📐 권장 사항

### 데이터 개수별 권장 설정

| 데이터 개수 | 그래프 타입 | 예상 너비 | 스크롤 | 권장 사항 |
|-----------|----------|---------|-------|---------|
| < 15개 | 모든 타입 | 800px | 없음 | 기본 설정으로 충분 |
| 15-30개 | Bar/Box | 1200-1800px | 경우에 따라 | 적절함 |
| 30-50개 | Bar/Box | 1800-3000px | 필요 | 스크롤 유용 |
| 50-100개 | Bar/Box | 3000-6000px | 필수 | 스크롤 + 필터링 권장 |
| > 100개 | 모든 타입 | 6000px+ | 필수 | 데이터 필터링 또는 집계 권장 |

### UX 개선 팁

1. **데이터가 너무 많을 때 (100개+)**
   - LLM에게 자동 필터링/그룹화 요청
   - 예: "상위 20개만", "주요 항목만"

2. **긴 라벨 처리**
   - tickangle: -45 또는 -90도
   - tickfont.size: 9-10px
   - 약어 사용 권장

3. **시간 데이터**
   - 날짜 포맷 단순화 (YYYY-MM-DD → MM/DD)
   - 적절한 간격으로 샘플링

## 🐛 알려진 제한사항

1. **매우 큰 데이터셋 (1000개+)**
   - 브라우저 성능 저하 가능
   - 권장: 백엔드에서 집계 또는 샘플링

2. **모바일 환경**
   - 작은 화면에서 스크롤이 번거로울 수 있음
   - 권장: 모바일에서는 데이터 개수 제한

3. **인쇄/PDF 출력**
   - 스크롤 영역은 잘릴 수 있음
   - 해결: 전체 화면 모드 후 출력

## 🔗 관련 문서

- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/plotly_customization_changes.md` - 커스터마이징 옵션
- `/docs/llm_prompts_for_plotly_spec_generation.md` - LLM 프롬프트
- [Plotly.js Configuration](https://plotly.com/javascript/configuration-options/)
