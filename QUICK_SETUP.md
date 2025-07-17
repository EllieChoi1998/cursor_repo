# 🚀 빠른 백엔드 IP 설정 가이드

## 30초 만에 백엔드 IP 변경하기

### 1️⃣ .env 파일 열기
```bash
# 프로젝트 루트에서
code .env
# 또는
nano .env
```

### 2️⃣ IP 주소 변경
```bash
# 기존
VUE_APP_API_BASE_URL=http://localhost:8000

# 변경 (예시)
VUE_APP_API_BASE_URL=http://192.168.1.100:8000
```

### 3️⃣ 개발 서버 재시작
```bash
# Ctrl+C로 종료 후
npm run serve
```

### 4️⃣ 확인
브라우저 콘솔에서 다음 메시지 확인:
```
🔗 API Base URL: http://192.168.1.100:8000
```

## 📋 자주 사용하는 설정

| 환경 | 설정 값 |
|------|---------|
| 로컬 개발 | `http://localhost:8000` |
| 같은 네트워크 PC | `http://192.168.1.xxx:8000` |
| 외부 서버 | `http://203.xxx.xxx.xxx:8000` |
| 도메인 사용 | `http://api.yoursite.com` |
| HTTPS | `https://api.yoursite.com` |

## ⚠️ 문제 해결

### 연결 안됨?
1. 백엔드 서버 실행 중인지 확인
2. IP 주소 정확한지 확인
3. 포트 번호 확인 (기본: 8000)
4. 방화벽 설정 확인

### 설정 적용 안됨?
1. 개발 서버 완전 재시작
2. 브라우저 캐시 삭제
3. `.env` 파일 위치 확인 (프로젝트 루트)

---
💡 **더 자세한 설정**: [BACKEND_IP_CONFIGURATION.md](./BACKEND_IP_CONFIGURATION.md) 참조