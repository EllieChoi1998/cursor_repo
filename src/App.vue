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
          <input 
            v-model="currentMessage" 
            @keyup.enter="sendMessage"
            type="text" 
            placeholder="Type your message here... (try typing 'trend')"
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
      
      <!-- Chart Section - Only shown when showChart is true -->
      <div v-if="showChart" class="chart-section">
        <div class="chart-header">
          <h3>PCM Trend Analysis Chart</h3>
          <button @click="hideChart" class="close-button">✕</button>
        </div>
        <PCMTrendChart 
          :data="chartData"
          :height="chartHeight"
          :title="chartTitle"
        />
      </div>

      <!-- Commonality Table Section - Only shown when showCommonalityTable is true -->
      <div v-if="showCommonalityTable" class="chart-section">
        <div class="chart-header">
          <h3>PCM Commonality Analysis Table</h3>
          <button @click="hideCommonalityTable" class="close-button">✕</button>
        </div>
        <CommonalityTable 
          :data="chartData"
        />
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
import { fetchPCMData, refreshPCMData, fetchPCMDataByDateRange, fetchPCMDataByDevice } from './services/api.js'

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
        text: 'Hello! I\'m your PCM Chat Assistant. I can help you with trend analysis and data visualization. Try typing "trend" to see the PCM trend chart!',
        timestamp: new Date()
      }
    ])
    
    const currentMessage = ref('')
    const isLoading = ref(false)
    const showChart = ref(false)
    const showCommonalityTable = ref(false)
    const messagesContainer = ref(null)
    const isDataLoading = ref(false)
    
    const chartTitle = ref('PCM Trend Analysis')
    const chartHeight = ref(600)
    
    const chartData = ref([])

    const uniqueDevices = computed(() => {
      const devices = chartData.value.map(row => row[6]) // DEVICE column
      return [...new Set(devices)]
    })

    const dateRange = computed(() => {
      const dates = chartData.value.map(row => row[0]) // DATE_WAFER_ID column
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
        chartData.value = data
        addMessage('bot', '✅ PCM 데이터를 성공적으로 로드했습니다!')
      } catch (error) {
        console.error('Failed to load PCM data:', error)
        addMessage('bot', '⚠️ 데이터 로드 중 오류가 발생했습니다. 기본 데이터를 사용합니다.')
        chartData.value = []
      } finally {
        isDataLoading.value = false
      }
    }

    // 데이터 새로고침
    const refreshData = async () => {
      isDataLoading.value = true
      try {
        const data = await refreshPCMData()
        chartData.value = data
        addMessage('bot', '🔄 데이터가 새로고침되었습니다!')
      } catch (error) {
        console.error('Failed to refresh data:', error)
        addMessage('bot', '⚠️ 데이터 새로고침 중 오류가 발생했습니다.')
      } finally {
        isDataLoading.value = false
      }
    }

    const processUserMessage = async (message) => {
      const lowerMessage = message.toLowerCase().trim()
      
      if (lowerMessage === 'trend' || lowerMessage.includes('trend')) {
        if (chartData.value.length === 0) {
          addMessage('bot', '📊 데이터가 없습니다. 먼저 데이터를 로드해주세요. "load data"를 입력하세요.')
          return
        }
        
        showChart.value = true
        showCommonalityTable.value = false
        addMessage('bot', 'Here\'s the PCM trend analysis chart! The chart shows box plots for different device types with control lines (USL, LSL, UCL, LCL). You can see the data distribution and trends over time.')
        
        // Add some delay to simulate processing
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        addMessage('bot', `Chart Summary:
• Total Records: ${chartData.value.length}
• Device Types: ${uniqueDevices.value.join(', ')}
• Date Range: ${dateRange.value}`)
      } else if (lowerMessage === 'commonality' || lowerMessage.includes('commonality')) {
        if (chartData.value.length === 0) {
          addMessage('bot', '📊 데이터가 없습니다. 먼저 데이터를 로드해주세요. "load data"를 입력하세요.')
          return
        }
        
        showCommonalityTable.value = true
        showChart.value = false
        addMessage('bot', '📋 Here\'s the Commonality Analysis Table! This table shows detailed PCM data with 12 columns including statistical values and control limits. You can search, filter by device, and sort by any column.')
        
        // Add some delay to simulate processing
        await new Promise(resolve => setTimeout(resolve, 800))
        
        addMessage('bot', `Table Features:
• Search functionality for quick data lookup
• Device filtering (A, B, C)
• Sortable columns (click column headers)
• Pagination for large datasets
• 12 columns: Date Wafer ID, Min, Max, Q1, Q2, Q3, Device, USL, TGT, LSL, UCL, LCL`)
      } else if (lowerMessage.includes('load data') || lowerMessage.includes('load')) {
        await loadPCMData()
      } else if (lowerMessage.includes('refresh') || lowerMessage.includes('reload')) {
        await refreshData()
      } else if (lowerMessage.includes('help') || lowerMessage === '?') {
        addMessage('bot', 'I can help you with PCM data analysis! Here are some things you can ask me:\n\n• Type "load data" to fetch data from API\n• Type "refresh" to reload data\n• Type "trend" to view the PCM trend chart\n• Type "commonality" to view the data table\n• Ask about specific device types\n• Request data summaries\n• Ask for help with interpretation')
      } else if (lowerMessage.includes('device') || lowerMessage.includes('devices')) {
        if (chartData.value.length === 0) {
          addMessage('bot', '📊 데이터가 없습니다. 먼저 "load data"를 입력하여 데이터를 로드해주세요.')
          return
        }
        addMessage('bot', `The data contains ${uniqueDevices.value.length} device types: ${uniqueDevices.value.join(', ')}. Each device type has its own trend line in the chart.`)
      } else if (lowerMessage.includes('data') || lowerMessage.includes('summary')) {
        if (chartData.value.length === 0) {
          addMessage('bot', '📊 데이터가 없습니다. 먼저 "load data"를 입력하여 데이터를 로드해주세요.')
          return
        }
        addMessage('bot', `Data Summary:\n• Total Records: ${chartData.value.length}\n• Device Types: ${uniqueDevices.value.join(', ')}\• Date Range: ${dateRange.value}\n• The data includes MIN, MAX, Q1, Q2, Q3 values with control limits.`)
      } else {
        addMessage('bot', 'I\'m not sure I understand. Try typing "load data" to fetch data from API, "trend" to see the PCM trend chart, "commonality" to view the data table, or type "help" for more options.')
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

    const hideChart = () => {
      showChart.value = false
      addMessage('bot', 'Chart hidden. Type "trend" again to show it.')
    }

    const hideCommonalityTable = () => {
      showCommonalityTable.value = false
      addMessage('bot', 'Table hidden. Type "commonality" again to show it.')
    }

    onMounted(() => {
      scrollToBottom()
      // 앱 시작 시 자동으로 데이터 로드
      loadPCMData()
    })

    return {
      messages,
      currentMessage,
      isLoading,
      isDataLoading,
      showChart,
      showCommonalityTable,
      messagesContainer,
      chartTitle,
      chartHeight,
      chartData,
      uniqueDevices,
      dateRange,
      formatTime,
      sendMessage,
      hideChart,
      hideCommonalityTable,
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
  display: flex;
  padding: 1rem;
  gap: 0.5rem;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
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
}
</style> 