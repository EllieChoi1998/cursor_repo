<template>
  <div id="app">
    <header class="app-header">
      <h1>PCM Chat Assistant</h1>
      <p class="subtitle">Ask me about PCM trends and data analysis</p>
    </header>
    
    <main class="app-main">
      <!-- Chat Interface -->
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div 
            v-for="(message, index) in messages" 
            :key="index" 
            :class="['message', message.type]"
          >
            <div class="message-avatar">
              <span v-if="message.type === 'user'">👤</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.text }}</div>
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
          </div>
        </div>
      </div>
      
      <!-- Results Section - Shows all accumulated results -->
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
              </div>
              <div class="result-actions">
                <button 
                  @click="activateResult(result.id)" 
                  :class="['activate-btn', { 'active': result.isActive }]"
                >
                  {{ result.isActive ? 'Active' : 'Activate' }}
                </button>
                <button @click="removeResult(result.id)" class="remove-btn">✕</button>
              </div>
            </div>
            
            <div v-if="result.isActive" class="result-content">
              <!-- PCM Trend Chart -->
              <div v-if="result.type === 'pcm_trend'" class="chart-section">
                <PCMTrendChart 
                  :data="result.data"
                  :height="chartHeight"
                  :title="result.title"
                />
              </div>
              
              <!-- Commonality Table -->
              <div v-else-if="result.type === 'commonality'" class="chart-section">
                <CommonalityTable 
                  :data="result.data"
                  :commonalityData="result.commonalityData"
                />
              </div>
              
              <!-- PCM Data Table -->
              <div v-else-if="result.type === 'pcm_data'" class="chart-section">
                <CommonalityTable 
                  :data="result.data"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="app-footer">
      <p>&copy; 2024 PCM Chat Assistant. Built with Vue.js and Plotly.js</p>
    </footer>
  </div>
</template>

<script>
import { defineComponent, ref, computed, nextTick, onMounted } from 'vue'
import PCMTrendChart from './components/PCMTrendChart.vue'
import CommonalityTable from './components/CommonalityTable.vue'
import { 
  fetchPCMData, 
  refreshPCMData, 
  fetchPCMDataByDateRange, 
  fetchPCMDataByDevice,
  streamChatAPI,
  generatePCMDataWithRealData,
  generateCommonalityDataWithRealData
} from './services/api.js'
import { isErrorResponse, extractErrorMessage } from './config/dataTypes.js'

