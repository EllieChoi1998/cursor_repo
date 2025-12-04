# PlotlyGraph X축 라벨 처리 가이드

## 📋 개요

엑셀 데이터 분석에서 생성되는 PlotlyGraph의 x축 라벨이 길거나 많을 때를 대비한 최적화 방안입니다.

## 🎯 문제 상황

### x축 라벨 관련 이슈

1. **라벨이 많을 때**
   - 100개 이상의 카테고리/데이터 포인트
   - 라벨이 서로 겹침
   - 읽기 어려움

2. **라벨이 길 때**
   - 긴 텍스트 라벨 (예: "2024-11-01-Device-A-Process-1")
   - 가로 방향으로 잘림
   - 세로로 회전해도 하단이 잘릴 수 있음

3. **트렌드 가시성**
   - 데이터가 많으면 트렌드 파악이 어려움
   - 전체 패턴을 한눈에 봐야 함

## ✅ 적용된 해결책

### 1. 하단 마진 증가

모든 그래프 타입에서 `bottom margin`을 **150px**로 증가:

```javascript
// App.vue
const defaultLayout = {
  height: 500,
  margin: { 
    l: 80,   // left
    r: 80,   // right
    t: 100,  // top
    b: 150,  // bottom - ⭐ 150px로 증가 (기존 100-120px)
    pad: 4 
  }
}
```

**효과:**
- ✅ x축 라벨이 길어도 잘리지 않음
- ✅ -90도 회전해도 충분한 공간 확보
- ✅ 여러 줄 라벨도 표시 가능

### 2. 라벨 각도 조절

기본적으로 `-45도` 각도 적용:

```javascript
xaxis: {
  tickangle: -45,  // 라벨을 45도 기울임
  tickfont: { size: 10, color: '#666' }
}
```

**장점:**
- 가로보다 더 많은 라벨을 표시 가능
- 읽기 쉬움
- 공간 효율적

### 3. 폰트 크기 축소

라벨 폰트를 `10px`로 설정:

```javascript
xaxis: {
  tickfont: { size: 10 }  // 작은 폰트로 더 많이 표시
}
```

### 4. 반응형 차트 너비

차트가 화면 너비에 자동으로 맞춰짐:

```javascript
// PlotlyGraph.vue
responsive: true  // 화면 너비에 맞춤
```

**효과:**
- ✅ 트렌드가 한눈에 보임
- ✅ 전체 데이터 패턴 파악 용이
- ✅ 여러 차트 비교 쉬움

## 📊 각도별 비교

### tickangle: 0 (가로)
```
장비1  장비2  장비3  장비4  장비5
      ↑ 겹쳐서 읽기 어려움
```
**단점:** 라벨이 많으면 겹침

### tickangle: -45 (기본값) ⭐
```
장비1
   장비2
      장비3
         장비4
            장비5
```
**장점:** 균형있는 가독성과 공간 효율

### tickangle: -90 (세로)
```
장  장  장  장  장
비  비  비  비  비
1   2   3   4   5
```
**장점:** 가장 많은 라벨 표시 가능
**단점:** 읽기 어려울 수 있음

## 🔧 커스터마이징 옵션

### 백엔드에서 각도 조절

LLM 또는 백엔드에서 `tickangle` 조절:

```python
graph_spec = {
    "layout": {
        "xaxis": {
            "tickangle": -90,  # 세로로 회전
        },
        "margin": {
            "b": 200  # 세로일 때 더 큰 마진 필요
        }
    }
}
```

### 라벨이 매우 긴 경우

```python
graph_spec = {
    "layout": {
        "xaxis": {
            "tickangle": -90,
            "tickfont": { "size": 8 },  # 더 작은 폰트
        },
        "margin": {
            "b": 250  # 라벨 길이에 맞게 조절
        }
    }
}
```

### 라벨 텍스트 줄이기

데이터 전처리 시 라벨 축약:

```python
# Before
labels = ["2024-11-01-Device-A-Process-1", ...]

# After
labels = ["24-11-01-A-P1", ...]  # 축약
```

## 📐 권장 설정

### 라벨 개수별 권장 설정

| 라벨 개수 | tickangle | 폰트 크기 | bottom margin | 권장 사항 |
|----------|-----------|----------|--------------|---------|
| < 10개 | 0° (가로) | 11-12px | 80-100px | 기본 설정 충분 |
| 10-30개 | -45° | 10px | 150px | ⭐ 기본값 (현재) |
| 30-50개 | -60° ~ -90° | 9-10px | 180-200px | 각도 증가 권장 |
| 50-100개 | -90° | 8-9px | 200-250px | 매우 작은 폰트 |
| > 100개 | N/A | N/A | N/A | 데이터 필터링/집계 필수 |

### 라벨 길이별 권장 설정

| 평균 글자 수 | tickangle | bottom margin | 권장 사항 |
|------------|-----------|--------------|---------|
| < 5자 | -45° | 150px | 기본 설정 |
| 5-10자 | -45° ~ -60° | 150-180px | 적절 |
| 10-20자 | -60° ~ -90° | 180-220px | 각도 크게 |
| > 20자 | -90° | 220-280px | 텍스트 축약 권장 |

## 🎨 실제 예시

### 예시 1: 장비명이 긴 경우

**데이터:**
```
["Equipment-A-Line1-Chamber1", "Equipment-B-Line2-Chamber3", ...]
```

