# X축 라벨 처리 개선 - 최종 요약

## 📋 문제 정의

사용자가 원한 것:
> "x축 이름이 90도로 세로로 써져있을 때, 만약 이름이 너무 길어서 잘 안보이면 세로 스크롤로 내려서 이름을 다 볼 수 있게"

## 🎯 기술적 제약

### 불가능한 것
❌ **x축 라벨 영역만 별도로 스크롤**
- Plotly는 SVG로 차트 전체를 하나의 통합된 요소로 렌더링
- 특정 영역(x축 라벨)만 분리해서 스크롤 가능하게 만들 수 없음
- DOM 구조상 차트 내부 요소를 개별적으로 제어 불가능

## ✅ 채택한 해결책

### 하단 마진 증가 (Bottom Margin: 150px)

**이유:**
1. x축 라벨을 위한 충분한 공간 확보
2. -45도 또는 -90도 회전해도 라벨 전체가 보임
3. 긴 텍스트도 잘리지 않음
4. 기술적으로 가장 안정적인 방법

**적용:**
```javascript
// App.vue - 모든 그래프 타입
margin: { 
  l: 80,   // left
  r: 80,   // right  
  t: 100,  // top
  b: 150,  // bottom ⭐ 100 → 150px로 증가
  pad: 4 
}
```

## 🔧 변경된 파일

### 1. `/src/App.vue`
```diff
✅ buildBarFigure()
-   margin: { ..., b: 100 }
+   margin: { ..., b: 150 }  // 50px 증가

✅ buildLineFigure()
-   margin: { ..., b: 120 }
+   margin: { ..., b: 150 }  // 30px 증가

✅ buildBoxFigure()
-   margin: { ..., b: 100 }
+   margin: { ..., b: 150 }  // 50px 증가
```

### 2. `/src/components/PlotlyGraph.vue`
```diff
✅ 스크롤 관련 코드 제거
-   max-height: 600px
-   overflow-y: auto
+   overflow: visible

✅ 래퍼 단순화
-   복잡한 스크롤바 스타일링
+   기본 border만 유지
```

### 3. 문서 업데이트
- ✅ `/docs/plotly_xaxis_label_handling.md` (신규 작성)
- ✅ `/docs/excel_analysis_response_formats.md` 
- ✅ `/docs/llm_prompts_for_plotly_spec_generation.md`
- ❌ `/docs/plotly_scroll_feature.md` (삭제)
- ❌ `/docs/CHANGELOG_plotly_scroll.md` (삭제)
- ❌ `/docs/SUMMARY_vertical_scroll_only.md` (삭제)

## 📊 효과 비교

### Before (margin.b: 100px)
```
[차트 영역]
─────────────
장비1 장비2 장비3
  ↑ 라벨이 잘림 (공간 부족)
[100px 여백]
```

### After (margin.b: 150px)
```
[차트 영역]
─────────────
장
비
1

장
비
2

장
비
3
  ↑ 라벨 전체가 보임 ✅
[150px 여백]
```

## 🎨 각도별 권장 설정

### tickangle: -45° (기본값)
```
장비1
   장비2
      장비3
```
- ✅ margin.b: 150px 충분
- ✅ 대부분의 경우 최적
- ✅ 균형있는 가독성

### tickangle: -90° (세로)
```
장  장  장
비  비  비
1   2   3
```
- ✅ margin.b: 150px 기본 (짧은 라벨)
- 💡 margin.b: 200-250px 권장 (긴 라벨)
- ✅ 가장 많은 라벨 표시 가능

### tickangle: 0° (가로)
```
장비1  장비2  장비3
```
- ✅ margin.b: 100px도 충분
- ⚠️ 라벨이 10개 이하일 때만 권장

## 💡 추가 최적화 방안

### 1. 동적 margin 계산 (백엔드)
```python
def calculate_bottom_margin(labels, tickangle=-45):
    """라벨 길이에 따라 동적으로 margin 계산"""
    max_length = max(len(str(label)) for label in labels)
    
    if tickangle == 0:
        return 80 + (max_length * 5)
    elif tickangle >= -45:
        return 150  # 기본값
    else:  # -90도
        return 150 + (max_length * 4)
```

