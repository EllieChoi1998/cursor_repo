# Data Analysis Chat Assistant

Vue.js 프론트엔드와 FastAPI 백엔드로 구성된 데이터 분석 채팅 어시스턴트입니다.

## 🚀 기능

- **PCM (Process Control Monitor)**: 트렌드 분석 및 Commonality 분석
- **CP (Critical Path)**: 성능 분석 및 모니터링
- **RAG (Retrieval-Augmented Generation)**: AI 기반 검색 및 요약
- **실시간 스트리밍**: Server-Sent Events를 통한 실시간 데이터 전송
- **인터랙티브 차트**: Plotly.js를 활용한 동적 데이터 시각화

## 📁 프로젝트 구조

```
cursor_repo/
├── app.py                 # FastAPI 백엔드
├── requirements.txt       # Python 의존성
├── test_backend.py       # 백엔드 테스트 스크립트
├── src/
│   ├── App.vue           # 메인 Vue 컴포넌트
│   ├── components/
│   │   ├── PCMTrendChart.vue    # PCM 트렌드 차트
│   │   └── CommonalityTable.vue # Commonality 테이블
│   ├── services/
│   │   └── api.js        # API 서비스
│   └── config/
│       └── dataTypes.js  # 데이터 타입 설정
└── README.md
```

## 🛠️ 설치 및 실행

### 백엔드 실행

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **백엔드 서버 실행**
```bash
python app.py
```

백엔드는 `http://localhost:8005`에서 실행됩니다.

### 프론트엔드 실행

1. **의존성 설치**
```bash
npm install
```

2. **개발 서버 실행**
```bash
npm run serve
```

프론트엔드는 `http://localhost:8080`에서 실행됩니다.

## 🧪 테스트

### 백엔드 테스트
```bash
python test_backend.py
```

### 프론트엔드 테스트
```bash
npm run test
```

## 📊 사용 방법

1. **데이터 타입 선택**: 드롭다운에서 PCM/CP/RAG 중 선택
2. **메시지 입력**: 원하는 분석 요청 입력
3. **전송**: Enter 키 또는 전송 버튼 클릭
4. **결과 확인**: 실시간으로 스트리밍되는 분석 결과 확인

### 지원되는 명령어

#### PCM (Process Control Monitor)
- `trend`, `트렌드`, `차트`, `그래프`, `분석`
- `commonality`, `커먼`, `공통`, `분석`

#### CP (Critical Path)
- `analysis`, `분석`, `성능`, `모니터링`
- `performance`, `성능`, `측정`, `평가`

#### RAG (Retrieval-Augmented Generation)
- `search`, `검색`, `찾기`, `조회`
- `summary`, `요약`, `정리`, `개요`

## 🔧 API 엔드포인트

### POST /api/chat
스트리밍 채팅 API

**요청:**
```json
{
  "choice": "pcm",
  "message": "trend",
  "chatroom_id": 1
}
```

**응답 (스트리밍):**
```
data: {"status": "processing"}

data: {
  "chat_id": "chat_20240101_120000_1234",
  "response": {
    "result": "lot_start",
    "real_data": [...],
    "sql": "SELECT * FROM pcm_data...",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

### GET /api/health
헬스 체크

### GET /
API 정보

## 🎨 주요 기능

### 실시간 스트리밍
- Server-Sent Events를 통한 실시간 데이터 전송
- 처리 중 상태 표시
- 에러 처리 및 복구

### 데이터 시각화
- **PCM Trend Chart**: Box plot과 제어선을 포함한 트렌드 분석
- **Commonality Table**: 검색, 필터링, 정렬 기능이 있는 데이터 테이블
- **Plotly.js**: 인터랙티브 차트 및 그래프

### 에러 처리
- 백엔드에서 유효성 검사
- 프론트엔드에서 에러 메시지 표시
- 사용자 친화적인 에러 안내

## 🔒 보안

- CORS 설정으로 허용된 origin만 접근 가능
- 입력 데이터 검증
- 에러 메시지에서 민감한 정보 제외

## 📈 확장성

### 새로운 데이터 타입 추가
1. `src/config/dataTypes.js`에 데이터 타입 정의
2. 새로운 차트 컴포넌트 생성
3. 백엔드 `app.py`에 처리 로직 추가

### 새로운 차트 타입 추가
1. Plotly.js를 사용한 차트 컴포넌트 생성
2. `DataTypes.js`에 차트 타입 등록
3. API 응답 처리 로직 추가

## 🐛 문제 해결

### 백엔드 연결 오류
- 백엔드 서버가 실행 중인지 확인
- 포트 8005가 사용 가능한지 확인
- CORS 설정 확인

### 프론트엔드 빌드 오류
- Node.js 버전 확인 (v14 이상 권장)
- 의존성 재설치: `rm -rf node_modules && npm install`

### 스트리밍 데이터 오류
- 네트워크 연결 상태 확인
- 브라우저 개발자 도구에서 네트워크 탭 확인

## 📝 라이선스

MIT License

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 