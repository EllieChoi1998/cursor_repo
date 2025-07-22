<template>
  <div id="app">
    <header class="app-header">
      <h1>Chat Assistant</h1>
      <p class="subtitle">Ask me about PCM / CP trends and data analysis, or Search Database via RAG system</p>
    </header>
    
    <main class="app-main">
      <div class="app-layout">
        <!-- Left Sidebar - Chat Room List -->
        <aside class="sidebar" ref="sidebar">
          <ChatRoomList 
            :activeChatId="activeChatId"
            :chatRooms="chatRooms"
            :isLoading="isLoadingChatRooms"
            @select-room="selectChatRoom"
            @create-room="createNewChatRoom"
            @delete-room="deleteChatRoom"
          />
        </aside>
        
        <!-- Resize Bar 1 -->
        <div class="resize-bar" ref="resizeBar1" @mousedown="startResize"></div>
        
        <!-- Center - Chat Interface -->
        <div class="chat-section" ref="chatSection">
          <div class="chat-container">
            <div class="chat-messages" ref="messagesContainer">
              <div 
                v-for="(message, index) in messages" 
                :key="index" 
                :class="['message', message.type, { 'error': message.isError, 'editable': message.isEditable, 'new-chatroom': message.isNewChatroom }]"
              >
                <div class="message-avatar">
                  <span v-if="message.type === 'user'">👤</span>
                  <span v-else-if="message.type === 'system'">🎉</span>
                  <span v-else>🤖</span>
                </div>
                <div class="message-content">
                  <div v-if="message.isEditable && message.type === 'user'" class="editable-message">
                    <input 
                      v-model="message.text"
                      @blur="editMessage(index, message.text)"
                      @keyup.enter="editMessage(index, message.text)"
                      class="message-edit-input"
                      :disabled="isLoading"
                    />
                    <button 
                      @click="editMessage(index, message.text)"
                      class="edit-button"
                      :disabled="isLoading"
                    >
                      ✏️
                    </button>
                  </div>
                  <div v-else class="message-text" v-html="message.text"></div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>
            </div>
            
            <div class="chat-input-container">
              <div class="input-controls">
                <div class="data-type-selector">
                  <label for="dataType">Data Type:</label>
                  <select 
                    id="dataType"
                    v-model="selectedDataType" 
                    class="data-type-dropdown"
                    :disabled="isLoading"
                  >
                    <option value="pcm">PCM (Process Control Monitor)</option>
                    <option value="cp">CP (Critical Path)</option>
                    <option value="rag">RAG (Retrieval-Augmented Generation)</option>
                  </select>
                </div>
                <div class="message-input-group">
                  <input 
                    v-model="currentMessage" 
                    @keyup.enter="sendMessage"
                    type="text" 
                    placeholder="Type your message here..."
                    class="chat-input"
                    :disabled="isLoading"
                  >
                  <button 
                    @click="sendMessage" 
                    class="send-button"
                    :disabled="!currentMessage.trim() || isLoading"
                  >
                    <span v-if="isLoading">⏳</span>
                                          <span v-else>📤</span>
                  </button>

                </div>
                <!-- 에러 메시지 표시 영역 -->
                <div v-if="showError" class="error-message">
                  <span class="error-icon">⚠️</span>
                  <span class="error-text">{{ currentError }}</span>
                  <button @click="clearErrorMessages" class="error-close-btn">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Resize Bar 2 -->
        <div class="resize-bar" ref="resizeBar2" @mousedown="startResize"></div>
        
        <!-- Right Sidebar - Results Section -->
        <aside class="results-sidebar" ref="resultsSidebar">
          <div v-if="results.length > 0" class="results-section">
            <div class="results-header">
              <h3>Analysis Results ({{ results.length }})</h3>
              <div class="results-controls">
                <button @click="clearAllResults" class="clear-button">Clear All</button>
              </div>
            </div>
            
            <div class="results-container">
              <div 
                v-for="(result, index) in results" 
                :key="result.id" 
                :class="['result-item', { 'active': result.isActive }]"
              >
                <div class="result-header">
                  <div class="result-info">
                    <h4>{{ result.title }}</h4>
                    <span class="result-type">{{ result.type }}</span>
                    <span class="result-time">{{ formatTime(result.timestamp) }}</span>
                    <span v-if="result.chatId" class="chat-id">Chat ID: {{ result.chatId }}</span>
                    <div v-if="result.userMessage" class="user-message">
                      <span class="user-message-label">💬 User Message:</span>
                      <span class="user-message-text">{{ result.userMessage }}</span>
                    </div>
                  </div>
                  <div class="result-actions">
                    <button 
                      @click="activateResult(result.id)" 
                      :class="['activate-btn', { 'active': result.isActive }]"
                    >
                      {{ result.isActive ? 'Active' : 'Activate' }}
                    </button>
                    <button 
                      @click="openFullscreen(result)" 
                      class="fullscreen-btn"
                      title="전체화면으로 보기"
                    >
                      🔍
                    </button>
                    <button @click="removeResult(result.id)" class="remove-btn">✕</button>
                  </div>
                </div>
                
                <!-- 항상 펼쳐서 보여주기 -->
                <div class="result-content">
                  <!-- PCM Trend Chart (기존 그래프 로직 유지) -->
                  <div v-if="result.type === 'pcm_trend'" class="chart-section">
                    <PCMTrendChart 
                      :data="result.data"
                      :height="chartHeight"
                      :title="result.title"
                    />
                  </div>
                  
                  <!-- PCM Trend Point Chart (기존 그래프 로직 유지) -->
                  <div v-else-if="result.type === 'pcm_trend_point'" class="chart-section">
                    <PCMTrendPointChart 
                      :data="result.data"
                      :height="chartHeight"
                      :title="result.title"
                      :maxLabels="50"
                      :dataSampling="false"
                    />
                  </div>

                  <!-- RAG Answer List (기존 RAG 로직 유지) -->
                  <div v-else-if="result.type === 'rag_search'" class="chart-section">
                    <RAGAnswerList :answer="result.answer" />
                  </div>

                  <!-- Metadata Only (real_data가 없는 경우) -->
                  <div v-else-if="result.type === 'metadata_only'" class="chart-section">
                    <div class="metadata-info">
                      <h4>📊 Analysis Metadata</h4>
                      <div class="metadata-details">
                        <p><strong>Result Type:</strong> {{ result.resultType }}</p>
                        <p v-if="result.sql"><strong>SQL:</strong> {{ result.sql }}</p>
                        <p v-if="result.metadata"><strong>Timestamp:</strong> {{ result.metadata.timestamp }}</p>
                        <p v-if="result.metadata && result.metadata.files">
                          <strong>Files:</strong> {{ result.metadata.files.length }} files found
                        </p>
                        <p v-if="result.metadata && result.metadata.response">
                          <strong>Response:</strong> {{ result.metadata.response }}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- 그 외 모든 result는 DynamicTable로 표시 (real_data가 있으면) -->
                  <div v-else-if="result.realData && result.realData.length > 0" class="chart-section">
                    <DynamicTable 
                      :data="result.realData"
                      :title="result.resultType || result.title || 'Data Table'"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Results가 없을 때 표시할 메시지 -->
          <div v-else class="no-results">
            <div class="no-results-icon">📊</div>
            <h3>Analysis Results</h3>
            <p>Send a message to see analysis results here</p>
          </div>
        </aside>
      </div>
    </main>
    
    <!-- 전체화면 모달 -->
    <div v-if="showFullscreen" class="fullscreen-modal" @click="closeFullscreen">
      <div class="fullscreen-content" @click.stop>
        <div class="fullscreen-header">
          <h2>{{ fullscreenResult?.title }}</h2>
          <div class="fullscreen-actions">
            <span class="result-type">{{ fullscreenResult?.type }}</span>
            <span class="result-time">{{ formatTime(fullscreenResult?.timestamp) }}</span>
            <button @click="closeFullscreen" class="close-fullscreen-btn">✕</button>
          </div>
          <div v-if="fullscreenResult?.userMessage" class="fullscreen-user-message">
            <span class="user-message-label">💬 User Message:</span>
            <span class="user-message-text">{{ fullscreenResult.userMessage }}</span>
          </div>
        </div>
        
        <div class="fullscreen-body">
          <!-- PCM Trend Chart -->
          <div v-if="fullscreenResult?.type === 'pcm_trend'" class="fullscreen-chart">
            <PCMTrendChart 
              :data="fullscreenResult.data"
              :height="800"
              :title="fullscreenResult.title"
              :maxLabels="50"
              :dataSampling="false"
            />
          </div>
          
          <!-- PCM Trend Point Chart -->
          <div v-else-if="fullscreenResult?.type === 'pcm_trend_point'" class="fullscreen-chart">
            <PCMTrendPointChart 
              :data="fullscreenResult.data"
              :height="800"
              :title="fullscreenResult.title"
              :maxLabels="50"
              :dataSampling="false"
            />
          </div>
          
          <!-- Commonality Table -->
          <div v-else-if="fullscreenResult?.type === 'commonality'" class="fullscreen-chart">
            <DynamicTable 
              :data="fullscreenResult.data || fullscreenResult.realData"
              :title="fullscreenResult.title || 'Commonality Analysis'"
            />
          </div>
          
          <!-- PCM Data Table -->
          <div v-else-if="fullscreenResult?.type === 'pcm_data'" class="fullscreen-chart">
            <DynamicTable 
              :data="fullscreenResult.data || fullscreenResult.realData"
              :title="fullscreenResult.title || 'PCM Data Table'"
            />
          </div>

          <!-- RAG Answer List -->
          <div v-else-if="fullscreenResult?.type === 'rag_search'" class="fullscreen-chart">
            <RAGAnswerList :answer="fullscreenResult.answer" />
          </div>
          
          <!-- Metadata Only (전체화면) -->
          <div v-else-if="fullscreenResult?.type === 'metadata_only'" class="fullscreen-chart">
            <div class="metadata-info-fullscreen">
              <h3>📊 Analysis Metadata</h3>
              <div class="metadata-details-fullscreen">
                <p><strong>Result Type:</strong> {{ fullscreenResult.resultType }}</p>
                <p v-if="fullscreenResult.sql"><strong>SQL:</strong> {{ fullscreenResult.sql }}</p>
                <p v-if="fullscreenResult.metadata"><strong>Timestamp:</strong> {{ fullscreenResult.metadata.timestamp }}</p>
                <p v-if="fullscreenResult.metadata && fullscreenResult.metadata.files">
                  <strong>Files:</strong> {{ fullscreenResult.metadata.files.length }} files found
                </p>
                <p v-if="fullscreenResult.metadata && fullscreenResult.metadata.response">
                  <strong>Response:</strong> {{ fullscreenResult.metadata.response }}
                </p>
              </div>
            </div>
          </div>
          
          <!-- 모든 기타 데이터 타입 -->
          <div v-else-if="fullscreenResult?.data || fullscreenResult?.realData" class="fullscreen-chart">
            <DynamicTable 
              :data="fullscreenResult.data || fullscreenResult.realData"
              :title="fullscreenResult.title || 'Data Table'"
            />
          </div>
        </div>
      </div>
    </div>
    
    <footer class="app-footer">
      <p>&copy; 2024 Chat Assistant. Built with Vue.js and Plotly.js</p>
    </footer>
  </div>
