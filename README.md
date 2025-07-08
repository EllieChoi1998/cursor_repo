# PCM Chat Assistant

PCM (Process Control Monitor) 데이터 분석을 위한 채팅 인터페이스 애플리케이션입니다.

## 기능

- 💬 **채팅 인터페이스**: 자연어로 PCM 데이터 분석 요청
- 📊 **트렌드 차트**: Box plot과 제어선을 포함한 PCM 트렌드 분석
- 📋 **Commonality 테이블**: 12개 컬럼의 상세 데이터를 표 형식으로 표시
- 🔄 **실시간 데이터**: API를 통한 실시간 데이터 로드
- 📱 **반응형 디자인**: 모바일과 데스크톱에서 최적화된 UI

## 설치 및 실행

### 1. 의존성 설치
```bash
npm install
```

### 2. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# API 설정
VUE_APP_API_BASE_URL=http://localhost:3000/api

# 개발 환경 설정
NODE_ENV=development
```

### 3. 개발 서버 실행
```bash
npm run dev
```

## API 설정

### API 엔드포인트

애플리케이션은 다음 API 엔드포인트를 사용합니다:

- `GET /api/pcm-data` - PCM 데이터 조회
- `POST /api/pcm-data/refresh` - 데이터 새로고침
- `GET /api/pcm-data?startDate=X&endDate=Y` - 기간별 데이터 조회
- `GET /api/pcm-data/device/{deviceType}` - 특정 디바이스 데이터 조회

### 데이터 형식

API는 다음 형식의 데이터를 반환해야 합니다:

```json
[
  [1, 10, 20, 15, 16, 17, "A", 30, 15, 1, 25, 6],
  [2, 11, 21, 15, 16, 17, "A", 30, 15, 1, 25, 6],
  ...
]
```

각 배열 요소는 다음 순서로 구성됩니다:
- `[0]` DATE_WAFER_ID
- `[1]` MIN
- `[2]` MAX
- `[3]` Q1
- `[4]` Q2
- `[5]` Q3
- `[6]` DEVICE
- `[7]` USL
- `[8]` TGT
- `[9]` LSL
- `[10]` UCL
- `[11]` LCL

## 사용법

### 채팅 명령어

- **"load data"** - API에서 데이터 로드
- **"refresh"** - 데이터 새로고침
- **"trend"** - PCM 트렌드 차트 표시
- **"commonality"** - Commonality 분석 테이블 표시
- **"help"** - 사용 가능한 명령어 목록
- **"device"** - 디바이스 정보 조회
- **"data"** 또는 **"summary"** - 데이터 요약 정보

### Commonality 테이블 기능

Commonality 테이블은 다음과 같은 기능을 제공합니다:

- **12개 컬럼**: Date Wafer ID, Min, Max, Q1, Q2, Q3, Device, USL, TGT, LSL, UCL, LCL
- **검색 기능**: 모든 컬럼에서 텍스트 검색
- **디바이스 필터**: 특정 디바이스(A, B, C)로 필터링
- **정렬 기능**: 컬럼 헤더 클릭으로 오름차순/내림차순 정렬
- **페이지네이션**: 대용량 데이터를 페이지별로 표시
- **반응형 디자인**: 모바일에서도 최적화된 표시

### 예시 대화

```
사용자: load data
봇: ✅ PCM 데이터를 성공적으로 로드했습니다!

사용자: commonality
봇: 📋 Here's the Commonality Analysis Table! This table shows detailed PCM data with 12 columns including statistical values and control limits. You can search, filter by device, and sort by any column.

사용자: trend
봇: Here's the PCM trend analysis chart! The chart shows box plots for different device types with control lines (USL, LSL, UCL, LCL). You can see the data distribution and trends over time.

사용자: device
봇: The data contains 3 device types: A, B, C. Each device type has its own trend line in the chart.
```

## 기술 스택

- **Vue.js 3** - 프론트엔드 프레임워크
- **Plotly.js** - 데이터 시각화
- **Fetch API** - HTTP 요청
- **CSS3** - 스타일링

## 프로젝트 구조

```
src/
├── components/
│   ├── PCMTrendChart.vue      # PCM 트렌드 차트 컴포넌트
│   └── CommonalityTable.vue   # Commonality 분석 테이블 컴포넌트
├── services/
│   └── api.js                # API 서비스
├── App.vue                   # 메인 애플리케이션 컴포넌트
└── main.js                   # 애플리케이션 진입점
```

## 개발

### 빌드
```bash
npm run build
```

### 린트
```bash
npm run lint
```

### Mock 서버 실행
```bash
npm run mock-server
```

## 라이선스

MIT License 