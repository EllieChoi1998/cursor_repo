// API 설정 중앙 관리
export const API_CONFIG = {
  // 백엔드 기본 URL (환경변수에서 읽어옴)
  BASE_URL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000',
  
  // API 엔드포인트들
  ENDPOINTS: {
    CHATROOMS: '/chatrooms',
    CHATROOM_HISTORY: '/chatrooms/:id/history',
    CHAT: '/chat',
    HEALTH: '/api/health'
  },
  
  // 요청 설정
  REQUEST_CONFIG: {
    timeout: 30000, // 30초
    headers: {
      'Content-Type': 'application/json'
    }
  },
  
  // 스트리밍 설정
  STREAMING_CONFIG: {
    headers: {
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Content-Type': 'text/event-stream'
    }
  }
}

// 전체 URL 생성 함수
export const getApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}

// 디버깅 정보 출력 (개발 환경에서만)
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 API Configuration:')
  console.log('  - Base URL:', API_CONFIG.BASE_URL)
  console.log('  - Environment:', process.env.NODE_ENV)
  console.log('  - Available Endpoints:', Object.keys(API_CONFIG.ENDPOINTS))
}

export default API_CONFIG