</template>

<script>
import { defineComponent, ref, computed, nextTick, onMounted } from 'vue'
import PCMTrendChart from './components/PCMTrendChart.vue'
import PCMTrendPointChart from './components/PCMTrendPointChart.vue'
import DynamicTable from './components/DynamicTable.vue'
import ChatRoomList from './components/ChatRoomList.vue'
import RAGAnswerList from './components/RAGAnswerList.vue'
import {
  streamChatAPI,
  generatePCMDataWithRealData,
  generateCommonalityDataWithRealData,
  createChatRoom,
  getChatRooms,
  getChatRoomHistory,
  deleteChatRoom as deleteChatRoomAPI
} from './services/api.js'
import { API_BASE_URL } from './services/api.js'
import { isErrorResponse, extractErrorMessage } from './config/dataTypes.js'

export default defineComponent({
  name: 'App',
  components: {
    PCMTrendChart,
    PCMTrendPointChart,
    DynamicTable,
    ChatRoomList,
    RAGAnswerList
  },
  setup() {

    
    const currentMessage = ref('')
    const selectedDataType = ref('pcm') // 기본값은 PCM
    const isLoading = ref(false)
    const messagesContainer = ref(null)
    const isDataLoading = ref(false)
    
    const chartHeight = ref(600)
    
    // 에러 상태 관리
    const currentError = ref('')
    const showError = ref(false)
    
    // 리사이즈 관련 refs
    const sidebar = ref(null)
    const chatSection = ref(null)
    const resultsSidebar = ref(null)
    const resizeBar1 = ref(null)
    const resizeBar2 = ref(null)
    
    // 리사이즈 상태
    const isResizing = ref(false)
    const currentResizeBar = ref(null)
    const startX = ref(0)
    const startWidths = ref({})
    
    // 전체화면 모달 상태 관리
    const fullscreenResult = ref(null)
    const showFullscreen = ref(false)

    const currentChatResponse = ref(null)
    
    // 채팅방 관련 상태
    const activeChatId = ref(null) // 백엔드에서 가져온 채팅방 ID
    const chatRooms = ref([])
    const isLoadingChatRooms = ref(false)
    
    // 채팅방별 메시지와 결과 저장
    const chatMessages = ref({
      'chat_1': [
        {
          type: 'bot',
          text: '안녕하세요! 데이터 분석 채팅 어시스턴트입니다.\n\n💡 사용 방법:\n1. 데이터 타입을 선택하세요 (PCM, CP, RAG)\n2. 메시지를 입력하고 전송하세요\n3. Enter 키를 누르거나 전송 버튼을 클릭하세요\n\n📊 지원하는 데이터 타입:\n• PCM (Process Control Monitor) - 트렌드 분석 및 공통성 분석\n• CP (Critical Path) - 성능 모니터링\n• RAG (Retrieval-Augmented Generation) - AI 기반 분석',
          timestamp: new Date()
        }
      ]
    })
    
    const chatResults = ref({
      'chat_1': []
    })

    // 새 채팅방 표시 상태 관리
    const newChatroomDisplay = ref({})

    // 현재 활성화된 채팅방의 메시지와 결과를 가져오는 computed
    const messages = computed(() => {
      if (!activeChatId.value) {
        // 활성 채팅방이 없을 때 기본 메시지 표시
        return [{
          type: 'bot',
          text: '채팅방을 선택해주세요.',
          timestamp: new Date()
        }]
      }
      
      const roomMessages = chatMessages.value[activeChatId.value] || []
      
      // 새 채팅방 표시가 활성화되어 있으면 디자인적인 메시지 추가
      if (newChatroomDisplay.value[activeChatId.value]) {
        return [
          {
            type: 'system',
            text: '새로운 채팅방',
            timestamp: new Date(),
            isNewChatroom: true
          },
          ...roomMessages
        ]
      }
      
      return roomMessages
    })
    
    const results = computed(() => {
      return chatResults.value[activeChatId.value] || []
    })
    
    // 현재 활성화된 결과의 데이터를 가져오는 computed
    const currentChartData = computed(() => {
      const activeResult = results.value.find(r => r.isActive)
      return activeResult?.data || []
    })

    const currentCommonalityData = computed(() => {
      const activeResult = results.value.find(r => r.isActive)
      return activeResult?.commonalityData || null
    })

    const uniqueDevices = computed(() => {
      const devices = currentChartData.value.map(row => row.DEVICE) // DEVICE column
      return [...new Set(devices)]
    })

    const dateRange = computed(() => {
      const dates = currentChartData.value.map(row => row.DATE_WAFER_ID) // DATE_WAFER_ID column
      if (dates.length === 0) return 'No data'
      const minDate = Math.min(...dates)
      const maxDate = Math.max(...dates)
      return `${minDate} - ${maxDate}`
    })

    const formatTime = (timestamp) => {
      return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    // 응답 데이터로부터 결과 객체 생성하는 함수
    const createResultFromResponseData = (responseData, userMessage, chatId) => {
      try {
        console.log('🔧 Creating result from response data:', responseData)
        
        if (!responseData) {
          console.warn('⚠️ No response data')
          return null
        }

        // real_data가 있으면 실제 데이터로 결과 생성, 없으면 메타데이터만 저장
        const realData = responseData.real_data || []
        let result = null

        // 결과 타입에 따라 다른 처리
        if (responseData.result === 'lot_start') {
          // PCM 트렌드 데이터 처리
          const chartData = generatePCMDataWithRealData(realData)
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'pcm_trend',
            title: `PCM Trend Analysis`,
            data: chartData,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: realData,
            resultType: responseData.result,
            userMessage: userMessage
          }
        } else if (responseData.result === 'lot_point') {
          // PCM 트렌드 포인트 데이터 처리
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'pcm_trend_point',
            title: `PCM Trend Point Chart`,
            data: realData,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: realData,
            userMessage: userMessage
          }
        } else if (responseData.result) {
          // real_data가 없어도 메타데이터만으로 결과 생성
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'metadata_only',
            title: `${responseData.result?.toUpperCase() || 'Data'} Analysis`,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql || responseData.SQL,
            realData: realData,
            resultType: responseData.result,
            userMessage: userMessage,
            metadata: responseData // 전체 메타데이터 저장
          }
        }

        if (result) {
          console.log('✅ Created result:', result)
        }
        return result
      } catch (error) {
        console.error('❌ Error creating result from response data:', error)
        return null
      }
    }

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const addMessage = (type, text, isEditable = false, originalMessage = null) => {
      if (!chatMessages.value[activeChatId.value]) {
        chatMessages.value = {
          ...chatMessages.value,
          [activeChatId.value]: []
        }
      }
      
      // 오류 메시지 중복 방지
      if (type === 'bot' && text.includes('❌')) {
        const existingError = chatMessages.value[activeChatId.value].find(msg => 
          msg.isError && msg.text.includes('❌')
        )
        if (existingError) {
          // 기존 오류 메시지 업데이트
          existingError.text = text
          existingError.timestamp = new Date()
          scrollToBottom()
          return
        }
      }
      
      const newMessage = {
        type,
        text,
        timestamp: new Date(),
        isEditable,
        originalMessage,
        isError: type === 'bot' && text.includes('❌')
      }
      
      const currentMessages = [...(chatMessages.value[activeChatId.value] || [])]
      currentMessages.push(newMessage)
      chatMessages.value = {
        ...chatMessages.value,
        [activeChatId.value]: currentMessages
      }
      
      // 수정 가능한 메시지를 맨 아래로 이동
      if (isEditable) {
        const messages = chatMessages.value[activeChatId.value]
        const lastIndex = messages.length - 1
        if (lastIndex > 0) {
          // 수정 가능한 메시지를 맨 뒤로 이동
          const editableMessage = messages.splice(lastIndex, 1)[0]
          messages.push(editableMessage)
        }
      }
      
      scrollToBottom()
    }

    // 에러 메시지 처리 함수
    const handleErrorMessage = (errorText, originalMessageText) => {
      // 에러 메시지를 채팅에서 제거 (이미 추가된 에러 메시지가 있다면)
      const messages = chatMessages.value[activeChatId.value]
      if (messages && messages.length > 0) {
        // 마지막 에러 메시지 제거
        const lastMessage = messages[messages.length - 1]
        if (lastMessage && lastMessage.isError) {
          messages.pop()
        }
      }
      
      // 에러 상태 설정
      currentError.value = errorText
      showError.value = true
      
      // 원본 메시지를 입력창에 자동 입력
      currentMessage.value = originalMessageText
      
      // 입력창에 포커스
      nextTick(() => {
        const inputElement = document.querySelector('.chat-input')
        if (inputElement) {
          inputElement.focus()
          inputElement.select()
        }
      })
    }

    // 에러 메시지들 제거 함수
    const clearErrorMessages = () => {
      const messages = chatMessages.value[activeChatId.value]
      if (messages) {
        // 에러 메시지들을 뒤에서부터 제거
        for (let i = messages.length - 1; i >= 0; i--) {
          if (messages[i].isError) {
            messages.splice(i, 1)
          }
        }
      }
      
      // 에러 상태 초기화
      currentError.value = ''
      showError.value = false
    }



    // 리사이즈 기능
    const startResize = (event) => {
      isResizing.value = true
      currentResizeBar.value = event.target
      startX.value = event.clientX
      
      // 현재 너비들 저장
      startWidths.value = {
        sidebar: sidebar.value?.offsetWidth || 280,
        chatSection: chatSection.value?.offsetWidth || 400,
        resultsSidebar: resultsSidebar.value?.offsetWidth || 500
      }
      
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      
      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', stopResize)
      event.preventDefault()
    }

    const handleResize = (event) => {
      if (!isResizing.value || !currentResizeBar.value) return
      
      const deltaX = event.clientX - startX.value
      
      if (currentResizeBar.value === resizeBar1.value) {
        // 사이드바와 채팅 섹션 사이 리사이즈
        const newSidebarWidth = Math.max(200, Math.min(500, startWidths.value.sidebar + deltaX))
        const newChatWidth = Math.max(350, Math.min(800, startWidths.value.chatSection - deltaX))
        
        if (sidebar.value) {
          sidebar.value.style.width = `${newSidebarWidth}px`
          sidebar.value.style.flex = `0 0 ${newSidebarWidth}px`
        }
        if (chatSection.value) {
          chatSection.value.style.width = `${newChatWidth}px`
          chatSection.value.style.flex = `1 1 ${newChatWidth}px`
        }
      } else if (currentResizeBar.value === resizeBar2.value) {
        // 채팅 섹션과 결과 사이드바 사이 리사이즈
        const newChatWidth = Math.max(350, Math.min(800, startWidths.value.chatSection + deltaX))
        const newResultsWidth = Math.max(300, Math.min(1200, startWidths.value.resultsSidebar - deltaX))
        
        if (chatSection.value) {
          chatSection.value.style.width = `${newChatWidth}px`
          chatSection.value.style.flex = `1 1 ${newChatWidth}px`
        }
        if (resultsSidebar.value) {
          resultsSidebar.value.style.width = `${newResultsWidth}px`
          resultsSidebar.value.style.flex = `1 1 ${newResultsWidth}px`
        }
      }
    }

    const stopResize = () => {
      isResizing.value = false
      currentResizeBar.value = null
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
    }

    // 전체화면 모달 제어 함수들
    const openFullscreen = (result) => {
      fullscreenResult.value = result
      showFullscreen.value = true
      // body 스크롤 방지
      document.body.style.overflow = 'hidden'
    }

    const closeFullscreen = () => {
      showFullscreen.value = false
      fullscreenResult.value = null
      // body 스크롤 복원
      document.body.style.overflow = 'auto'
    }

    // API에서 데이터 가져오기
    const loadPCMData = async () => {
      isDataLoading.value = true
      try {
        const data = await fetchPCMData()
        const newResult = {
          id: `local_${Date.now()}`, // 로컬 데이터는 별도 ID 사용
          type: 'pcm_data',
          title: 'PCM Data Load',
          data: data,
          isActive: true,
          timestamp: new Date()
        }
        
        // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
        const currentResults = chatResults.value[activeChatId.value] || []
        currentResults.forEach(r => r.isActive = false)
        currentResults.push(newResult)
        chatResults.value[activeChatId.value] = currentResults
        
        addMessage('bot', '✅ PCM 데이터를 성공적으로 로드했습니다!')
      } catch (error) {
        console.error('Failed to load PCM data:', error)
        addMessage('bot', '⚠️ 데이터 로드 중 오류가 발생했습니다. 기본 데이터를 사용합니다.')
      } finally {
        isDataLoading.value = false
      }
    }

    // 데이터 새로고침
    const refreshData = async () => {
      isDataLoading.value = true
      try {
        const data = await refreshPCMData()
        const newResult = {
          id: `local_${Date.now()}`, // 로컬 데이터는 별도 ID 사용
          type: 'pcm_data',
          title: 'PCM Data Refresh',
          data: data,
          isActive: true,
          timestamp: new Date()
        }
        
        // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
        const currentResults = chatResults.value[activeChatId.value] || []
        currentResults.forEach(r => r.isActive = false)
        currentResults.push(newResult)
        chatResults.value[activeChatId.value] = currentResults
        
        addMessage('bot', '🔄 데이터가 새로고침되었습니다!')
      } catch (error) {
        console.error('Failed to refresh data:', error)
        addMessage('bot', '⚠️ 데이터 새로고침 중 오류가 발생했습니다.')
      } finally {
        isDataLoading.value = false
      }
    }

    const processUserMessage = async (message) => {
      // 모든 메시지를 백엔드로 전송하여 백엔드에서 처리하도록 함
      await processStreamingChat(message)
    }

    // 스트리밍 채팅 처리 함수
    const processStreamingChat = async (message) => {
      try {
        // 선택된 데이터 타입으로 메시지를 백엔드로 전송하고 백엔드에서 유효성을 검사하도록 함
        addMessage('bot', '🔄 메시지를 처리하는 중...')
        
        await streamChatAPI(selectedDataType.value, message, activeChatId.value, (data) => {
          // 스트리밍 데이터 처리
          console.log('🎯 Received streaming data:', data)
          
          if (data.status === 'processing') {
            addMessage('bot', '⚙️ 데이터를 처리하고 있습니다...')
          } else if (data.error) {
            // 에러 발생 시 처리 - 채팅에 에러 메시지 추가하지 않음
            handleErrorMessage(`❌ 오류: ${data.error}`, message)
          } else if (isErrorResponse(data)) {
            // 백엔드 에러 응답 처리 - 채팅에 에러 메시지 추가하지 않음
            const errorMessage = extractErrorMessage(data)
            handleErrorMessage(`❌ 백엔드 오류: ${errorMessage}`, message)
            console.error('Backend error response:', data)
          } else if (data.response) {
            // 성공한 경우 에러 메시지들 제거
            clearErrorMessages()
            
            // 실제 응답 데이터 처리
            currentChatResponse.value = data

            
            if (data.response.result === 'lot_start') {
              // PCM 트렌드 데이터 처리
              const realData = data.response.real_data
              const chartData = generatePCMDataWithRealData(realData)
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'pcm_trend',
                title: `PCM Trend Analysis`,
                data: chartData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql,
                realData: realData,
                resultType: data.response.result,
                userMessage: userMessage ? userMessage.text : 'Unknown message'
              }
              
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              addMessage('bot', `✅ PCM 트렌드 데이터를 성공적으로 받았습니다!\n• SQL: ${data.response.sql}\n• Chat ID: ${data.chat_id}`)
              
              addMessage('bot', `Chart Summary:
• Total Records: ${chartData.length}
• Device Types: ${[...new Set(chartData.map(row => row.DEVICE))].join(', ')}
• Date Range: ${Math.min(...chartData.map(row => row.DATE_WAFER_ID))} - ${Math.max(...chartData.map(row => row.DATE_WAFER_ID))}`)
              
            } else if (data.response.result === 'lot_point') {
              // PCM 트렌드 포인트 데이터 처리
              const realData = data.response.real_data
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'pcm_trend_point',
                title: `PCM Trend Point Chart`,
                data: realData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql,
                realData: realData,
                userMessage: userMessage ? userMessage.text : 'Unknown message'
              }
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              addMessage('bot', `✅ PCM 트렌드 포인트 데이터를 성공적으로 받았습니다!\n• SQL: ${data.response.sql}\n• Chat ID: ${data.chat_id}`)
              addMessage('bot', `Chart Summary:\n• Total Records: ${realData.length}\n• PCM_SITE: ${[...new Set(realData.map(row => row.PCM_SITE))].join(', ')}\n• Date Range: ${Math.min(...realData.map(row => row.DATE_WAFER_ID))} - ${Math.max(...realData.map(row => row.DATE_WAFER_ID))}`)
            } 
            // 그래프나 RAG가 아닌 모든 응답은 테이블로 처리
            else if (data.response.real_data && data.response.real_data.length > 0) {
              const realData = data.response.real_data
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'dynamic_table',
                title: `${data.response.result.toUpperCase()} Analysis`,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql || data.response.SQL,
                realData: realData,
                resultType: data.response.result,
                userMessage: userMessage ? userMessage.text : 'Unknown message'
              }
              
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              addMessage('bot', `✅ ${data.response.result.toUpperCase()} 데이터를 성공적으로 받았습니다!\n• Result Type: ${data.response.result}\n• Total Records: ${realData.length}\n• Chat ID: ${data.chat_id}`)
            }

            else if (data.response.result === 'rag') {
              // RAG 응답 처리 - 모든 결과를 채팅 내역에 표시
              if (data.response.files) {
                // 파일 검색 결과를 채팅 메시지로 표시
                const files = data.response.files || []
                let fileListText = '📁 검색된 파일 목록:\n\n'
                
                files.forEach((file, index) => {
                  const fileName = file.file_name || file.filename || 'Unknown File'
                  const filePath = file.file_path || ''
                  // API_BASE_URL이 undefined인 경우 기본값 사용
                  const baseUrl = API_BASE_URL || 'http://localhost:8000'
                  const downloadUrl = filePath ? `${baseUrl}${filePath}` : ''
                  
                  fileListText += `${index + 1}. 📄 ${fileName}\n`
                  if (file.content) {
                    fileListText += `   내용: ${file.content.substring(0, 200)}${file.content.length > 200 ? '...' : ''}\n`
                  }
                  if (file.similarity || file.score) {
                    const score = file.similarity || file.score
                    fileListText += `   유사도 점수: ${(score * 100).toFixed(2)}%\n`
                  }
                  if (filePath) {
                    fileListText += `   경로: ${filePath}\n`
                  }
                  
                  // 다운로드 링크 추가
                  if (downloadUrl) {
                    fileListText += `   📥 <a href="${downloadUrl}" target="_blank" class="download-link">파일 보기</a>\n`
                  }
                  
                  fileListText += '\n'
                })
                
                addMessage('bot', fileListText)
              } else if (data.response.response) {
                // 텍스트 응답을 메시지에 추가
                addMessage('bot', data.response.response)
              } else {
                // 기타 RAG 응답
                addMessage('bot', '✅ RAG 검색이 완료되었습니다.')
              }
            }
            
            // 성공한 응답 후 입력창에 포커스
            nextTick(() => {
              const inputElement = document.querySelector('.chat-input')
              if (inputElement) {
                inputElement.focus()
              }
            })
          }
        })
        
      } catch (error) {
        console.error('Streaming chat error:', error)
        addMessage('bot', `❌ 스트리밍 API 오류: ${error.message}`)
      }
    }

    const sendMessage = async () => {
      const message = currentMessage.value.trim()
      if (!message || isLoading.value) return
      
      // 활성 채팅방이 없으면 첫 번째 채팅방 선택
      if (!activeChatId.value && chatRooms.value.length > 0) {
        await selectChatRoom(chatRooms.value[0].id)
      }
      
      // 채팅방이 여전히 없으면 에러
      if (!activeChatId.value) {
        addMessage('bot', '⚠️ 채팅방을 선택해주세요.')
        return
      }
      
      // 새 채팅방 표시 제거 (첫 번째 메시지 전송 시)
      if (newChatroomDisplay.value[activeChatId.value]) {
        newChatroomDisplay.value[activeChatId.value] = false
      }
      
      // 새 메시지 전송 시 기존 에러 메시지들 제거
      clearErrorMessages()
      
      // Add user message (수정 가능하게)
      const messageIndex = chatMessages.value[activeChatId.value]?.length || 0
      addMessage('user', message, true, messageIndex)
      currentMessage.value = ''
      isLoading.value = true
      
      // 채팅방 정보 업데이트
      updateChatRoomInfo(message)
      updateChatRoomName(message)
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Process the message
      await processUserMessage(message)
      
      isLoading.value = false
    }

    // 메시지 수정 기능
    const editMessage = async (messageIndex, newText) => {
      const messages = chatMessages.value[activeChatId.value]
      if (!messages || !messages[messageIndex]) return
      
      const message = messages[messageIndex]
      if (!message.isEditable) return
      
      // 원본 메시지 업데이트
      message.text = newText
      message.timestamp = new Date()
      
      // 에러 메시지들 제거 (실패한 응답들)
      const errorMessageIndices = []
      for (let i = messageIndex + 1; i < messages.length; i++) {
        if (messages[i].isError || messages[i].originalMessage === messageIndex) {
          errorMessageIndices.push(i)
        }
      }
      
      // 에러 메시지들을 뒤에서부터 제거
      for (let i = errorMessageIndices.length - 1; i >= 0; i--) {
        messages.splice(errorMessageIndices[i], 1)
      }
      
      // 수정된 메시지를 맨 아래로 이동
      const editedMessage = messages.splice(messageIndex, 1)[0]
      messages.push(editedMessage)
      
      // 수정된 메시지 재처리
      isLoading.value = true
      await processUserMessage(newText)
      isLoading.value = false
      
      // 스크롤을 맨 아래로
      scrollToBottom()
    }

    // 결과 관리 함수들
    const activateResult = (resultId) => {
      const currentResults = chatResults.value[activeChatId.value] || []
      currentResults.forEach(r => {
        r.isActive = r.id === resultId
      })
    }

    const removeResult = (resultId) => {
      const currentResults = chatResults.value[activeChatId.value] || []
      const index = currentResults.findIndex(r => r.id === resultId)
      if (index !== -1) {
        const removed = currentResults.splice(index, 1)[0]
        
        // 만약 삭제된 결과가 활성화되어 있었다면, 다른 결과를 활성화
        if (removed.isActive && currentResults.length > 0) {
          currentResults[currentResults.length - 1].isActive = true
        }
      }
    }

    const clearAllResults = () => {
      chatResults.value[activeChatId.value] = []
      addMessage('bot', 'All results cleared.')
    }

    // 채팅방 데이터 로드
    const loadChatRooms = async () => {
      isLoadingChatRooms.value = true
      try {
        console.log('🚀 Starting to load chatrooms...')
        const rooms = await getChatRooms()
        console.log('📋 Received rooms from API:', rooms)
        
        if (!rooms || rooms.length === 0) {
          console.warn('⚠️ No rooms received from API')
          chatRooms.value = []
          
          // 빈 배열일 때 기본 채팅방 생성 시도
          try {
            console.log('🔄 Attempting to create default chatroom...')
            const defaultRoom = await createChatRoom()
            console.log('✅ Created default room:', defaultRoom)
            
            // 새로 생성된 채팅방으로 목록 다시 로드
            await loadChatRooms()
            return
          } catch (createError) {
            console.error('❌ Failed to create default room:', createError)
            return
          }
        }
        
        chatRooms.value = rooms.map(room => {
          console.log('🏠 Processing room:', room)
          return {
            id: room.id,
            name: `채팅방 #${room.id}`, // ID를 포함한 이름으로
            dataType: 'pcm', // API 명세에 data_type이 없으므로 기본값
            lastMessage: `${room.message_count || 0}개의 메시지`,
            lastMessageTime: new Date(room.last_activity || new Date()),
            messageCount: room.message_count || 0
          }
        })
        
        console.log('Processed chatrooms:', chatRooms.value)
        
        // 각 채팅방의 메시지 히스토리 로드
        for (const room of rooms) {
          try {
            const history = await getChatRoomHistory(room.id)
            console.log(`Loading history for room ${room.id}:`, history)
            const messages = []
            
            // 히스토리를 메시지 형태로 변환
            if (history.recent_conversations && history.recent_conversations.length > 0) {
              console.log(`Found ${history.recent_conversations.length} conversations for room ${room.id}`)
              const results = [] // 결과 배열 초기화
              
              history.recent_conversations.forEach(conv => {
              messages.push({
                type: 'user',
                text: conv.user_message,
                timestamp: new Date(conv.chat_time),
                chatId: conv.chat_id // 백엔드에서 받은 chat_id 사용
              })
              
              // bot_response를 파싱하여 적절히 처리
              let botResponseText = conv.bot_response
              let responseData = null
              
              console.log('🔍 Parsing bot response:', conv.bot_response)
              
              try {
                const parsed = JSON.parse(conv.bot_response)
                console.log('✅ Parsed response data:', parsed)
                
                if (parsed.result) {
                  console.log('🔍 Processing result:', parsed.result)
                  // 실제 응답 데이터를 기반으로 구체적인 메시지 생성
                  if (parsed.result === 'lot_start') {
                    botResponseText = `✅ PCM 트렌드 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
                  } else if (parsed.result === 'lot_point') {
                    botResponseText = `✅ PCM 트렌드 포인트 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
                  } else if (parsed.result === 'commonality_start') {
                    botResponseText = `✅ PCM 커먼 분석이 완료되었습니다!\n• SQL: ${parsed.SQL || 'N/A'}\n• Determined: ${JSON.stringify(parsed.determined) || 'N/A'}\n• Chat ID: ${conv.chat_id}`
                  } else if (parsed.result === 'rag') {
                    if (parsed.files) {
                      botResponseText = `✅ RAG 검색이 완료되었습니다!\n• ${parsed.files.length}개의 파일을 찾았습니다.\n• Chat ID: ${conv.chat_id}`
                    } else if (parsed.response) {
                      botResponseText = `✅ RAG 응답: ${parsed.response}\n• Chat ID: ${conv.chat_id}`
                    } else {
                      botResponseText = `✅ RAG 분석이 완료되었습니다!\n• Chat ID: ${conv.chat_id}`
                    }
                  } else {
                    botResponseText = `✅ ${parsed.result.toUpperCase()} 분석이 완료되었습니다!\n• Chat ID: ${conv.chat_id}`
                  }
                  responseData = parsed
                  
                  // 응답 데이터가 있으면 결과 생성 (real_data가 없어도 메타데이터는 저장)
                  if (responseData) {
                    const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
                    if (result) {
                      results.push(result)
                    }
                  }
                } else {
                  console.warn('⚠️ No result field in parsed response')
                }
              } catch (e) {
                // JSON 파싱 실패시 원본 텍스트 사용
                console.warn('❌ Failed to parse bot response:', e)
                console.log('📄 Raw bot response:', conv.bot_response)
              }
              
              messages.push({
                type: 'bot',
                text: botResponseText,
                timestamp: new Date(conv.response_time),
                chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
                responseData: responseData // 파싱된 응답 데이터 저장
              })
            })
            
            // 결과 설정
            chatResults.value[room.id] = results
            } else {
              console.log(`No conversations found for room ${room.id}`)
            }
            
            console.log(`Setting messages for room ${room.id}:`, messages)
            // Vue의 reactivity를 위해 새 객체로 설정
            chatMessages.value = {
              ...chatMessages.value,
              [room.id]: messages
            }
            chatResults.value[room.id] = []
            console.log(`After setting, chatMessages[${room.id}]:`, chatMessages.value[room.id])
          } catch (error) {
            console.error(`Failed to load history for room ${room.id}:`, error)
            // 히스토리 로드 실패시 기본 메시지만 설정
            const welcomeMessage = {
              type: 'bot',
              text: '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, CP, RAG 분석에 대해 질문해주세요.',
              timestamp: new Date(room.last_activity)
            }
            chatMessages.value = {
              ...chatMessages.value,
              [room.id]: [welcomeMessage]
            }
            chatResults.value[room.id] = []
          }
        }
        
        // 첫 번째 채팅방을 기본으로 선택
        if (rooms.length > 0 && !activeChatId.value) {
          console.log('Selecting first chatroom:', rooms[0].id)
          await selectChatRoom(rooms[0].id)
        }
        
        // 디버깅: 최종 chatMessages 상태 확인
        console.log('Final chatMessages state after loading:', chatMessages.value)
      } catch (error) {
        console.error('Failed to load chatrooms:', error)
        addMessage('bot', '⚠️ 채팅방 목록을 불러오는데 실패했습니다.')
      } finally {
        isLoadingChatRooms.value = false
      }
    }
    
    // 채팅방 히스토리 새로고침 (필요시)
    const refreshChatRoomHistory = async (roomId) => {
      try {
        const history = await getChatRoomHistory(roomId)
        const messages = []
        const results = [] // 결과 배열 초기화
        
        // 히스토리를 메시지 형태로 변환
        history.recent_conversations.forEach(conv => {
          messages.push({
            type: 'user',
            text: conv.user_message,
            timestamp: new Date(conv.chat_time),
            chatId: conv.chat_id // 백엔드에서 받은 chat_id 사용
          })
          
          // bot_response를 파싱하여 적절히 처리
          let botResponseText = conv.bot_response
          let responseData = null
          
          console.log('🔍 Parsing bot response (refresh):', conv.bot_response)
          
          try {
            const parsed = JSON.parse(conv.bot_response)
            console.log('✅ Parsed response data (refresh):', parsed)
            
            if (parsed.result) {
              console.log('🔍 Processing result (refresh):', parsed.result)
              // 실제 응답 데이터를 기반으로 구체적인 메시지 생성
              if (parsed.result === 'lot_start') {
                botResponseText = `✅ PCM 트렌드 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
              } else if (parsed.result === 'lot_point') {
                botResponseText = `✅ PCM 트렌드 포인트 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
              } else if (parsed.result === 'commonality_start') {
                botResponseText = `✅ PCM 커먼 분석이 완료되었습니다!\n• SQL: ${parsed.SQL || 'N/A'}\n• Determined: ${JSON.stringify(parsed.determined) || 'N/A'}\n• Chat ID: ${conv.chat_id}`
              } else if (parsed.result === 'rag') {
                if (parsed.files) {
                  botResponseText = `✅ RAG 검색이 완료되었습니다!\n• ${parsed.files.length}개의 파일을 찾았습니다.\n• Chat ID: ${conv.chat_id}`
                } else if (parsed.response) {
                  botResponseText = `✅ RAG 응답: ${parsed.response}\n• Chat ID: ${conv.chat_id}`
                } else {
                  botResponseText = `✅ RAG 분석이 완료되었습니다!\n• Chat ID: ${conv.chat_id}`
                }
              } else {
                botResponseText = `✅ ${parsed.result.toUpperCase()} 분석이 완료되었습니다!\n• Chat ID: ${conv.chat_id}`
              }
              responseData = parsed
              
              // 응답 데이터가 있으면 결과 생성 (real_data가 없어도 메타데이터는 저장)
              if (responseData) {
                const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
                if (result) {
                  results.push(result)
                }
              }
            } else {
              console.warn('⚠️ No result field in parsed response (refresh)')
            }
          } catch (e) {
            // JSON 파싱 실패시 원본 텍스트 사용
            console.warn('❌ Failed to parse bot response (refresh):', e)
            console.log('📄 Raw bot response (refresh):', conv.bot_response)
          }
          
          messages.push({
            type: 'bot',
            text: botResponseText,
            timestamp: new Date(conv.response_time),
            chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
            responseData: responseData // 파싱된 응답 데이터 저장
          })
        })
        
        chatMessages.value = {
          ...chatMessages.value,
          [roomId]: messages
        }
        chatResults.value[roomId] = results
        
      } catch (error) {
        console.error(`Failed to refresh history for room ${roomId}:`, error)
        addMessage('bot', '⚠️ 채팅방 히스토리를 새로고침하는데 실패했습니다.')
      }
    }
    
    // 채팅방 관련 함수들
    const selectChatRoom = async (roomId) => {
      console.log(`Selecting chatroom ${roomId}`)
      console.log('Current chatMessages state:', chatMessages.value)
      console.log(`Messages for room ${roomId}:`, chatMessages.value[roomId])
      
      activeChatId.value = roomId
      const selectedRoom = chatRooms.value.find(room => room.id === roomId)
      if (selectedRoom) {
        selectedDataType.value = selectedRoom.dataType
        // 히스토리는 이미 loadChatRooms에서 로드되므로 별도 로드 불필요
        console.log(`Selected chatroom ${roomId} with ${(chatMessages.value[roomId] || []).length} messages`)
      }
    }

    const createNewChatRoom = async (newRoom) => {
      try {
        console.log('Creating new chatroom')
        
        // 백엔드에 새 채팅방 생성 (파라미터 없이)
        const createdRoom = await createChatRoom()
        console.log('Created room response:', createdRoom)
        
        // 로컬 상태 업데이트
        const roomData = {
          id: createdRoom.id,
          name: `채팅방 #${createdRoom.id}`, // ID를 포함한 이름으로
          dataType: 'pcm', // 기본값으로 설정
          lastMessage: '새로운 채팅방',
          lastMessageTime: new Date(), // 현재 시간으로 설정
          messageCount: 0
        }
        
        chatRooms.value.unshift(roomData)
        activeChatId.value = createdRoom.id
        selectedDataType.value = 'pcm' // 기본값으로 설정
        
        // 새 채팅방의 초기 메시지 설정 (빈 배열로 시작)
        chatMessages.value[createdRoom.id] = []
        
        // 새 채팅방의 결과 배열 초기화
        chatResults.value[createdRoom.id] = []
        
        // 새 채팅방 표시 활성화
        newChatroomDisplay.value[createdRoom.id] = true
        
        console.log('Successfully created and configured new chatroom:', createdRoom.id)
        
        // 채팅방 목록 새로고침
        await loadChatRooms()
        
      } catch (error) {
        console.error('Failed to create chatroom:', error)
        addMessage('bot', '⚠️ 새 채팅방 생성에 실패했습니다.')
      }
    }

    const deleteChatRoom = async (roomId) => {
      try {
        // 백엔드에서 채팅방 삭제
        await deleteChatRoomAPI(roomId)
        
        // 로컬 상태 업데이트
        const index = chatRooms.value.findIndex(room => room.id === roomId)
        if (index !== -1) {
          chatRooms.value.splice(index, 1)
          
          // 채팅방 데이터 삭제
          delete chatMessages.value[roomId]
          delete chatResults.value[roomId]
          delete newChatroomDisplay.value[roomId] // 채팅방 삭제 시 표시 상태도 제거
          
          // 삭제된 채팅방이 현재 활성화된 채팅방이었다면 다른 채팅방으로 전환
          if (activeChatId.value === roomId) {
            if (chatRooms.value.length > 0) {
              selectChatRoom(chatRooms.value[0].id)
            } else {
              // 모든 채팅방이 삭제된 경우
              activeChatId.value = null
            }
          }
        }
        
        // 채팅방 목록 새로고침
        await loadChatRooms()
        
      } catch (error) {
        console.error('Failed to delete chatroom:', error)
        addMessage('bot', '⚠️ 채팅방 삭제에 실패했습니다.')
      }
    }

    // 메시지 전송 시 채팅방 정보 업데이트
    const updateChatRoomInfo = (message) => {
      const currentRoom = chatRooms.value.find(room => room.id === activeChatId.value)
      if (currentRoom) {
        currentRoom.lastMessage = message
        currentRoom.lastMessageTime = new Date()
        currentRoom.messageCount += 1
      }
    }
    
    // 채팅방 이름 업데이트 (첫 번째 메시지 기반)
    const updateChatRoomName = (message) => {
      const currentRoom = chatRooms.value.find(room => room.id === activeChatId.value)
      if (currentRoom && !currentRoom.name.startsWith('새 채팅방')) {
        // 첫 번째 사용자 메시지를 기반으로 채팅방 이름 설정
        const shortMessage = message.length > 20 ? message.substring(0, 20) + '...' : message
        currentRoom.name = shortMessage
      }
    }

    onMounted(async () => {
      // 채팅방 데이터 로드
      await loadChatRooms()
      scrollToBottom()
      
      // ESC 키 이벤트 리스너 추가
      const handleKeydown = (event) => {
        if (event.key === 'Escape' && showFullscreen.value) {
          closeFullscreen()
        }
      }
      
      document.addEventListener('keydown', handleKeydown)
      
      // 컴포넌트 언마운트 시 이벤트 리스너 제거
      return () => {
        document.removeEventListener('keydown', handleKeydown)
      }
    })

          return {
        messages,
        currentMessage,
        selectedDataType,
        isLoading,
        isDataLoading,
        messagesContainer,
        chartHeight,
        results,
        currentChatResponse,
        uniqueDevices,
        dateRange,
        formatTime,
        sendMessage,
        activateResult,
        removeResult,
        clearAllResults,
        loadPCMData,
        refreshData,
        // 채팅방 관련
        activeChatId,
        chatRooms,
        isLoadingChatRooms,
        selectChatRoom,
        createNewChatRoom,
        deleteChatRoom,
        updateChatRoomInfo,
        updateChatRoomName,
        loadChatRooms,
        editMessage,
        newChatroomDisplay,
        handleErrorMessage,
        clearErrorMessages,

        // 에러 상태
        currentError,
        showError,
        // 전체화면 모달
        fullscreenResult,
        showFullscreen,
        openFullscreen,
        closeFullscreen,
        // 리사이즈 관련
        sidebar,
        chatSection,
        resultsSidebar,
        resizeBar1,
        resizeBar2,
        startResize
      }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f5f5;
  color: #333;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 0;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  font-weight: 300;
}

