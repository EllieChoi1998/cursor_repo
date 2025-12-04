# PlotlyGraph 세로 스크롤 기능 추가

## 📋 개요

엑셀 데이터 분석에서 생성되는 PlotlyGraph에 세로 스크롤 기능을 추가했습니다. 차트 높이가 너무 클 때 사용자가 세로 스크롤로 편하게 볼 수 있습니다.

## 🎯 해결하는 문제

### Before (문제점)
- ❌ 차트 높이가 클 때 전체 화면을 차지해서 불편
- ❌ 다른 콘텐츠를 보려면 페이지를 많이 스크롤해야 함
- ❌ 여러 차트가 있을 때 비교하기 어려움

### After (해결)
- ✅ 차트가 최대 600px 높이로 제한
- ✅ 세로 스크롤로 차트 내부를 탐색
- ✅ 다른 콘텐츠와 함께 보기 편함
- ✅ 세련된 스크롤바 스타일링
- ✅ 부드러운 스크롤 경험
- ✅ 차트가 화면 너비에 맞춰져서 트렌드가 명확하게 보임

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

#### 1.2 Plotly Config 유지

```javascript
const config = {
  displaylogo: false,
  responsive: true,  // ✅ 차트가 화면 너비에 맞춰짐
  scrollZoom: true,
  ...parsedSpec.value.config
}
```

**설정 이유:**
- `responsive: true`로 차트가 컨테이너 너비에 자동으로 맞춰짐
- 트렌드가 명확하게 보임
- 세로 스크롤만 활성화

#### 1.3 CSS 스타일 추가

```css
/* Scrollable wrapper for the chart - VERTICAL SCROLL ONLY */
.plotly-scroll-wrapper {
  width: 100%;
  max-width: 100%;
  max-height: 600px;       /* 최대 높이 제한 */
  overflow-x: hidden;      /* 가로 스크롤 비활성화 */
  overflow-y: auto;        /* 세로 스크롤만 활성화 */
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
  width: 100%;             /* 부모 너비에 맞춤 (responsive) */
  min-height: 360px;
  background: #fff;
}
```

**특징:**
- 최대 높이: 600px 제한
- 세로 스크롤만 활성화 (가로 스크롤 비활성화)
- 스크롤바 스타일링: 얇고 세련된 디자인
- 브라우저 호환성: Chrome/Safari (webkit), Firefox (표준)
- 부드러운 스크롤: `scroll-behavior: smooth`
- 차트는 화면 너비에 맞춰짐 (트렌드 명확)

### 2. App.vue 변경사항

#### 2.1 변경 없음 (원래대로 유지)

차트 너비는 컨테이너에 맞춰 자동 조절됩니다 (`responsive: true`).

모든 그래프 타입의 기본 레이아웃:

```javascript
const defaultLayout = {
  height: 500,
  margin: { l: 80, r: 80, t: 100, b: 100, pad: 4 },
  xaxis: { /* ... */ },
  yaxis: { /* ... */ }
}
```

**특징:**
- 너비는 자동으로 컨테이너에 맞춰짐
- 높이는 500px 고정
- 높이가 600px를 넘으면 세로 스크롤 표시

### 3. 동작 원리

```
1. App.vue: 그래프 스펙 생성
   └─> layout.height = 500px

2. graph_spec 전달
   └─> PlotlyGraph.vue로 전달

3. PlotlyGraph.vue
   ├─> responsive: true 설정
   ├─> Plotly가 컨테이너 너비에 맞춰 차트 렌더링
   └─> plotly-container는 부모 너비 100%

4. plotly-scroll-wrapper
   ├─> max-height: 600px
   ├─> overflow-y: auto
   └─> 차트 높이 > 600px → 세로 스크롤바 표시 ✅

5. 사용자
   ├─> 차트가 화면 너비에 딱 맞음 (트렌드 명확)
   └─> 세로 스크롤로 차트 탐색 가능 🎉
```

## 📊 사용 예시

### 예시 1: 높이가 큰 차트

**Before:**
```
차트가 화면 전체를 차지
↓
↓ 스크롤 많이 필요
↓
다음 콘텐츠
```

