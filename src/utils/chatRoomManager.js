import { 
  getChatRooms, 
  getChatRoomHistory, 
  createChatRoom, 
  deleteChatRoom as deleteChatRoomAPI 
} from '../services/api'

/**
 * 채팅방 목록을 로드하는 함수
 * @param {Object} state - Vue 상태 객체
 * @param {Function} createResultFromResponseData - 결과 생성 함수
 * @param {Function} selectChatRoom - 채팅방 선택 함수
 * @returns {Promise<void>}
 */
export const loadChatRooms = async (state, createResultFromResponseData, selectChatRoom) => {
  state.isLoadingChatRooms.value = true
  try {
    console.log('🚀 Starting to load chatrooms...')
    const rooms = await getChatRooms()
    console.log('📦 Received rooms from API:', rooms)
    
    if (!rooms || rooms.length === 0) {
      console.warn('⚠️ No rooms received from API')
      state.chatRooms.value = []
      return
    }
    
    state.chatRooms.value = rooms.map(room => {
      console.log('🔧 Processing room:', room)
      return {
        id: room.id,
        name: room.name || `채팅방 #${room.id}`,
        dataType: 'pcm',
        lastMessage: `${room.message_count || 0}개의 메시지`,
        lastMessageTime: new Date(room.last_activity || new Date()),
        messageCount: room.message_count || 0
      }
    })
    
    console.log('✅ Processed chatrooms:', state.chatRooms.value)
    
    // 각 채팅방의 메시지 히스토리 로드
    for (const room of rooms) {
      try {
        const history = await getChatRoomHistory(room.id)
        console.log(`📜 Loading history for room ${room.id}:`, history)
        const messages = []
        
        // 히스토리를 메시지 형태로 변환
        if (history.recent_conversations && history.recent_conversations.length > 0) {
          console.log(`💬 Found ${history.recent_conversations.length} conversations for room ${room.id}`)
          const results = []
          
          history.recent_conversations.forEach(conv => {
            // 사용자 메시지 추가
            messages.push({
              type: 'user',
              text: conv.user_message,
              timestamp: new Date(conv.chat_time),
              chatId: conv.chat_id,
              originalTime: conv.chat_time
            })
            
            // bot_response 파싱
            let botResponseText = conv.bot_response
            let responseData = null
            
            try {
              const parsed = JSON.parse(conv.bot_response)
              
              if (parsed.success_message) {
                botResponseText = parsed.success_message
              } else if (parsed.result) {
                botResponseText = formatResultMessage(parsed, conv.chat_id)
              }
              
              responseData = parsed
              
              // 응답 데이터가 있으면 결과 생성
              if (responseData) {
                const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
                if (result) {
                  results.push(result)
                }
              }
            } catch (e) {
              console.warn('❌ Failed to parse bot response:', e)
            }
            
            // 봇 응답 메시지 추가
            messages.push({
              type: 'bot',
              text: botResponseText,
              timestamp: new Date(conv.response_time),
              chatId: conv.chat_id,
              responseData: responseData,
              originalTime: conv.response_time
            })
          })
          
          state.chatResults.value[room.id] = results
        } else {
          console.log(`📭 No conversations found for room ${room.id}`)
        }
        
        console.log(`💾 Setting messages for room ${room.id}:`, messages)
        state.chatMessages.value = {
          ...state.chatMessages.value,
          [room.id]: messages
        }
        
        if (!state.chatResults.value[room.id]) {
          state.chatResults.value[room.id] = []
        }
        
      } catch (error) {
        console.error(`❌ Failed to load history for room ${room.id}:`, error)
        // 히스토리 로드 실패시 기본 메시지 설정
        const welcomeMessage = {
          type: 'bot',
          text: '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, INLINE, RAG 분석에 대해 질문해주세요.',
          timestamp: new Date(room.last_activity)
        }
        state.chatMessages.value = {
          ...state.chatMessages.value,
          [room.id]: [welcomeMessage]
        }
        state.chatResults.value[room.id] = []
      }
    }
    
    // 첫 번째 채팅방을 기본으로 선택
    if (rooms.length > 0 && !state.activeChatId.value) {
      console.log('🎯 Selecting first chatroom:', rooms[0].id)
      await selectChatRoom(rooms[0].id)
    }
    
    console.log('🏁 Final chatMessages state after loading:', state.chatMessages.value)
  } catch (error) {
    console.error('❌ Failed to load chatrooms:', error)
  } finally {
    state.isLoadingChatRooms.value = false
  }
}