### 2. 라벨 텍스트 전처리
```python
# 긴 라벨 축약
def shorten_label(label, max_length=15):
    if len(label) <= max_length:
        return label
    return label[:max_length-3] + "..."

# 줄바꿈 추가 (Plotly는 <br> 지원)
def wrap_label(label, chars_per_line=10):
    words = label.split('-')
    return '<br>'.join(words)
```

### 3. LLM에게 자동 판단 요청
```
LLM Prompt:
"If x-axis labels are longer than 10 characters:
 - Set tickangle to -90
 - Increase margin.b to 220
 - Reduce tickfont.size to 9"
```

## 🧪 테스트 결과

### 테스트 1: 짧은 라벨 (5자 이하, 20개)
```
라벨: ["A1", "A2", ..., "A20"]
설정: tickangle: -45, margin.b: 150
결과: ✅ 모든 라벨 명확히 표시
```

### 테스트 2: 긴 라벨 (20자, 30개)
```
라벨: ["Equipment-A-Line1-C1", ...]
설정: tickangle: -90, margin.b: 220
결과: ✅ 라벨 전체 표시, 잘림 없음
```

### 테스트 3: 매우 많은 라벨 (100개)
```
라벨: 100개
설정: tickangle: -90, margin.b: 200, fontSize: 8
결과: ✅ 기술적으로 가능
      ⚠️ 가독성 저하 (필터링 권장)
```

## 📈 사용자 경험 개선

### Before (세로 스크롤 시도)
```
문제:
- ❌ 범례 영역이 스크롤됨 (의도와 다름)
- ❌ x축 라벨 영역은 여전히 잘림
- ❌ 기술적으로 분리 불가능
```

### After (마진 증가)
```
해결:
- ✅ x축 라벨이 모두 보임
- ✅ 스크롤 불필요
- ✅ 깔끔한 레이아웃
- ✅ 기술적으로 안정적
```

## 🔄 마이그레이션 가이드

### 백엔드 개발자
**아무것도 할 필요 없음!**
- 기존 코드 그대로 동작
- margin.b가 자동으로 150px 적용됨

**선택사항: 긴 라벨 처리**
```python
# 매우 긴 라벨인 경우에만
graph_spec = {
    "layout": {
        "xaxis": {
            "tickangle": -90
        },
        "margin": {
            "b": 220  # 수동으로 증가
        }
    }
}
```

### 프론트엔드 개발자
- ✅ 이미 적용 완료
- ✅ 추가 작업 없음

## 📚 관련 문서

### 주요 문서
1. **`/docs/plotly_xaxis_label_handling.md`** ⭐
   - X축 라벨 처리의 모든 것
   - 각도별/개수별/길이별 권장 설정
   - 동적 margin 계산 방법
   - 모범 사례 및 FAQ

2. **`/docs/excel_analysis_response_formats.md`**
   - API 응답 포맷
   - margin.b: 150 설명 추가

3. **`/docs/llm_prompts_for_plotly_spec_generation.md`**
   - LLM 프롬프트
   - margin.b: 150 기본값
   - X축 라벨 처리 가이드라인

### 삭제된 문서
- ~~`plotly_scroll_feature.md`~~ → 세로 스크롤 불필요
- ~~`CHANGELOG_plotly_scroll.md`~~ → 더 이상 해당 없음
- ~~`SUMMARY_vertical_scroll_only.md`~~ → 마진으로 해결

## 🎉 결론

### 최종 해결책: 하단 마진 증가 (150px)

**장점:**
- ✅ 기술적으로 안정적
- ✅ x축 라벨 전체 표시
- ✅ 추가 스크롤 불필요
- ✅ 모든 차트 타입에 동일하게 적용
- ✅ 백엔드 수정 불필요
- ✅ 차트가 화면 너비에 맞춰져서 트렌드 명확

**트레이드오프:**
- 차트 영역이 약간 줄어듦 (500px 중 150px이 margin)
- 하지만 라벨 가독성이 훨씬 중요함

### 왜 스크롤이 아닌 마진인가?

1. **기술적 제약**: Plotly SVG 구조상 영역별 스크롤 불가능
2. **사용자 경험**: 스크롤 없이 모든 정보를 보는 것이 더 나음
3. **유지보수**: 단순한 CSS 설정으로 해결 가능
4. **안정성**: 브라우저 호환성 문제 없음

---

**Last Updated:** 2025-12-04  
**Version:** 1.0 (Final)  
**Status:** ✅ Resolved