**설정:**
```python
{
    "layout": {
        "xaxis": {
            "tickangle": -90,
            "tickfont": { "size": 9 }
        },
        "margin": { "b": 220 }
    }
}
```

**결과:**
- ✅ 모든 글자가 명확하게 표시됨
- ✅ 잘림 없음

### 예시 2: 날짜 데이터

**데이터:**
```
["2024-11-01", "2024-11-02", ..., "2024-12-31"]  // 60개
```

**설정:**
```python
{
    "layout": {
        "xaxis": {
            "tickangle": -45,
            "tickfont": { "size": 9 }
        },
        "margin": { "b": 150 }
    }
}
```

**결과:**
- ✅ 날짜가 명확하게 보임
- ✅ 트렌드 파악 용이

### 예시 3: 숫자/짧은 코드

**데이터:**
```
["A1", "A2", "A3", ..., "Z9"]  // 100개
```

**설정:**
```python
{
    "layout": {
        "xaxis": {
            "tickangle": -90,
            "tickfont": { "size": 8 }
        },
        "margin": { "b": 180 }
    }
}
```

**결과:**
- ✅ 100개 라벨도 표시 가능
- ✅ 세로로 읽기 가능

## 🚫 기술적 제약사항

### 불가능한 것들

1. **x축 라벨 영역만 스크롤**
   - Plotly는 SVG로 통합 렌더링
   - 특정 영역만 분리해서 스크롤 불가능
   - 차트 전체가 하나의 요소

2. **자동 라벨 줄바꿈**
   - Plotly는 자동 줄바꿈 미지원
   - 수동으로 `<br>` 태그 삽입 필요
   - 데이터 전처리에서 처리

3. **가변 높이 차트**
   - 라벨 길이에 따라 자동으로 margin 조절 불가
   - 고정값 또는 백엔드에서 계산 필요

## 💡 모범 사례

### 1. 데이터 전처리

```python
def format_label(label, max_length=15):
    """라벨을 적절히 축약"""
    if len(label) <= max_length:
        return label
    # 중간 생략
    return label[:max_length-3] + "..."

# 또는 줄바꿈 추가
def wrap_label(label, max_chars=10):
    """라벨에 줄바꿈 추가"""
    if len(label) <= max_chars:
        return label
    words = label.split('-')
    return '<br>'.join(words)
```

### 2. 동적 margin 계산

```python
def calculate_bottom_margin(labels, tickangle=-45):
    """라벨 길이에 따라 margin 계산"""
    max_label_length = max(len(str(label)) for label in labels)
    
    if tickangle == 0:  # 가로
        return 80 + (max_label_length * 5)
    elif tickangle >= -45:  # -45도
        return 120 + (max_label_length * 3)
    else:  # -90도
        return 150 + (max_label_length * 4)

# 사용
bottom_margin = calculate_bottom_margin(x_labels, -45)
graph_spec["layout"]["margin"]["b"] = bottom_margin
```

### 3. LLM 프롬프트에서 처리

```
If x-axis labels are long (>10 characters):
- Set tickangle to -90
- Increase margin.b to 220
- Reduce tickfont.size to 9

If x-axis has many categories (>50):
- Set tickangle to -90
- Set tickfont.size to 8
- Consider filtering data to top 30 categories
```

## 📈 성능 고려사항

### 많은 라벨 처리

**100개 이상의 라벨:**
- ✅ 기술적으로 가능
- ⚠️ 가독성 저하
- ⚠️ 렌더링 성능 영향
- 💡 권장: 필터링 또는 집계

**해결책:**
1. Top N 필터링
2. 그룹화/집계
3. 샘플링
4. 페이지네이션 (다중 차트)

## 🧪 테스트 시나리오

### 시나리오 1: 짧은 라벨 10개
- ✅ tickangle: -45°
- ✅ margin.b: 150px
- ✅ 모든 라벨 명확히 표시

### 시나리오 2: 긴 라벨 30개
- ✅ tickangle: -90°
- ✅ margin.b: 220px
- ✅ 라벨 전체 표시, 잘림 없음

### 시나리오 3: 매우 많은 라벨 100개
- ✅ tickangle: -90°
- ✅ tickfont.size: 8px
- ✅ margin.b: 200px
- ⚠️ 읽기 어려움 (필터링 권장)

## 🔗 관련 문서

- `/docs/excel_analysis_response_formats.md` - API 응답 포맷
- `/docs/plotly_customization_changes.md` - 커스터마이징 옵션
- `/docs/llm_prompts_for_plotly_spec_generation.md` - LLM 프롬프트

## 📞 FAQ

### Q: x축 라벨이 여전히 잘려요
**A:** `margin.b`를 더 크게 설정하세요 (200-250px)

### Q: 라벨이 너무 많아서 읽기 어려워요
**A:** 데이터를 필터링하거나 그룹화하세요. 30-50개가 적정선입니다.

### Q: 라벨을 가로로 표시하고 싶어요
**A:** `tickangle: 0`으로 설정하되, 라벨 개수가 적을 때만 권장합니다.

### Q: x축 영역만 스크롤 가능한가요?
**A:** Plotly 구조상 불가능합니다. 대신 margin을 크게 설정하여 모든 라벨이 보이도록 하세요.

---

**Last Updated:** 2025-12-04  
**Version:** 1.0