.subtitle {
  font-size: 1rem;
  opacity: 0.9;
}

.app-main {
  flex: 1;
  padding: 1rem;
  width: 100%;
  background: #f5f5f5;
}

.app-layout {
  display: flex;
  gap: 1rem;
  height: calc(100vh - 200px);
  min-height: 600px;
}

.sidebar {
  flex: 0 0 280px;
  width: 280px;
  min-width: 200px;
  max-width: 500px;
  flex-shrink: 0;
  background: none;
  position: relative;
}

.chat-section {
  flex: 1 1 400px;
  display: flex;
  flex-direction: column;
  min-width: 350px;
  max-width: 800px;
  position: relative;
}

.results-sidebar {
  flex: 1 1 500px;
  min-width: 300px;
  max-width: 1200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: none;
  position: relative;
}

/* Chat Container */
.chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex-shrink: 0;
}

.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 150px; /* 최소 높이 조정 */
}

.message {
  display: flex;
  gap: 0.75rem;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.bot {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.bot .message-avatar {
  background: #f0f0f0;
  color: #666;
}

.message-content {
  flex: 1;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 18px;
  white-space: pre-line;
  word-wrap: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.bot .message-text {
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.25rem;
  text-align: right;
}

.message.user .message-time {
  text-align: right;
}

.message.bot .message-time {
  text-align: left;
}

/* Chat Input */
.chat-input-container {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.input-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.data-type-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.data-type-selector label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  min-width: 80px;
}

.data-type-dropdown {
  padding: 0.5rem 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s ease;
  min-width: 200px;
}

.data-type-dropdown:focus {
  border-color: #667eea;
}

.data-type-dropdown:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.message-input-group {
  display: flex;
  gap: 0.5rem;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.chat-input:focus {
  border-color: #667eea;
}

.chat-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  width: 45px;
  height: 45px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: transform 0.2s ease;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Results Section */
.results-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.results-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.results-controls {
  display: flex;
  gap: 0.5rem;
}

.clear-button {
  padding: 0.5rem 1rem;
  border: 1px solid #dc3545;
  background: white;
  color: #dc3545;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.clear-button:hover {
  background: #dc3545;
  color: white;
}

.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.result-item {
  border-bottom: 1px solid #e0e0e0;
  transition: all 0.2s ease;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.active {
  background: #f8f9fa;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.result-header:hover {
  background: #f0f0f0;
}

.result-info {
  flex: 1;
}

.result-info h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1rem;
}

.result-type {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #667eea;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-right: 0.5rem;
}

.result-time {
  color: #666;
  font-size: 0.8rem;
  margin-right: 0.5rem;
}

.chat-id {
  color: #28a745;
  font-size: 0.8rem;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 0.5rem;
}

.activate-btn {
  padding: 0.25rem 0.75rem;
  border: 1px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.activate-btn:hover,
.activate-btn.active {
  background: #667eea;
  color: white;
}

.remove-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid #dc3545;
  background: white;
  color: #dc3545;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: #dc3545;
  color: white;
}

.fullscreen-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid #007bff;
  background: white;
  color: #007bff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.fullscreen-btn:hover {
  background: #007bff;
  color: white;
}

.result-content {
  padding: 0 1.5rem 1.5rem 1.5rem;
}

/* Chart Section */
.chart-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
  animation: slideIn 0.3s ease-out;
  min-width: 1200px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.chart-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.close-button:hover {
  background: #e0e0e0;
}

.app-footer {
  background-color: #333;
  color: white;
  text-align: center;
  padding: 1rem;
  margin-top: auto;
}

/* 반응형 레이아웃 조정 */
@media (max-width: 1400px) {
  .app-layout {
    gap: 0.5rem;
  }
  
  .results-sidebar {
    max-width: 700px;
  }
  
  .chat-section {
    max-width: 500px;
  }
}

@media (max-width: 1200px) {
  .app-layout {
    flex-direction: column;
    height: auto;
  }
  
  .sidebar {
    flex: 0 0 auto;
    width: 100%;
    min-width: unset;
    max-width: unset;
    order: 1;
    resize: none;
  }
  
  .chat-section {
    flex: 0 0 auto;
    min-width: unset;
    max-width: unset;
    width: 100%;
    height: 400px;
    order: 2;
    resize: none;
  }
  
  .results-sidebar {
    flex: 0 0 auto;
    min-width: unset;
    max-width: unset;
    width: 100%;
    order: 3;
    resize: none;
  }
}

@media (max-width: 768px) {
  .app-main {
    padding: 0.5rem;
  }
  
  .app-layout {
    gap: 0.5rem;
  }
  
  .chat-section {
    height: 350px;
  }
}

/* Error Message Styles */
.message.bot .message-text {
  white-space: pre-line;
}

.message.error .message-text {
  background: rgba(220, 53, 69, 0.1);
  border-left: 4px solid #dc3545;
  color: #dc3545;
  padding: 0.5rem;
  border-radius: 4px;
  margin: 0.25rem 0;
}

/* New Chatroom Display Styles */
.message.new-chatroom {
  justify-content: center;
  max-width: 100%;
  margin: 1rem 0;
}

.message.new-chatroom .message-content {
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  border-radius: 25px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  animation: newChatroomPulse 2s ease-in-out infinite;
}

.message.new-chatroom .message-text {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  padding: 0;
  background: none;
  border-radius: 0;
}

.message.new-chatroom .message-time {
  display: none;
}

@keyframes newChatroomPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  }
}

/* Editable Message Styles */
.message.editable {
  position: relative;
}

.editable-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.message-edit-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
}

