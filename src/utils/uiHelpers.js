import { nextTick } from 'vue'

/**
 * Textarea 높이를 자동으로 조정하는 함수
 * @param {HTMLTextAreaElement} textarea - 높이를 조정할 textarea 요소
 */
export const adjustTextareaHeight = (textarea) => {
  if (textarea) {
    // 높이를 최소값으로 리셋
    textarea.style.height = '80px'
    
    // 스크롤 높이를 계산하여 최대 10줄 정도(약 240px)로 제한
    const minHeight = 80
    const maxHeight = 240
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight))
    textarea.style.height = newHeight + 'px'
    
    console.log('🔍 Textarea height adjusted:', newHeight + 'px', 'scrollHeight:', textarea.scrollHeight)
  }
}

/**
 * 메시지 컨테이너를 맨 아래로 스크롤하는 함수
 * @param {HTMLElement} messagesContainer - 스크롤할 메시지 컨테이너
 */
export const scrollToBottom = async (messagesContainer) => {
  await nextTick()
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight
  }
}

/**
 * 리사이즈 시작 함수
 * @param {MouseEvent} event - 마우스 이벤트
 * @param {Object} resizeState - 리사이즈 상태 객체
 * @param {Object} refs - DOM 참조 객체
 * @returns {Function} cleanup 함수
 */
export const startResize = (event, resizeState, refs) => {
  resizeState.isResizing = true
  resizeState.currentResizeBar = event.target
  resizeState.startX = event.clientX
  
  // 현재 너비들 저장
  resizeState.startWidths = {
    sidebar: refs.sidebar?.offsetWidth || 280,
    chatSection: refs.chatSection?.offsetWidth || 400,
    resultsSidebar: refs.resultsSidebar?.offsetWidth || 500
  }
  
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  
  const handleResizeMove = (e) => handleResize(e, resizeState, refs)
  const handleResizeEnd = () => stopResize(resizeState, handleResizeMove, handleResizeEnd)
  
  document.addEventListener('mousemove', handleResizeMove)
  document.addEventListener('mouseup', handleResizeEnd)
  event.preventDefault()
  
  return () => {
    document.removeEventListener('mousemove', handleResizeMove)
    document.removeEventListener('mouseup', handleResizeEnd)
  }
}

/**
 * 리사이즈 처리 함수
 * @param {MouseEvent} event - 마우스 이벤트
 * @param {Object} resizeState - 리사이즈 상태 객체
 * @param {Object} refs - DOM 참조 객체
 */
export const handleResize = (event, resizeState, refs) => {
  if (!resizeState.isResizing || !resizeState.currentResizeBar) return
  
  const deltaX = event.clientX - resizeState.startX
  
  if (resizeState.currentResizeBar === refs.resizeBar1) {
    // 사이드바와 채팅 섹션 사이 리사이즈
    const newSidebarWidth = Math.max(200, Math.min(500, resizeState.startWidths.sidebar + deltaX))
    const newChatWidth = Math.max(350, Math.min(800, resizeState.startWidths.chatSection - deltaX))
    
    if (refs.sidebar) {
      refs.sidebar.style.width = `${newSidebarWidth}px`
      refs.sidebar.style.flex = `0 0 ${newSidebarWidth}px`
    }
    if (refs.chatSection) {
      refs.chatSection.style.width = `${newChatWidth}px`
      refs.chatSection.style.flex = `1 1 ${newChatWidth}px`
    }
  } else if (resizeState.currentResizeBar === refs.resizeBar2) {
    // 채팅 섹션과 결과 사이드바 사이 리사이즈
    const newChatWidth = Math.max(350, Math.min(800, resizeState.startWidths.chatSection + deltaX))
    const newResultsWidth = Math.max(300, resizeState.startWidths.resultsSidebar - deltaX)
    
    if (refs.chatSection) {
      refs.chatSection.style.width = `${newChatWidth}px`
      refs.chatSection.style.flex = `1 1 ${newChatWidth}px`
    }
    if (refs.resultsSidebar) {
      refs.resultsSidebar.style.width = `${newResultsWidth}px`
      refs.resultsSidebar.style.flex = `1 1 ${newResultsWidth}px`
    }
  }
}

/**
 * 리사이즈 종료 함수
 * @param {Object} resizeState - 리사이즈 상태 객체
 * @param {Function} handleResizeMove - 리사이즈 이동 핸들러
 * @param {Function} handleResizeEnd - 리사이즈 종료 핸들러
 */
export const stopResize = (resizeState, handleResizeMove, handleResizeEnd) => {
  resizeState.isResizing = false
  resizeState.currentResizeBar = null
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
}

/**
 * 전체화면 모달 열기
 * @param {Object} result - 결과 객체
 * @param {Object} fullscreenState - 전체화면 상태 객체
 */
export const openFullscreen = (result, fullscreenState) => {
  fullscreenState.fullscreenResult = result
  fullscreenState.showFullscreen = true
  // body 스크롤 방지
  document.body.style.overflow = 'hidden'
  // 모달 DOM이 붙은 다음 Plotly가 사이즈를 다시 잡도록 강제
  nextTick(() => {
    window.dispatchEvent(new Event('resize'))
  })
}

/**
 * 전체화면 모달 닫기
 * @param {Object} fullscreenState - 전체화면 상태 객체
 */
export const closeFullscreen = (fullscreenState) => {
  fullscreenState.showFullscreen = false
  fullscreenState.fullscreenResult = null
  // body 스크롤 복원
  document.body.style.overflow = 'auto'
}

/**
 * 시간 포맷 함수
 * @param {Date|string} timestamp - 포맷할 시간
 * @returns {string} 포맷된 시간 문자열
 */
export const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    if (isNaN(date.getTime())) return ''
    
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return '방금 전'
    if (diffMins < 60) return `${diffMins}분 전`
    if (diffHours < 24) return `${diffHours}시간 전`
    if (diffDays < 7) return `${diffDays}일 전`
    
    return date.toLocaleString('ko-KR', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    console.error('시간 포맷 오류:', error)
    return ''
  }
}

/**
 * 파일 크기 포맷 함수
 * @param {number} bytes - 바이트 단위 파일 크기
 * @returns {string} 포맷된 파일 크기 문자열
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