/**
 * 채팅방 히스토리를 새로고침하는 함수
 * @param {string} roomId - 채팅방 ID
 * @param {Object} state - Vue 상태 객체
 * @param {Function} createResultFromResponseData - 결과 생성 함수
 * @returns {Promise<void>}
 */
export const refreshChatRoomHistory = async (roomId, state, createResultFromResponseData) => {
  try {
    const history = await getChatRoomHistory(roomId)
    const messages = []
    const results = []
    
    history.recent_conversations.forEach(conv => {
      messages.push({
        type: 'user',
        text: conv.user_message,
        timestamp: new Date(conv.chat_time),
        chatId: conv.chat_id,
        originalTime: conv.chat_time
      })
      
      let botResponseText = conv.bot_response
      let responseData = null
      
      try {
        const parsed = JSON.parse(conv.bot_response)
        
        if (parsed.success_message) {
          botResponseText = parsed.success_message
        } else if (parsed.result) {
          botResponseText = formatResultMessage(parsed, conv.chat_id)
        }
        
        responseData = parsed
        
        if (responseData) {
          const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
          if (result) {
            results.push(result)
          }
        }
      } catch (e) {
        console.warn('❌ Failed to parse bot response (refresh):', e)
      }
      
      messages.push({
        type: 'bot',
        text: botResponseText,
        timestamp: new Date(conv.response_time),
        chatId: conv.chat_id,
        responseData: responseData,
        originalTime: conv.response_time
      })
    })
    
    state.chatMessages.value = {
      ...state.chatMessages.value,
      [roomId]: messages
    }
    state.chatResults.value[roomId] = results
    
  } catch (error) {
    console.error(`❌ Failed to refresh history for room ${roomId}:`, error)
  }
}

/**
 * 채팅방을 선택하는 함수
 * @param {string} roomId - 채팅방 ID
 * @param {Object} state - Vue 상태 객체
 * @param {Function} scrollToBottom - 스크롤 함수
 * @returns {Promise<void>}
 */
export const selectChatRoom = async (roomId, state, scrollToBottom) => {
  console.log(`🔄 Selecting chatroom ${roomId}`)
  console.log('📊 Previous activeChatId:', state.activeChatId.value)
  console.log(`💬 Messages for room ${roomId}:`, state.chatMessages.value[roomId]?.length || 0, 'messages')
  console.log(`📈 Results for room ${roomId}:`, state.chatResults.value[roomId]?.length || 0, 'results')
  
  state.activeChatId.value = roomId
  const selectedRoom = state.chatRooms.value.find(room => room.id === roomId)
  
  if (selectedRoom) {
    state.selectedDataType.value = selectedRoom.dataType
    console.log(`✅ Selected chatroom ${roomId} with data type: ${selectedRoom.dataType}`)
    console.log(`💬 Final messages count: ${(state.chatMessages.value[roomId] || []).length}`)
    console.log(`📈 Final results count: ${(state.chatResults.value[roomId] || []).length}`)
  }

  scrollToBottom()
}

/**
 * 새 채팅방을 생성하는 함수
 * @param {Object} state - Vue 상태 객체
 * @param {Function} loadChatRoomsFunc - 채팅방 목록 로드 함수
 * @returns {Promise<void>}
 */
export const createNewChatRoom = async (state, loadChatRoomsFunc) => {
  try {
    console.log('➕ Creating new chatroom')
    
    const createdRoom = await createChatRoom()
    console.log('✅ Created room response:', createdRoom)
    
    const roomData = {
      id: createdRoom.id,
      name: `채팅방 #${createdRoom.id}`,
      dataType: 'pcm',
      lastMessage: '새로운 채팅방',
      lastMessageTime: new Date(),
      messageCount: 0
    }
    
    state.chatRooms.value.unshift(roomData)
    state.activeChatId.value = createdRoom.id
    state.selectedDataType.value = 'pcm'
    
    // 새 채팅방 초기화
    state.chatMessages.value[createdRoom.id] = []
    state.chatResults.value[createdRoom.id] = []
    state.chatInputs.value[createdRoom.id] = ''
    state.chatErrors.value[createdRoom.id] = { show: false, message: '' }
    state.newChatroomDisplay.value[createdRoom.id] = true
    
    console.log('🎉 Successfully created and configured new chatroom:', createdRoom.id)
    
    // 채팅방 목록 새로고침
    await loadChatRoomsFunc()
    
  } catch (error) {
    console.error('❌ Failed to create chatroom:', error)
  }
}