.message-edit-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.edit-button {
  padding: 0.25rem 0.5rem;
  border: none;
  background: #667eea;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s ease;
}

.edit-button:hover:not(:disabled) {
  background: #5a6fd8;
}

.edit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Error Message Styles */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  animation: fadeIn 0.5s ease-out;
}

.error-icon {
  font-size: 1.1rem;
  color: #856404;
}

.error-text {
  flex: 1;
}

.error-close-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #856404;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.error-close-btn:hover {
  background-color: #ffeeba;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 1200px) {
  .app-layout {
    flex-direction: column;
    height: auto;
  }
  
  .sidebar {
    width: 100%;
    height: 300px;
  }
  
  .chat-section {
    height: 500px;
  }
  
  .results-sidebar {
    width: 100%;
    height: 400px;
  }
}

@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.5rem;
  }
  
  .app-main {
    padding: 0.5rem;
  }
  
  .app-layout {
    gap: 0.5rem;
  }
  
  .sidebar {
    height: 250px;
  }
  
  .chat-section {
    height: 400px;
  }
  
  .results-sidebar {
    height: 350px;
  }
  
  .message {
    max-width: 90%;
  }
  
  .data-type-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 0.25rem;
  }
  
  .data-type-selector label {
    min-width: auto;
  }
  
  .data-type-dropdown {
    min-width: auto;
  }
  
  .input-controls {
    gap: 0.5rem;
  }
}

