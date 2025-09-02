/**
 * 인증 관련 유틸리티 함수들
 */

const TOKEN_KEY = 'jwt_token'
const USER_KEY = 'user_info'

/**
 * JWT 토큰을 localStorage에서 가져오기
 * @returns {string|null} JWT 토큰 또는 null
 */
export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch (error) {
    console.error('Error getting token from localStorage:', error)
    return null
  }
}

/**
 * JWT 토큰을 localStorage에 저장
 * @param {string} token - JWT 토큰
 */
export const setToken = (token) => {
  try {
    localStorage.setItem(TOKEN_KEY, token)
    console.log('✅ Token saved to localStorage')
  } catch (error) {
    console.error('Error saving token to localStorage:', error)
  }
}

/**
 * JWT 토큰을 localStorage에서 삭제
 */
export const removeToken = () => {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    console.log('✅ Token removed from localStorage')
  } catch (error) {
    console.error('Error removing token from localStorage:', error)
  }
}

/**
 * JWT 토큰이 유효한지 확인
 * @returns {boolean} 토큰 유효성
 */
export const isTokenValid = () => {
  const token = getToken()
  if (!token) {
    return false
  }

  try {
    // JWT 토큰 디코딩 (서명 검증 없이)
    const payload = JSON.parse(atob(token.split('.')[1]))
    const currentTime = Math.floor(Date.now() / 1000)
    
    // 만료 시간 확인
    if (payload.exp && payload.exp < currentTime) {
      console.log('❌ Token has expired')
      return false
    }
    
    return true
  } catch (error) {
    console.error('Error validating token:', error)
    return false
  }
}

/**
 * JWT 토큰에서 사용자 정보 추출
 * @returns {object|null} 사용자 정보 또는 null
 */
export const getUserFromToken = () => {
  const token = getToken()
  if (!token) {
    return null
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      userId: payload.userId,
      loginTime: payload.loginTime,
      iat: payload.iat,
      exp: payload.exp
    }
  } catch (error) {
    console.error('Error extracting user from token:', error)
    return null
  }
}

/**
 * 사용자 정보를 localStorage에 저장
 * @param {object} userInfo - 사용자 정보
 */
export const setUserInfo = (userInfo) => {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    console.log('✅ User info saved to localStorage')
  } catch (error) {
    console.error('Error saving user info to localStorage:', error)
  }
}

/**
 * localStorage에서 사용자 정보 가져오기
 * @returns {object|null} 사용자 정보 또는 null
 */
export const getUserInfo = () => {
  try {
    const userInfo = localStorage.getItem(USER_KEY)
    return userInfo ? JSON.parse(userInfo) : null
  } catch (error) {
    console.error('Error getting user info from localStorage:', error)
    return null
  }
}

/**
 * 인증 상태 확인
 * @returns {boolean} 인증 여부
 */
export const isAuthenticated = () => {
  return isTokenValid() && getUserFromToken() !== null
}

/**
 * 로그아웃 처리
 */
export const logout = () => {
  removeToken()
  // 페이지 새로고침하여 상태 초기화
  window.location.reload()
}

/**
 * API 요청을 위한 Authorization 헤더 생성
 * @returns {object} Authorization 헤더가 포함된 객체
 */
export const getAuthHeaders = () => {
  const token = getToken()
  if (!token) {
    return {}
  }
  
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

/**
 * URL에서 토큰 파라미터 추출 (SSO 콜백용)
 * @returns {string|null} 토큰 또는 null
 */
export const getTokenFromUrl = () => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('token')
}

/**
 * SSO 로그인 후 토큰 처리
 * @param {string} token - SSO에서 받은 토큰
 */
export const handleSSOLogin = (token) => {
  if (token) {
    setToken(token)
    const userInfo = getUserFromToken()
    if (userInfo) {
      setUserInfo(userInfo)
      console.log('✅ SSO login successful:', userInfo.userId)
    }
    
    // URL에서 토큰 파라미터 제거
    const url = new URL(window.location)
    url.searchParams.delete('token')
    window.history.replaceState({}, document.title, url.pathname)
  }
}
