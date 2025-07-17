# 백엔드 IP 설정 가이드

## 📋 개요
이 문서는 프론트엔드에서 백엔드 서버의 IP 주소를 쉽게 변경하는 방법을 설명합니다.

## 🎯 방법 1: 환경변수 파일 사용 (권장)

### 1-1. .env 파일 수정
프로젝트 루트에 있는 `.env` 파일을 수정하세요:

```bash
# .env 파일
VUE_APP_API_BASE_URL=http://your-backend-ip:8000
```

### 1-2. 설정 예시
```bash
# 로컬 개발
VUE_APP_API_BASE_URL=http://localhost:8000

# 같은 네트워크의 다른 PC
VUE_APP_API_BASE_URL=http://192.168.1.100:8000

# 외부 서버
VUE_APP_API_BASE_URL=http://203.123.45.67:8000

# 도메인 사용
VUE_APP_API_BASE_URL=http://api.yourcompany.com

# HTTPS 사용
VUE_APP_API_BASE_URL=https://api.yourcompany.com
```

### 1-3. 적용 방법
1. `.env` 파일을 수정
2. 개발 서버 재시작 (`npm run serve`)
3. 브라우저 새로고침

## 🔧 방법 2: 설정 파일 직접 수정

### 2-1. API 설정 파일 수정
`src/config/api.js` 파일에서 직접 수정:

```javascript
export const API_CONFIG = {
  // 이 부분을 수정
  BASE_URL: 'http://your-backend-ip:8000',
  // ...
}
```

### 2-2. API 서비스 파일 수정
`src/services/api.js` 파일에서 직접 수정:

```javascript
// 이 부분을 수정
const API_BASE_URL = 'http://your-backend-ip:8000'
```

## 📂 파일 위치 요약

### 환경변수 관련 파일
```
프로젝트루트/
├── .env                    # 실제 설정 파일 (수정하세요)
├── .env.example           # 예제 템플릿
```

### 코드 파일
```
src/
├── config/
│   └── api.js            # API 설정 중앙 관리
└── services/
    └── api.js            # API 호출 함수들
```

## 🚀 빠른 설정 방법

### 단계별 설정
1. **`.env` 파일 열기**
   ```bash
   # 프로젝트 루트에서
   code .env  # VSCode 사용시
   # 또는
   nano .env  # 터미널에서
   ```

2. **IP 주소 변경**
   ```bash
   # 기존
   VUE_APP_API_BASE_URL=http://localhost:8000
   
   # 변경 후 (예시)
   VUE_APP_API_BASE_URL=http://192.168.1.100:8000
   ```

3. **개발 서버 재시작**
   ```bash
   # 기존 서버 종료 (Ctrl+C)
   # 다시 시작
   npm run serve
   ```

4. **확인**
   - 브라우저 개발자 도구 → Console 탭에서 확인
   - "🔗 API Base URL: http://..." 메시지 확인

## ⚙️ 환경별 설정 예시

### 개발 환경
```bash
# .env.development
VUE_APP_API_BASE_URL=http://localhost:8000
NODE_ENV=development
```

### 스테이징 환경
```bash
# .env.staging
VUE_APP_API_BASE_URL=http://staging-server:8000
NODE_ENV=staging
```

### 운영 환경
```bash
# .env.production
VUE_APP_API_BASE_URL=https://api.production.com
NODE_ENV=production
```

## 🔍 디버깅 및 확인 방법

### 1. 브라우저 콘솔 확인
개발 환경에서는 콘솔에 다음과 같은 메시지가 표시됩니다:
```
🔗 API Base URL: http://your-backend-ip:8000
🔧 API Configuration:
  - Base URL: http://your-backend-ip:8000
  - Environment: development
  - Available Endpoints: ['CHATROOMS', 'CHAT', 'HEALTH']
```

### 2. 네트워크 탭 확인
1. 브라우저 개발자 도구 → Network 탭
2. 채팅 요청 시 올바른 IP로 요청이 가는지 확인
3. 요청 URL이 `http://your-backend-ip:8000/chat` 형태인지 확인

### 3. API 연결 테스트
```bash
# 백엔드 헬스 체크
curl http://your-backend-ip:8000/

# 채팅방 목록 조회
curl http://your-backend-ip:8000/chatrooms
```

## ⚠️ 주의사항

### 1. CORS 설정
백엔드에서 새로운 IP나 도메인을 허용하도록 CORS 설정이 필요할 수 있습니다:

```python
# app.py에서
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://localhost:3000",
        "http://your-frontend-ip:8080"  # 추가
    ],
    # ...
)
```

### 2. 포트 번호 확인
- 백엔드 서버가 실제로 해당 포트에서 실행 중인지 확인
- 방화벽에서 포트가 열려있는지 확인

### 3. HTTPS vs HTTP
- 운영 환경에서는 HTTPS 사용 권장
- Mixed Content 오류 방지를 위해 프론트엔드와 백엔드 모두 같은 프로토콜 사용

## 🆘 문제 해결

### 문제: "Failed to fetch" 오류
**해결방법:**
1. 백엔드 서버가 실행 중인지 확인
2. IP 주소와 포트 번호가 정확한지 확인
3. 방화벽 설정 확인
4. CORS 설정 확인

### 문제: 환경변수가 적용되지 않음
**해결방법:**
1. 개발 서버 완전 재시작
2. `.env` 파일 이름과 위치 확인 (프로젝트 루트)
3. 변수명이 `VUE_APP_` 접두사로 시작하는지 확인

### 문제: 일부만 연결됨
**해결방법:**
1. 모든 API 호출이 같은 BASE_URL을 사용하는지 확인
2. 하드코딩된 URL이 있는지 검색: `grep -r "localhost:8000" src/`

## 📝 체크리스트

설정 완료 후 다음을 확인하세요:

- [ ] `.env` 파일에 올바른 IP 설정
- [ ] 개발 서버 재시작 완료
- [ ] 브라우저 콘솔에서 올바른 API URL 확인
- [ ] 채팅방 목록 로드 정상 작동
- [ ] 채팅 메시지 전송 정상 작동
- [ ] 네트워크 탭에서 올바른 URL로 요청 확인

---

> 💡 **팁**: 설정 변경 후 항상 브라우저 캐시를 지우고 개발 서버를 재시작하는 것이 좋습니다!