/* No Results */
.no-results {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
}

.no-results-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-results h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.2rem;
}

.no-results p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.7;
}

/* Fullscreen Modal */
.fullscreen-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease-out;
}

.fullscreen-content {
  background: white;
  border-radius: 12px;
  width: 98vw;
  height: 96vh;
  max-width: 2200px;
  max-height: 1200px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.fullscreen-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.fullscreen-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.fullscreen-actions .result-type {
  padding: 0.25rem 0.75rem;
  background: #667eea;
  color: white;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.fullscreen-actions .result-time {
  color: #666;
  font-size: 0.9rem;
}

.close-fullscreen-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.close-fullscreen-btn:hover {
  background: #c82333;
}

.fullscreen-body {
  flex: 1;
  padding: 2rem;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 1200px;
  overflow-x: auto;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}



/* Resize Bar Styles */
.resize-bar {
  width: 8px;
  background: #e0e0e0;
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}

.resize-bar:hover {
  background: #007bff;
}

.resize-bar:active {
  background: #0056b3;
}

.resize-bar::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 20px;
  background: #999;
  border-radius: 1px;
}

.resize-bar:hover::before {
  background: white;
}

/* Download Link Styles */
.download-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 123, 255, 0.1);
  transition: all 0.2s ease;
}

.download-link:hover {
  background: rgba(0, 123, 255, 0.2);
  color: #0056b3;
  text-decoration: underline;
}

