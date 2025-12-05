# PlotlyGraph 커스터마이징 옵션 추가 - 변경사항

## 📋 개요

엑셀 데이터 분석에서 생성되는 모든 그래프 유형(bar_graph, line_graph, box_plot)에 대해 다음 커스터마이징 옵션들을 추가했습니다:

1. ✅ **그래프 높이/크기 조절** - 차트 크기 및 autosize
2. ✅ **마진 조절** - 좌/우/상/하 마진 설정
3. ✅ **X축 커스터마이징** - 폰트 크기, 각도, 그리드 라인
4. ✅ **Y축 커스터마이징** - 범위, 그리드 라인, zeroline
6. ✅ **기준선(Shapes) 추가** - 수평/수직 참조선

## 📝 변경된 파일

### 1. `/docs/excel_analysis_response_formats.md`

#### 추가된 섹션
- **3.3 Layout Customization Options** - 상세한 커스터마이징 옵션 문서
  - 차트 크기 & 마진 설정
  - X축 커스터마이징 (tickangle, tickfont, showgrid 등)
  - Y축 커스터마이징 (range, gridcolor, zeroline 등)
  - 기준선 & Shapes 추가 방법
  - 완전한 예제 포함

#### 업데이트된 예제들
- 4.2 Box Plot Result - 기본 커스터마이징 적용
- 4.3 Line Graph Result - 기본 커스터마이징 + shapes 예제 적용
- 4.4 Bar Graph Result - 기본 커스터마이징 적용

### 2. `/src/App.vue`

#### 추가된 함수
```javascript
// Deep merge helper function
const mergeDeep = (source, target) => { ... }
```
- 기본 레이아웃과 사용자 레이아웃을 깊게 병합
- 사용자 설정(target)이 항상 우선권을 가짐

#### 수정된 함수들

**1) `buildBarFigure()`**
```javascript
const defaultLayout = {
  height: 500,
  margin: { l: 80, r: 80, t: 100, b: 100, pad: 4 },
  xaxis: {
    tickangle: -45,
    tickfont: { size: 10, color: '#666' },
    showgrid: true,
    gridcolor: '#e5e5e5',
    gridwidth: 1
  },
  yaxis: {
    showgrid: true,
    gridcolor: '#d3d3d3',
    gridwidth: 1,
    zeroline: true,
    zerolinecolor: '#999',
    zerolinewidth: 2
  }
}
const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})
```

**2) `buildLineFigure()`**
```javascript
const defaultLayout = {
  height: 500,
  margin: { l: 80, r: 80, t: 100, b: 120, pad: 4 },
  xaxis: {
    tickangle: -45,
    tickfont: { size: 10, color: '#666' },
    showgrid: true,
    gridcolor: '#e5e5e5',
    gridwidth: 1
  },
  yaxis: {
    showgrid: true,
    gridcolor: '#d3d3d3',
    gridwidth: 1,
    griddash: 'dot',
    zeroline: true,
    zerolinecolor: '#999',
    zerolinewidth: 2
  }
}
const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})
```

**3) `buildBoxFigure()`**
```javascript
const defaultLayout = {
  height: 500,
  margin: { l: 80, r: 80, t: 100, b: 100, pad: 4 },
  xaxis: {
    tickangle: -45,
    tickfont: { size: 10, color: '#666' },
    showgrid: true,
    gridcolor: '#e5e5e5',
    gridwidth: 1
  },
  yaxis: {
    showgrid: true,
    gridcolor: '#d3d3d3',
    gridwidth: 1,
    zeroline: true,
    zerolinecolor: '#999',
    zerolinewidth: 2
  }
}
const mergedLayout = mergeDeep(defaultLayout, spec.layout || {})
```

### 3. `/src/components/PlotlyGraph.vue`

#### 수정된 로직
```javascript
// Before
if (props.height) {
  layout.height = props.height
}

// After
// Only apply props.height if layout.height is not already defined
if (props.height && !layout.height) {
  layout.height = props.height
}
```

**변경 이유**: `graph_spec.layout.height`가 이미 정의되어 있으면 그것을 우선 사용하도록 수정

## 🎯 적용된 기본 커스터마이징

### 모든 그래프 타입에 공통 적용

| 옵션 | 값 | 설명 |
|------|-----|------|
| `height` | 500 | 차트 높이 (픽셀) |
| `margin.l` | 80 | 왼쪽 마진 |
| `margin.r` | 80 | 오른쪽 마진 |
| `margin.t` | 100 | 상단 마진 |
| `margin.b` | 100/120 | 하단 마진 (line: 120) |
| `margin.pad` | 4 | 패딩 |
| `xaxis.tickangle` | -45 | X축 라벨 각도 (45도 기울임) |
| `xaxis.tickfont.size` | 10 | X축 라벨 폰트 크기 |
| `xaxis.showgrid` | true | X축 그리드 표시 |
| `xaxis.gridcolor` | #e5e5e5 | X축 그리드 색상 |
| `yaxis.showgrid` | true | Y축 그리드 표시 |
| `yaxis.gridcolor` | #d3d3d3 | Y축 그리드 색상 |
| `yaxis.zeroline` | true | Y축 0 기준선 표시 |
| `yaxis.zerolinecolor` | #999 | 0 기준선 색상 |

### Line Graph 추가 설정
- `yaxis.griddash`: 'dot' (점선 그리드)

## 🔧 백엔드에서 사용하는 방법

백엔드에서 `graph_spec`를 생성할 때 `layout` 객체에 원하는 커스터마이징 옵션을 추가하면 됩니다:

```python
graph_spec = {
    "schema_version": "1.0",
    "chart_type": "line_graph",
    "encodings": { ... },
    "layout": {
        "title": "CPK Trend",
        "height": 600,  # 기본값 500 대신 600 사용
        "xaxis": {
            "title": "Date",
            "tickangle": -90,  # 기본값 -45 대신 -90 사용
            "tickfont": { "size": 8 }  # 기본값 10 대신 8 사용
        },
        "yaxis": {
            "title": "CPK",
            "range": [0.8, 2.0]  # Y축 범위 명시
        },
        "shapes": [  # 목표값 기준선 추가
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

## ✨ 장점

1. **기본 설정 제공**: 백엔드에서 아무 설정도 하지 않아도 깔끔한 그래프 생성
2. **유연한 커스터마이징**: 백엔드에서 필요한 부분만 override 가능
3. **일관성**: 모든 엑셀 분석 그래프가 동일한 스타일 적용
4. **사용자 경험 개선**: 
   - X축 라벨이 길어도 -45도 각도로 가독성 확보
   - 그리드 라인으로 값 읽기 쉬움
   - 적절한 마진으로 라벨 잘림 방지

## 🧪 테스트 방법

1. 엑셀 파일 업로드
2. "바차트 그려줘", "선 그래프 그려줘", "박스플롯 그려줘" 등 요청
3. 생성된 그래프에서 확인할 사항:
   - 높이가 500px로 설정되었는지
   - X축 라벨이 45도 기울어졌는지
   - 그리드 라인이 표시되는지
   - Y축에 0 기준선이 있는지
   - 마진이 충분히 확보되어 라벨이 잘리지 않는지

## 📚 참고 문서

- `/docs/excel_analysis_response_formats.md` - 전체 API 응답 포맷 및 커스터마이징 옵션
- [Plotly.js Layout Reference](https://plotly.com/javascript/reference/layout/) - Plotly 공식 문서