**After:**
```
차트 (최대 600px)
  ↕ 세로 스크롤
다음 콘텐츠 (바로 보임)
```

### 예시 2: 트렌드 분석

**Before (가로 스크롤 시):**
```
← 스크롤 → 해야 트렌드 파악
일부만 보여서 전체 패턴 파악 어려움
```

**After (화면 너비 맞춤):**
```
[============================] 전체 트렌드 한눈에
↑↓ 필요시 세로 스크롤만
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

### 백엔드에서 높이 직접 지정

LLM 또는 백엔드에서 `graph_spec.layout.height`를 명시:

```python
graph_spec = {
    "layout": {
        "height": 700,  # 더 큰 높이 사용
        # width는 자동으로 컨테이너에 맞춰짐
    }
}
```

### 프론트엔드에서 최대 높이 조정

`PlotlyGraph.vue`에서 상수 수정:

```css
.plotly-scroll-wrapper {
  max-height: 600px;  /* 기본값 - 필요시 조정 */
}
```

### 스크롤 비활성화

특정 상황에서 스크롤을 원하지 않으면:

```css
.plotly-scroll-wrapper {
  max-height: none;      /* 높이 제한 해제 */
  overflow-y: hidden;    /* 세로 스크롤 끄기 */
}
```

## 🧪 테스트 시나리오

### 시나리오 1: 기본 높이 차트 (500px 이하)
- ✅ 세로 스크롤바 표시 안 됨
- ✅ 차트가 화면 너비에 맞춰짐
- ✅ 기존과 동일한 UX

### 시나리오 2: 높이가 큰 차트 (600px 이상)
- ✅ 세로 스크롤바 표시
- ✅ 최대 높이 600px로 제한
- ✅ 스크롤로 차트 전체 탐색 가능

### 시나리오 3: 많은 데이터 포인트
- ✅ 차트가 화면 너비에 맞춰짐
- ✅ 트렌드가 명확하게 보임
- ✅ x축 라벨이 적절히 표시됨 (tickangle 적용)

### 시나리오 4: 여러 차트 비교
- ✅ 각 차트가 600px 이하로 유지
- ✅ 페이지 스크롤 없이 여러 차트 한눈에 비교 가능
- ✅ 필요한 차트만 세로 스크롤로 탐색

## 📐 권장 사항

### 차트 높이별 권장 설정

| 차트 높이 | 스크롤 | UX 상태 | 권장 사항 |
|----------|-------|---------|---------|
| < 400px | 없음 | 최적 | 기본 설정으로 충분 |
| 400-600px | 없음 | 좋음 | 적절한 크기 |
| 600-800px | 세로 스크롤 | 양호 | 스크롤 유용 |
| > 800px | 세로 스크롤 | 주의 | 높이 조절 권장 |

### UX 개선 팁

1. **차트 높이 조절**
   - 기본 높이 500px이 대부분의 경우 적절
   - 필요시 LLM에게 높이 조절 요청

2. **긴 라벨 처리**
   - tickangle: -45 또는 -90도 (기본 적용됨)
   - tickfont.size: 10px (기본 적용됨)
   - 약어 사용 권장

3. **트렌드 분석**
   - 차트가 화면 너비에 맞춰져서 전체 트렌드 파악 용이
   - 세로 스크롤로 상세 정보 확인

## 🐛 알려진 제한사항

1. **매우 높은 차트**
   - 세로 스크롤이 길어질 수 있음
   - 권장: 적절한 높이 설정 (500-700px)

2. **많은 데이터 포인트**
   - 차트가 화면 너비에 맞춰지므로 라벨이 겹칠 수 있음
   - 해결: tickangle 조절, 폰트 크기 축소 (기본 적용됨)
   - 권장: 매우 많은 데이터는 필터링/집계

3. **인쇄/PDF 출력**
   - 스크롤 영역은 잘릴 수 있음
   - 해결: 전체 화면 모드 후 출력 또는 높이 조절

## 🔗 관련 문서

- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/plotly_customization_changes.md` - 커스터마이징 옵션
- `/docs/llm_prompts_for_plotly_spec_generation.md` - LLM 프롬프트
- [Plotly.js Configuration](https://plotly.com/javascript/configuration-options/)