/* Message text에서 링크 스타일링 */
.message-text a {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 123, 255, 0.1);
  transition: all 0.2s ease;
}

.message-text a:hover {
  background: rgba(0, 123, 255, 0.2);
}

/* User Message Styles */
.user-message {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 6px;
  border-left: 3px solid #007bff;
}

.user-message-label {
  font-weight: 600;
  color: #007bff;
  font-size: 0.85rem;
  margin-right: 0.5rem;
}

.user-message-text {
  color: #333;
  font-size: 0.9rem;
  word-break: break-word;
  line-height: 1.4;
}

.fullscreen-user-message {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.fullscreen-user-message .user-message-label {
  font-weight: 600;
  color: #007bff;
  font-size: 1rem;
  margin-right: 0.75rem;
}

.fullscreen-user-message .user-message-text {
  color: #333;
  font-size: 1rem;
  word-break: break-word;
  line-height: 1.5;
}

/* Metadata Info Styles */
.metadata-info {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #17a2b8;
}

.metadata-info h4 {
  margin: 0 0 1rem 0;
  color: #17a2b8;
  font-size: 1.1rem;
}

.metadata-details p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.metadata-details strong {
  color: #495057;
  font-weight: 600;
}

.metadata-info-fullscreen {
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 6px solid #17a2b8;
  max-width: 800px;
  margin: 0 auto;
}

.metadata-info-fullscreen h3 {
  margin: 0 0 1.5rem 0;
  color: #17a2b8;
  font-size: 1.5rem;
}

.metadata-details-fullscreen p {
  margin: 0.75rem 0;
  font-size: 1rem;
  line-height: 1.5;
}

.metadata-details-fullscreen strong {
  color: #495057;
  font-weight: 600;
}
</style> 