# Data Analysis Chat Assistant

Vue.js 프론트엔드와 FastAPI 백엔드로 구성된 데이터 분석 채팅 어시스턴트입니다.

## 🚀 기능

- **PCM (Process Control Monitor)**: 트렌드 분석 및 Commonality 분석
- **CP (Critical Path)**: 성능 분석 및 모니터링
- **RAG (Retrieval-Augmented Generation)**: AI 기반 검색 및 요약
- **실시간 스트리밍**: Server-Sent Events를 통한 실시간 데이터 전송
- **인터랙티브 차트**: Plotly.js를 활용한 동적 데이터 시각화
- **PostgreSQL 데이터베이스**: 안정적인 데이터 저장 및 관리
- **유저 관리**: 사용자별 채팅방 및 세션 관리
- **데이터 보존**: 채팅방 삭제 시에도 연관 데이터 보존
- **세션 관리**: 유저별 세션 스토리지 및 만료 관리

## 📁 프로젝트 구조

```
cursor_repo/
├── app/                   # FastAPI 백엔드
│   ├── __init__.py
│   ├── main.py           # FastAPI 애플리케이션
│   ├── config.py         # 설정 관리
│   ├── database.py       # 데이터베이스 연결
│   ├── database_init.py  # 데이터베이스 초기화
│   ├── models/           # Pydantic 모델
│   ├── repositories/     # 데이터 접근 계층
│   │   ├── chat_storage.py      # 채팅 데이터 저장소
│   │   ├── user_storage.py      # 유저 세션 저장소
│   │   ├── user_repository.py   # 유저 데이터 저장소
│   │   └── data_preservation.py # 데이터 보존 유틸리티
│   ├── routers/          # API 라우터
│   ├── services/         # 비즈니스 로직
│   └── utils/            # 유틸리티 함수
├── src/                  # Vue.js 프론트엔드
│   ├── App.vue           # 메인 Vue 컴포넌트
│   ├── components/
│   │   ├── PCMTrendChart.vue    # PCM 트렌드 차트
│   │   └── CommonalityTable.vue # Commonality 테이블
│   ├── services/
│   │   └── api.js        # API 서비스
│   └── config/
│       └── dataTypes.js  # 데이터 타입 설정
├── requirements.txt      # Python 의존성
├── tables.sql           # 데이터베이스 스키마
├── init_db.py           # 데이터베이스 초기화 스크립트
├── .env.example         # 환경 변수 예제
└── README.md
```

## 🛠️ 설치 및 실행

### 데이터베이스 설정

이 프로젝트는 PostgreSQL을 사용합니다.

1. **PostgreSQL 설치 및 설정**
```bash
# PostgreSQL 설치 (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# PostgreSQL 설치 (macOS)
brew install postgresql

# PostgreSQL 설치 (Windows)
# https://www.postgresql.org/download/windows/ 에서 다운로드
```

2. **데이터베이스 생성**
```bash
# PostgreSQL에 접속
sudo -u postgres psql

# 데이터베이스 생성
CREATE DATABASE chat_analysis_db;

# 사용자 생성 (선택사항)
CREATE USER chat_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chat_analysis_db TO chat_user;
```

3. **환경 변수 설정**
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 데이터베이스 정보 설정
DB_HOST=localhost
DB_DATABASE=chat_analysis_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

4. **데이터베이스 초기화**
```bash
python init_db.py
```

### 백엔드 실행

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **백엔드 서버 실행**
```bash
python app.py
```

백엔드는 `http://localhost:8000`에서 실행됩니다.

### 백엔드 IP 설정

프론트엔드에서 백엔드 서버 IP를 변경하려면 `.env` 파일을 수정하세요:

```bash
# .env 파일 수정
VUE_APP_API_BASE_URL=http://your-backend-ip:8000
```

자세한 설정 방법은 [BACKEND_IP_CONFIGURATION.md](./BACKEND_IP_CONFIGURATION.md) 문서를 참조하세요.

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