export default defineComponent({
  name: 'App',
  components: {
    PCMTrendChart,
    CommonalityTable
  },
  setup() {
    const messages = ref([
      {
        type: 'bot',
        text: 'Hello! I\'m your Data Analysis Chat Assistant. I can help you with various data analysis tasks.\n\n💡 How to use:\n1. Select a data type from the dropdown (PCM, CP, RAG)\n2. Type your message in the input field\n3. Click send or press Enter\n\n📊 Available Data Types:\n• PCM (Process Control Monitor) - Trend analysis and commonality\n• CP (Critical Path) - Performance monitoring\n• RAG (Retrieval-Augmented Generation) - AI-powered analysis',
        timestamp: new Date()
      }
    ])
    
    const currentMessage = ref('')
    const selectedDataType = ref('pcm') // 기본값은 PCM
    const isLoading = ref(false)
    const messagesContainer = ref(null)
    const isDataLoading = ref(false)
    
    const chartHeight = ref(600)
    
    // 누적되는 결과들을 저장하는 배열
    const results = ref([])
    const currentChatResponse = ref(null)

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

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const addMessage = (type, text) => {
      messages.value.push({
        type,
        text,
        timestamp: new Date()
      })
      scrollToBottom()
    }

    // API에서 데이터 가져오기
    const loadPCMData = async () => {
      isDataLoading.value = true
      try {
        const data = await fetchPCMData()
        const newResult = {
          id: Date.now(),
          type: 'pcm_data',
          title: 'PCM Data Load',
          data: data,
          isActive: true,
          timestamp: new Date()
        }
        
        // 기존 결과들을 비활성화
        results.value.forEach(r => r.isActive = false)
        results.value.push(newResult)
        
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
          id: Date.now(),
          type: 'pcm_data',
          title: 'PCM Data Refresh',
          data: data,
          isActive: true,
          timestamp: new Date()
        }
        
        // 기존 결과들을 비활성화
        results.value.forEach(r => r.isActive = false)
        results.value.push(newResult)
        
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
        
        await streamChatAPI(selectedDataType.value, message, 1, (data) => {
          // 스트리밍 데이터 처리
          if (data.status === 'processing') {
            addMessage('bot', '⚙️ 데이터를 처리하고 있습니다...')
          } else if (data.error) {
            addMessage('bot', `❌ 오류: ${data.error}`)
          } else if (isErrorResponse(data)) {
            // 백엔드 에러 응답 처리
            const errorMessage = extractErrorMessage(data)
            addMessage('bot', `❌ 백엔드 오류: ${errorMessage}`)
            console.error('Backend error response:', data)
          } else if (data.response) {
            // 실제 응답 데이터 처리
            currentChatResponse.value = data
            

            
            if (data.response.result === 'lot_start') {
              // PCM 트렌드 데이터 처리
              const realData = data.response.real_data
              const chartData = generatePCMDataWithRealData(realData)
              
              const newResult = {
                id: Date.now(),
                type: 'pcm_trend',
                title: `PCM Trend Analysis`,
                data: chartData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                sql: data.response.sql,
                realData: realData
              }
              
              // 기존 결과들을 비활성화
              results.value.forEach(r => r.isActive = false)
              results.value.push(newResult)
              
              addMessage('bot', `✅ PCM 트렌드 데이터를 성공적으로 받았습니다!\n• SQL: ${data.response.sql}\n• Chat ID: ${data.chat_id}`)
              
              addMessage('bot', `Chart Summary:
• Total Records: ${chartData.length}
• Device Types: ${[...new Set(chartData.map(row => row.DEVICE))].join(', ')}
• Date Range: ${Math.min(...chartData.map(row => row.DATE_WAFER_ID))} - ${Math.max(...chartData.map(row => row.DATE_WAFER_ID))}`)
              
            } else if (data.response.result === 'commonality_start') {
              // Commonality 데이터 처리
              const realData = data.response.real_data
              const determinedData = data.response.determined
              
              const commonalityResult = generateCommonalityDataWithRealData(realData, determinedData)
              
              const newResult = {
                id: Date.now(),
                type: 'commonality',
                title: `Commonality Analysis`,
                data: commonalityResult.data,
                commonalityData: commonalityResult.commonality,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                sql: data.response.SQL,
                realData: realData
              }
              
              // 기존 결과들을 비활성화
              results.value.forEach(r => r.isActive = false)
              results.value.push(newResult)
              
              addMessage('bot', `✅ Commonality 데이터를 성공적으로 받았습니다!\n• SQL: ${data.response.SQL}\n• Chat ID: ${data.chat_id}`)
              
              addMessage('bot', `Commonality Summary:
• Good Lots: ${commonalityResult.commonality.good_lots.join(', ')}
• Bad Lots: ${commonalityResult.commonality.bad_lots.join(', ')}
• Good Wafers: ${commonalityResult.commonality.good_wafers.join(', ')}
• Bad Wafers: ${commonalityResult.commonality.bad_wafers.join(', ')}`)
            }
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
      
      // Add user message
      addMessage('user', message)
      currentMessage.value = ''
      isLoading.value = true
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Process the message
      await processUserMessage(message)
      
      isLoading.value = false
    }

    // 결과 관리 함수들
    const activateResult = (resultId) => {
      results.value.forEach(r => {
        r.isActive = r.id === resultId
      })
    }

    const removeResult = (resultId) => {
      const index = results.value.findIndex(r => r.id === resultId)
      if (index !== -1) {
        const removed = results.value.splice(index, 1)[0]
        
        // 만약 삭제된 결과가 활성화되어 있었다면, 다른 결과를 활성화
        if (removed.isActive && results.value.length > 0) {
          results.value[results.value.length - 1].isActive = true
        }
      }
    }

    const clearAllResults = () => {
      results.value = []
      addMessage('bot', 'All results cleared.')
    }

    onMounted(() => {
      scrollToBottom()
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
        refreshData
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
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Chat Container */
.chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 500px;
}

.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.results-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
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
  max-height: 800px;
  overflow-y: auto;
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

.activate-btn:hover {
  background: #667eea;
  color: white;
}

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

.result-content {
  padding: 0 1.5rem 1.5rem 1.5rem;
}

/* Chart Section */
.chart-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
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

/* Error Message Styles */
.message.bot .message-text {
  white-space: pre-line;
}

.message.bot .message-text:has(❌) {
  background: rgba(220, 53, 69, 0.1);
  border-left: 4px solid #dc3545;
  padding: 0.5rem;
  border-radius: 4px;
  margin: 0.25rem 0;
}

/* Responsive Design */
@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.5rem;
  }
  
  .app-main {
    padding: 0.5rem;
  }
  
  .chat-container {
    height: 400px;
  }
  
  .message {
    max-width: 90%;
  }
  
  .chart-section {
    margin-top: 1rem;
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
</style> 