/**
 * 채팅방을 삭제하는 함수
 * @param {string} roomId - 삭제할 채팅방 ID
 * @param {Object} state - Vue 상태 객체
 * @param {Function} selectChatRoomFunc - 채팅방 선택 함수
 * @param {Function} loadChatRoomsFunc - 채팅방 목록 로드 함수
 * @returns {Promise<void>}
 */
export const deleteChatRoom = async (roomId, state, selectChatRoomFunc, loadChatRoomsFunc) => {
  try {
    await deleteChatRoomAPI(roomId)
    
    const index = state.chatRooms.value.findIndex(room => room.id === roomId)
    if (index !== -1) {
      state.chatRooms.value.splice(index, 1)
      
      // 채팅방 데이터 삭제
      delete state.chatMessages.value[roomId]
      delete state.chatResults.value[roomId]
      delete state.chatInputs.value[roomId]
      delete state.chatErrors.value[roomId]
      delete state.newChatroomDisplay.value[roomId]
      
      // 삭제된 채팅방이 현재 활성화된 채팅방이었다면 다른 채팅방으로 전환
      if (state.activeChatId.value === roomId) {
        if (state.chatRooms.value.length > 0) {
          await selectChatRoomFunc(state.chatRooms.value[0].id)
        } else {
          state.activeChatId.value = null
        }
      }
    }
    
    // 채팅방 목록 새로고침
    await loadChatRoomsFunc()
    
  } catch (error) {
    console.error('❌ Failed to delete chatroom:', error)
  }
}

/**
 * 채팅방 정보를 업데이트하는 함수
 * @param {string} message - 메시지 내용
 * @param {Object} state - Vue 상태 객체
 */
export const updateChatRoomInfo = (message, state) => {
  const currentRoom = state.chatRooms.value.find(room => room.id === state.activeChatId.value)
  if (currentRoom) {
    currentRoom.lastMessage = message
    currentRoom.lastMessageTime = new Date()
    currentRoom.messageCount += 1
  }
}

/**
 * 채팅방 이름을 업데이트하는 함수 (첫 번째 메시지 기반)
 * @param {string} message - 메시지 내용
 * @param {Object} state - Vue 상태 객체
 */
export const updateChatRoomName = (message, state) => {
  const currentRoom = state.chatRooms.value.find(room => room.id === state.activeChatId.value)
  if (currentRoom && !currentRoom.name.startsWith('새 채팅방')) {
    const shortMessage = message.length > 20 ? message.substring(0, 20) + '...' : message
    currentRoom.name = shortMessage
  }
}

/**
 * 채팅방 이름 수정 핸들러
 * @param {Object} params - { roomId, name }
 */
export const handleUpdateRoomName = ({ roomId, name }) => {
  console.log('🔄 Chatroom name updated:', { roomId, name })
  // 로컬 상태는 이미 ChatRoomList에서 업데이트되었으므로 추가 작업 불필요
}

/**
 * 결과 메시지를 포맷하는 헬퍼 함수
 * @param {Object} parsed - 파싱된 응답 데이터
 * @param {string} chatId - 채팅 ID
 * @returns {string} 포맷된 메시지
 */
function formatResultMessage(parsed, chatId) {
  if (parsed.result === 'lot_start') {
    return `✅ PCM 트렌드 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${chatId}`
  } else if (parsed.result === 'lot_point') {
    return `✅ PCM 트렌드 포인트 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${chatId}`
  } else if (parsed.result === 'commonality_module') {
    return `✅ PCM 커먼 분석이 완료되었습니다!\n• SQL: ${parsed.SQL || 'N/A'}\n• Determined: ${JSON.stringify(parsed.determined) || 'N/A'}\n• Chat ID: ${chatId}`
  } else if (parsed.result === 'rag') {
    if (parsed.files) {
      return `✅ RAG 검색이 완료되었습니다!\n• ${parsed.files.length}개의 파일을 찾았습니다.\n• Chat ID: ${chatId}`
    } else if (parsed.response) {
      return `✅ RAG 응답: ${parsed.response}\n• Chat ID: ${chatId}`
    } else {
      return `✅ RAG 분석이 완료되었습니다!\n• Chat ID: ${chatId}`
    }
  } else {
    return `✅ ${parsed.result.toUpperCase()} 분석이 완료되었습니다!\n• Chat ID: ${chatId}`
  }
}
