<template>
  <div id="app">


    <header class="app-header">
      <div class="header-content">
        <h1>Chat Assistant</h1>
        <div class="user-info" v-if="currentUser">
          <span class="user-id">👤 {{ currentUser.userId }}</span>
          <button @click="logout" class="logout-btn" title="로그아웃">🚪</button>
        </div>
        <div class="login-prompt" v-else>
          <span class="login-message">로그인이 필요합니다</span>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <div class="app-layout">
        <!-- Left Sidebar - Chat Room List -->
        <aside class="sidebar" ref="sidebar">
          <div v-if="!isUserAuthenticated" class="auth-required">
            <div class="auth-message">
              <h3>🔐 로그인이 필요합니다</h3>
              <p>채팅 서비스를 이용하려면 로그인해주세요.</p>
            </div>
          </div>
          <ChatRoomList 
            v-else
            :activeChatId="activeChatId"
            :chatRooms="chatRooms"
            :isLoading="isLoadingChatRooms"
            @select-room="selectChatRoom"
            @create-room="createNewChatRoom"
            @delete-room="deleteChatRoom"
            @update-room-name="handleUpdateRoomName"
          />
        </aside>
        
        <!-- Resize Bar 1 -->
        <div class="resize-bar" ref="resizeBar1" @mousedown="startResize"></div>
        
        <!-- Center - Chat Interface -->
        <div class="chat-section" ref="chatSection">
          <div v-if="!isUserAuthenticated" class="auth-required">
            <div class="auth-message">
              <h3>🔐 로그인이 필요합니다</h3>
              <p>채팅 기능을 이용하려면 로그인해주세요.</p>
            </div>
          </div>
          <div v-else class="chat-container">
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
                  <!-- 사용자 메시지인 경우 수정 가능한 형태로 표시 -->
                  <div v-if="message.type === 'user'" class="user-message-container">
                    <!-- 수정 모드 -->
                    <div v-if="message.isEditing" class="editable-message">
                      <input 
                        v-model="message.editText"
                        @blur="saveEdit(index)"
                        @keyup.enter="saveEdit(index)"
                        @keyup.esc="cancelEdit(index)"
                        class="message-edit-input"
                        :disabled="isLoading"
                        ref="editInput"
                      />
                      <div class="edit-buttons">
                        <button 
                          @click="saveEdit(index)"
                          class="save-button"
                          :disabled="isLoading"
                          title="저장"
                        >
                          ✅
                        </button>
                        <button 
                          @click="cancelEdit(index)"
                          class="cancel-button"
                          :disabled="isLoading"
                          title="취소"
                        >
                          ❌
                        </button>
                      </div>
                    </div>
                    <!-- 일반 표시 모드 -->
                    <div v-else class="message-display">
                      <div class="message-text" v-html="message.text"></div>
                      <div class="message-actions">
                        <button 
                          @click="startEdit(index)"
                          class="edit-action-button"
                          :disabled="isLoading"
                          title="메시지 수정"
                        >
                          ✏️
                        </button>
                      </div>
                    </div>
                  </div>
                  <!-- 봇 메시지 처리 -->
                  <div v-else>
                    <!-- 파일 목록 메시지인 경우 -->
                    <div v-if="message.messageType === 'file_list'" class="file-list-message">
                      <div class="message-text">{{ message.text }}</div>
                      <div class="file-list">
                        <div 
                          v-for="(file, fileIndex) in message.files" 
                          :key="fileIndex"
                          class="file-item"
                        >
                          <div class="file-info">
                            <h4 class="file-name">
                               {{ file.file_name || file.filename || 'Unknown File' }}
                            </h4>
                            <div v-if="file.content" class="file-preview">
                              <strong>내용:</strong> {{ file.content.substring(0, 200) }}{{ file.content.length > 200 ? '...' : '' }}
                            </div>
                            <div v-if="file.similarity || file.score" class="file-score">
                              <strong>유사도 점수:</strong> {{ ((file.similarity || file.score)).toFixed(2) }}%
                            </div>
                            <div v-if="file.file_path" class="file-path">
                              <strong>경로:</strong> {{ file.file_path }}
                            </div>
                          </div>
                          <div class="file-actions">
                            <button 
                            @click="downloadFile(file.file_name || file.filename || 'Unknown File', file.file_path)"
                            class="file-download-btn"
                            :disabled="!file.file_path"
                            >
                             파일 다운로드
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div v-else-if="/^(SEARCH|SUMMARY)\|(True|False)\|/.test(message.text)">
                      <!-- RAG 검색 결과 중 파일 목록 형태의 메시지 -->
                      <div v-if="(() => { 
                        try {
                          const obj = JSON.parse(message.text.split('|')[2]);
                          return true
                        } catch(e) {
                          return false
                        }}) ()" class="file-list">
                        <div 
                          v-for="(file, fileIndex) in JSON.parse(message.text.split('|')[2])" 
                          :key="fileIndex"
                          class="file-item"
                        >
                          <div class="file-info">
                            <h4 class="file-name">
                               {{ file.file_name || file.filename || 'Unknown File' }}
                            </h4>
                            <div v-if="file.content" class="file-preview">
                              <strong>내용:</strong> {{ file.content.substring(0, 200) }}{{ file.content.length > 200 ? '...' : '' }}
                            </div>
                            <div v-if="file.similarity || file.score" class="file-score">
                              <strong>유사도 점수:</strong> {{ ((file.similarity || file.score)).toFixed(2) }}%
                            </div>
                            <div v-if="file.file_path" class="file-path">
                              <strong>경로:</strong> {{ file.file_path }}
                            </div>
                          </div>
                          <div class="file-actions">
                            <button 
                            @click="downloadFile(file.file_name || file.filename || 'Unknown File', file.file_path)"
                            class="file-download-btn"
                            :disabled="!file.file_path"
                            >
                             파일 다운로드
                            </button>
                          </div>
                        </div>
                      </div>
                      <!-- RAG 검색 결과 중 일반 텍스트 메시지 -->
                      <div v-else class="message-text" v-html="message.text.split('|')[2]"></div>
                    </div>
                    <!-- 일반 텍스트 메시지 -->
                    <div v-else class="message-text" v-html="message.text"></div>
                  </div>
                  
                  <div class="message-time">
                    {{ formatTime(message.timestamp) }}
                    <span v-if="message.originalTime && showOriginalTime" class="original-time" :title="message.originalTime">
                      (원본: {{ new Date(message.originalTime).toLocaleString('ko-KR') }})
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="chat-input-container">
              <div class="input-controls">
                <div class="input-controls-top">
                  <div class="data-type-selector">
                    <label for="dataType">Data Type:</label>
                    <select 
                      id="dataType"
                      v-model="selectedDataType" 
                      class="data-type-dropdown"
                      :disabled="isLoading"
                    >
                      <option value="pcm">PCM (Process Control Monitor)</option>
                      <option value="inline">INLINE (Inline Analysis)</option>
                      <option value="rag">불량 이력 검색</option>
                      <option value="excel">엑셀 데이터 분석</option>
                      <option value="dcc">표준 문서 검색</option>
                    </select>
                  </div>
                  <div class="time-toggle">
                    <button 
                      @click="showOriginalTime = !showOriginalTime" 
                      :class="['time-toggle-btn', { 'active': showOriginalTime }]"
                      title="원본 시간 표시 토글"
                    >
                      {{ showOriginalTime ? '🕐' : '🕑' }} 원본시간
                    </button>
                  </div>
                  <div class="analysis-toggle">
                    <button 
                      @click="toggleAnalysisSection" 
                      :class="['analysis-toggle-btn', { 'collapsed': isAnalysisCollapsed }]"
                      :title="isAnalysisCollapsed ? 'Analysis Results 펼치기' : 'Analysis Results 접기'"
                    >
                      {{ isAnalysisCollapsed ? '📊' : '📈' }}
                    </button>
                  </div>
                </div>
                <div class="message-input-group">
                  <textarea 
                    v-model="currentMessage" 
                    @input="adjustTextareaHeight"
                    @keydown="handleKeyDown"
                    placeholder="Type your message here... (Enter for new line, Tab to send)"
                    class="chat-input"
                    :disabled="isLoading"
                    ref="messageInput"
                  ></textarea>
                  
                  <!-- 엑셀 파일 업로드 버튼 (엑셀 선택 시에만 표시) -->
                  <button 
                    v-if="selectedDataType === 'excel'"
                    @click="triggerFileUpload" 
                    class="file-upload-button"
                    :disabled="isLoading"
                    title="엑셀 파일 업로드"
                  >
                    📁
                  </button>
                  
                  <button 
                    @click="sendMessage" 
                    class="send-button"
                    :disabled="!currentMessage.trim() || isLoading"
                    :title="selectedFile ? '파일과 함께 업로드' : '메시지 전송'"
                  >
                    <span v-if="isLoading">⏳</span>
                    <span v-else>📤</span>
                  </button>

                </div>
                
                <!-- 선택된 파일 표시 영역 -->
                <div v-if="selectedFile" class="selected-file-display">
                  <span class="file-icon">📎</span>
                  <span class="file-name">{{ selectedFile.name }}</span>
                  <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
                  <button @click="removeSelectedFile" class="file-remove-btn" title="파일 제거">
                    ✕
                  </button>
                </div>
                
                <!-- 숨겨진 파일 입력 -->
                <input 
                  ref="fileInput"
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  @change="handleFileSelect"
                  style="display: none"
                />
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
        <div v-if="!isAnalysisCollapsed" class="resize-bar" ref="resizeBar2" @mousedown="startResize"></div>
        
        <!-- Right Sidebar - Results Section -->
        <aside v-if="!isAnalysisCollapsed" class="results-sidebar" ref="resultsSidebar">
          <div v-if="results.length > 0" class="results-section">
            <div class="results-header">
              <h3>Analysis Results ({{ results.length }})</h3>
              <div class="results-controls">
                <button 
                  @click="toggleAnalysisSection" 
                  class="toggle-button"
                  :title="isAnalysisCollapsed ? '펼치기' : '접기'"
                >
                  {{ isAnalysisCollapsed ? '📂' : '📁' }}
                </button>
                <button @click="clearAllResults" class="clear-button">Clear All</button>
              </div>
            </div>
            
            <div v-if="!isAnalysisCollapsed" class="results-container">
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
                  
                            <!-- PCM To Trend Chart (sameness_to_trend, commonality_to_trend) -->
          <div v-else-if="result.type === 'sameness_to_trend' || result.type === 'commonality_to_trend'" class="chart-section">
                    <PCMToTrend 
                      :data="result.data"
                      :height="chartHeight"
                      :resultType="result.type"
                      :graphName="result.graphName"
                      :maxLabels="50"
                      :dataSampling="false"
                    />
                  </div>

                  <!-- RAG Answer List (기존 RAG 로직 유지) -->
                  <div v-else-if="result.type === 'rag_search'" class="chart-section">
                    <RAGAnswerList :answer="result.answer" />
                  </div>

                  <!-- Excel Analysis Results -->
                  <div v-else-if="result.type === 'excel_analysis' || result.type === 'excel_chart' || result.type === 'excel_summary'" class="chart-section">
                    <div class="excel-analysis-result">
                      <div class="excel-header">
                        <h4>📊 {{ result.title }}</h4>
                        <p class="file-name">파일: {{ result.fileName }}</p>
                      </div>
                      
                        <div v-if="result.successMessage" class="excel-success-message">
                          {{ result.successMessage }}
                        </div>
                      
                      <!-- 분석 요약 -->
                      <div v-if="result.summary" class="excel-summary">
                        <h5>📋 분석 요약</h5>
                        <div class="summary-content">{{ result.summary }}</div>
                      </div>
                      
                      <!-- 차트 데이터 (excel_chart인 경우) -->
                      <div v-if="result.type === 'excel_chart' && result.chartConfig" class="excel-chart">
                        <h5>📈 데이터 시각화</h5>
                        <div class="chart-info">
                          <p><strong>차트 타입:</strong> {{ result.chartConfig.chart_type }}</p>
                          <p v-if="result.chartConfig.x_column"><strong>X축:</strong> {{ result.chartConfig.x_column }}</p>
                          <p v-if="result.chartConfig.y_column"><strong>Y축:</strong> {{ result.chartConfig.y_column }}</p>
                          <p><strong>데이터 포인트:</strong> {{ result.chartConfig.data?.length || 0 }}개</p>
                        </div>
                        <!-- 여기에 실제 차트 컴포넌트를 추가할 수 있습니다 -->
                      </div>
                      
                      <!-- 데이터 테이블 (excel_analysis인 경우) -->
                      <div v-if="result.type === 'excel_analysis' && result.data?.basic_info" class="excel-data-table">
                        <h5>📋 데이터 정보</h5>
                        <div class="data-info">
                          <p><strong>행 수:</strong> {{ result.data.basic_info.shape[0] }}</p>
                          <p><strong>열 수:</strong> {{ result.data.basic_info.shape[1] }}</p>
                          <p><strong>컬럼:</strong> {{ result.data.basic_info.columns.join(', ') }}</p>
                        </div>
                        
                        <!-- 샘플 데이터 표시 -->
                        <div v-if="result.data.basic_info.sample_data" class="sample-data">
                          <h6>샘플 데이터 (상위 10행)</h6>
                          <div class="table-container">
                            <table class="data-table">
                              <thead>
                                <tr>
                                  <th v-for="column in result.data.basic_info.columns" :key="column">
                                    {{ column }}
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr v-for="(row, index) in result.data.basic_info.sample_data" :key="index">
                                  <td v-for="column in result.data.basic_info.columns" :key="column">
                                    {{ row[column] }}
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                      
                      <!-- 통계 정보 (excel_analysis인 경우) -->
                      <div v-if="result.type === 'excel_analysis' && result.data?.statistics" class="excel-statistics">
                        <h5>📊 통계 정보</h5>
                        <div class="stats-grid">
                          <div v-for="(stats, column) in result.data.statistics" :key="column" class="stat-item">
                            <h6>{{ column }}</h6>
                            <ul>
                              <li>평균: {{ stats.mean?.toFixed(2) }}</li>
                              <li>표준편차: {{ stats.std?.toFixed(2) }}</li>
                              <li>최솟값: {{ stats.min?.toFixed(2) }}</li>
                              <li>최댓값: {{ stats.max?.toFixed(2) }}</li>
                              <li>중앙값: {{ stats.median?.toFixed(2) }}</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                    </div>

                    <!-- Plotly Graph Results -->
                    <div v-else-if="isPlotlyGraphType(result.type)" class="chart-section plotly-section">
                      <!-- Multiple Graphs (graph_specs array) -->
                      <div v-if="result.graphSpecs && result.graphSpecs.length > 0" class="multiple-graphs-container">
                        <div 
                          v-for="(graphSpec, graphIndex) in result.graphSpecs" 
                          :key="`${result.id}-graph-${graphIndex}`"
                          class="single-graph-wrapper"
                        >
                          <PlotlyGraph
                            :graph-spec="graphSpec"
                            :title="graphSpec?.layout?.title?.text || graphSpec?.layout?.title || `Graph ${graphIndex + 1}`"
                            :file-name="result.fileName"
                            :success-message="''"
                            :height="chartHeight"
                          />
                        </div>
                      </div>
                      
                      <!-- Single Graph (legacy graph_spec) -->
                      <div v-else class="single-graph-wrapper">
                        <PlotlyGraph
                          :graph-spec="result.graphSpec"
                          :title="result.title"
                          :file-name="result.fileName"
                          :success-message="''"
                          :height="chartHeight"
                        />
                      </div>

                      <div
                        v-if="result.realDataSets && result.realDataSets.length"
                        class="plotly-real-data"
                      >
                        <details
                          v-for="(dataset, datasetIndex) in result.realDataSets"
                          :key="`${result.id}-dataset-${datasetIndex}`"
                          class="plotly-data-set"
                          open
                        >
                          <summary>
                            📄 데이터셋
                            <span v-if="dataset && dataset.length">({{ dataset.length }}행)</span>
                          </summary>
                          <DynamicTable
                            :data="dataset"
                            :title="`데이터셋`"
                          />
                        </details>
                      </div>
                    </div>

                    <!-- General Text Results -->
                    <div v-else-if="result.type === 'general_text'" class="chart-section general-text-section">
                      <div class="general-text-card">
                        <h5>📝 분석 결과</h5>
                        <p v-if="result.successMessage">{{ result.successMessage }}</p>
                        <p v-else-if="result.summary">{{ result.summary }}</p>
                        <p v-else-if="result.textContent">{{ result.textContent }}</p>
                        <p v-else class="empty-text">표시할 메시지가 없습니다.</p>
                      </div>
                    </div>

                    <!-- Table Results -->
                    <div v-else-if="result.type === 'table'" class="chart-section table-result-section">
                      <div
                        v-if="result.realDataSets && result.realDataSets.length"
                        class="table-datasets"
                      >
                        <DynamicTable
                          v-for="(dataset, datasetIndex) in result.realDataSets"
                          :key="`${result.id}-table-${datasetIndex}`"
                          :data="dataset"
                          :title="`데이터 테이블`"
                        />
                      </div>
                      <div v-else class="empty-table">
                        표시할 데이터가 없습니다.
                      </div>
                    </div>

                  <!-- Metadata Only (real_data가 없는 경우) -->
                  <div v-else-if="result.type === 'metadata_only'" class="chart-section">
                    <div class="metadata-info">
                      <h4> Analysis Metadata</h4>
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

                  <!-- Two Dynamic Tables (lot_hold_pe_confirm_module) -->
                  <div v-else-if="result.type === 'lot_hold_pe_confirm_module'" class="chart-section">
                    <TwoDynamicTables 
                      :data="[result.realData]"
                      :title="result.title || 'Lot Hold & PE Module Analysis'"
                    />
                  </div>

                  <!-- INLINE Trend Chart (inline_trend_initial, inline_trend_followup)
                  <div v-else-if="result.type === 'inline_trend_initial' || result.type === 'inline_trend_followup'" class="chart-section inline-vertical">
                    <INLINETrendChart 
                      :backendData="result.backendData"
                      :height="chartHeight"
                      :title="result.title || 'Inline Trend Analysis'"
                    />
                  </div> -->
                  <!-- INLINE Trend Chart (LLM spec가 있으면 LLMDrivenInlineChart로) -->
                  <div
                    v-else-if="(result.type === 'inline_trend_initial' || result.type === 'inline_trend_followup') && result.backendData?.llm_spec"
                    class="chart-section inline-vertical"
                  >
                    <LLMDrivenInlineChart
                      :backendData="result.backendData"
                      :height="chartHeight"
                      :title="result.title || 'Inline Trend (LLM Spec)'"
                    />
                  </div>
                  <!-- LLM spec가 없으면 기존 INLINETrendChart로 -->
                  <div
                    v-else-if="result.type === 'inline_trend_initial' || result.type === 'inline_trend_followup'"
                    class="chart-section inline-vertical"
                  >
                    <INLINETrendChart
                      :backendData="result.backendData"
                      :height="chartHeight"
                      :title="result.title || 'Inline Trend Analysis'"
                    />
                  </div>

                  <!-- CPK 달성률 분석 (cpk_achieve_rate_initial) -->
                  <div v-else-if="result.type === 'cpk_achieve_rate_initial'" class="chart-section">
                    <CPKAchieveRateChart
                      :backendData="result.backendData"
                      :height="chartHeight"
                      :title="result.title || 'CPK 달성률 분석'"
                    />
                  </div>

                  <!-- Low CPK Trend Module -->
                  <div v-else-if="result.type === 'low_cpk_chart_trend' || result.type === 'low_cpk_analysis_trend'" class="chart-section inline-vertical">
                    <LowCPKTrendChart
                      :backendData="result.backendData"
                      :height="chartHeight"
                    />
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
            <div class="results-header">
              <h3>Analysis Results (0)</h3>
              <div class="results-controls">
                <button 
                  @click="toggleAnalysisSection" 
                  class="toggle-button"
                  :title="isAnalysisCollapsed ? '펼치기' : '접기'"
                >
                  {{ isAnalysisCollapsed ? '📂' : '📁' }}
                </button>
              </div>
            </div>
            <div v-if="!isAnalysisCollapsed" class="no-results-content">
              <div class="no-results-icon"></div>
              <p>Send a message to see analysis results here</p>
            </div>
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

        </div>
        
        <div class="fullscreen-body" :class="{ 'fullscreen-body-stretch': isPlotlyGraphType(fullscreenResult?.type) }">
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
          
          <!-- INLINE Trend Chart (inline_trend_initial, inline_trend_followup)
          <div v-else-if="fullscreenResult?.type === 'inline_trend_initial' || fullscreenResult?.type === 'inline_trend_followup'" class="fullscreen-chart inline-vertical">
            <INLINETrendChart 
              :key="`inline-full-${fullscreenResult?.id}-${showFullscreen}`"
              :backendData="fullscreenResult.backendData"
              :height="800"
              :title="fullscreenResult.title || 'Inline Trend Analysis'"
            />
          </div> -->
          <!-- INLINE Trend Chart (LLM spec가 있으면 LLMDrivenInlineChart로) -->
          <div
            v-else-if="(fullscreenResult?.type === 'inline_trend_initial' || fullscreenResult?.type === 'inline_trend_followup') && fullscreenResult?.backendData?.llm_spec"
            class="fullscreen-chart inline-vertical"
          >
            <LLMDrivenInlineChart
              :key="`llm-inline-full-${fullscreenResult?.id}-${showFullscreen}`"
              :backendData="fullscreenResult.backendData"
              :height="800"
              :title="fullscreenResult.title || 'Inline Trend (LLM Spec)'"
            />
          </div>
          <!-- LLM spec가 없으면 기존 INLINETrendChart로 -->
          <div
            v-else-if="fullscreenResult?.type === 'inline_trend_initial' || fullscreenResult?.type === 'inline_trend_followup'"
            class="fullscreen-chart inline-vertical"
          >
            <INLINETrendChart
              :key="`inline-full-${fullscreenResult?.id}-${showFullscreen}`"
              :backendData="fullscreenResult.backendData"
              :height="800"
              :title="fullscreenResult.title || 'Inline Trend Analysis'"
            />
          </div>
          
          <!-- CPK 달성률 분석 (cpk_achieve_rate_initial) -->
          <div v-else-if="fullscreenResult?.type === 'cpk_achieve_rate_initial'" class="fullscreen-chart">
            <CPKAchieveRateChart
              :key="`cpk-achieve-full-${fullscreenResult?.id}-${showFullscreen}`"
              :backendData="fullscreenResult.backendData"
              :height="800"
              :title="fullscreenResult.title || 'CPK 달성률 분석'"
            />
          </div>
          
          <!-- Low CPK Trend Module -->
          <div v-else-if="fullscreenResult?.type === 'low_cpk_chart_trend' || fullscreenResult?.type === 'low_cpk_analysis_trend'" class="fullscreen-chart inline-vertical">
            <LowCPKTrendChart
              :key="`low-cpk-full-${fullscreenResult?.id}-${showFullscreen}`"
              :backendData="fullscreenResult.backendData"
              :height="800"
            />
          </div>
          
          <!-- PCM To Trend Chart (sameness_to_trend, commonality_to_trend) -->
          <div v-else-if="fullscreenResult?.type === 'sameness_to_trend' || fullscreenResult?.type === 'commonality_to_trend'" class="fullscreen-chart">
            <PCMToTrend 
              :data="fullscreenResult.data"
              :height="800"
              :resultType="fullscreenResult.type"
              :graphName="fullscreenResult.graphName"
              :maxLabels="50"
              :dataSampling="false"
            />
          </div>
          
          <!-- Commonality Table -->
          <div v-else-if="fullscreenResult?.type === 'commonality_module'" class="fullscreen-chart">
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
        
        <div v-else-if="isPlotlyGraphType(fullscreenResult?.type)" class="fullscreen-chart fullscreen-plotly-vertical">
          <!-- Multiple Graphs in Fullscreen -->
          <div v-if="fullscreenResult?.graphSpecs && fullscreenResult.graphSpecs.length > 0" class="fullscreen-multiple-graphs">
            <div 
              v-for="(graphSpec, graphIndex) in fullscreenResult.graphSpecs" 
              :key="`full-${fullscreenResult.id}-graph-${graphIndex}`"
              class="fullscreen-single-graph"
            >
              <PlotlyGraph
                :graph-spec="graphSpec"
                :title="graphSpec?.layout?.title?.text || graphSpec?.layout?.title || `Graph ${graphIndex + 1}`"
                :file-name="fullscreenResult.fileName"
                :success-message="''"
                :height="800"
              />
            </div>
          </div>
          
          <!-- Single Graph in Fullscreen -->
          <div v-else class="fullscreen-plotly-graph">
            <PlotlyGraph
              :graph-spec="fullscreenResult.graphSpec"
              :title="fullscreenResult.title"
              :file-name="fullscreenResult.fileName"
              :success-message="''"
              :height="800"
            />
          </div>
          
          <div
            v-if="fullscreenResult?.realDataSets && fullscreenResult.realDataSets.length"
            class="plotly-real-data fullscreen"
          >
            <details
              v-for="(dataset, datasetIndex) in fullscreenResult.realDataSets"
              :key="`full-${fullscreenResult.id}-dataset-${datasetIndex}`"
              class="plotly-data-set"
              open
            >
              <summary>
                📄 데이터셋
                <span v-if="dataset && dataset.length">({{ dataset.length }}행)</span>
              </summary>
              <DynamicTable
                :data="dataset"
                :title="`데이터셋`"
              />
            </details>
          </div>
        </div>
        
        <div v-else-if="fullscreenResult?.type === 'general_text'" class="fullscreen-chart general-text-section">
          <div class="general-text-card">
            <h5>📝 분석 결과</h5>
            <p v-if="fullscreenResult?.successMessage">{{ fullscreenResult.successMessage }}</p>
            <p v-else-if="fullscreenResult?.summary">{{ fullscreenResult.summary }}</p>
            <p v-else-if="fullscreenResult?.textContent">{{ fullscreenResult.textContent }}</p>
            <p v-else class="empty-text">표시할 메시지가 없습니다.</p>
          </div>
        </div>
        
        <div v-else-if="fullscreenResult?.type === 'table'" class="fullscreen-chart table-result-section">
          <div
            v-if="fullscreenResult?.realDataSets && fullscreenResult.realDataSets.length"
            class="table-datasets"
          >
            <DynamicTable
              v-for="(dataset, datasetIndex) in fullscreenResult.realDataSets"
              :key="`full-${fullscreenResult.id}-table-${datasetIndex}`"
              :data="dataset"
              :title="`데이터 테이블`"
            />
          </div>
          <div v-else class="empty-table">
            표시할 데이터가 없습니다.
          </div>
        </div>
          
          <!-- Metadata Only (전체화면) -->
          <div v-else-if="fullscreenResult?.type === 'metadata_only'" class="fullscreen-chart">
            <div class="metadata-info-fullscreen">
              <h3> Analysis Metadata</h3>
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
          
          <!-- Two Dynamic Tables for fullscreen (lot_hold_pe_confirm_module) -->
          <div v-else-if="fullscreenResult?.type === 'lot_hold_pe_confirm_module'" class="fullscreen-chart">
            <TwoDynamicTables 
              :data="[fullscreenResult.realData || fullscreenResult.data]"
              :title="fullscreenResult.title || 'Lot Hold & PE Module Analysis'"
            />
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
  </div>
</template>

<script>
import { defineComponent, ref, computed, nextTick, onMounted, watch } from 'vue'
import PCMTrendChart from './components/PCMTrendChart.vue'
import PCMTrendPointChart from './components/PCMTrendPointChart.vue'
import PCMToTrend from './components/PCMToTrend.vue'
import DynamicTable from './components/DynamicTable.vue'
import PlotlyGraph from './components/PlotlyGraph.vue'
import TwoDynamicTables from './components/TwoDynamicTables.vue'
import ChatRoomList from './components/ChatRoomList.vue'
import RAGAnswerList from './components/RAGAnswerList.vue'
import INLINETrendChart from './components/INLINETrendChart.vue'
import CPKAchieveRateChart from './components/CPKAchieveRateChart.vue'
import LLMDrivenInlineChart from './components/LLMDrivenInlineChart.vue'
import LowCPKTrendChart from './components/LowCPKTrendChart.vue'

import {
  streamChatAPI,
  editMessageAPI,
  generatePCMDataWithRealData,
  generateCommonalityDataWithRealData,
  createChatRoom,
  getChatRooms,
  getChatRoomHistory,
  deleteChatRoom as deleteChatRoomAPI,
  fetchFileContent,
  analyzeExcelFileStream
} from './services/api.js'
import { API_BASE_URL } from './services/api.js'
import { isErrorResponse, extractErrorMessage } from './config/dataTypes.js'
import {
  getValueByPath,
  coerceNumber,
  mergeDeep,
  aggregatePoints,
  splitSeriesPoints,
  applyDeclarativeTransforms
} from './utils/plotlyHelpers.js'
import {
  buildBarFigure,
  buildLineFigure,
  buildBoxFigure
} from './utils/plotlyGraphBuilders.js'
import { 
  isAuthenticated, 
  getUserFromToken, 
  handleSSOLogin, 
  getTokenFromUrl, 
  logout as authLogout 
} from './utils/auth.js'
import {
  adjustTextareaHeight as adjustTextareaHeightHelper,
  scrollToBottom as scrollToBottomHelper,
  formatTime as formatTimeHelper,
  formatFileSize as formatFileSizeHelper,
  openFullscreen as openFullscreenHelper,
  closeFullscreen as closeFullscreenHelper,
  startResize as startResizeHelper
} from './utils/uiHelpers.js'
import {
  loadChatRooms as loadChatRoomsHelper,
  refreshChatRoomHistory as refreshChatRoomHistoryHelper,
  selectChatRoom as selectChatRoomHelper,
  createNewChatRoom as createNewChatRoomHelper,
  deleteChatRoom as deleteChatRoomHelper,
  updateChatRoomInfo as updateChatRoomInfoHelper,
  updateChatRoomName as updateChatRoomNameHelper,
  handleUpdateRoomName as handleUpdateRoomNameHelper
} from './utils/chatRoomManager.js'

export default defineComponent({
  name: 'App',
  components: {
    PCMTrendChart,
    PCMTrendPointChart,
    PCMToTrend,
    DynamicTable,
    PlotlyGraph,
    TwoDynamicTables,
    ChatRoomList,
    RAGAnswerList,
    INLINETrendChart,
    CPKAchieveRateChart,
    LLMDrivenInlineChart,
    LowCPKTrendChart
  },
  setup() {
    // 인증 관련 상태
    const currentUser = ref(null)
    const isUserAuthenticated = ref(false)
    
    const selectedDataType = ref('pcm') // 기본값은 PCM
    const isLoading = ref(false)
    const messagesContainer = ref(null)
    const messageInput = ref(null)
    const fileInput = ref(null)
    const selectedFile = ref(null) // 선택된 파일 저장
    const isDataLoading = ref(false)
    
    const chartHeight = ref(600)
    

    
    // 채팅방별 UI 상태 관리
    const chatInputs = ref({}) // 각 채팅방별 입력 메시지
    const chatErrors = ref({}) // 각 채팅방별 에러 상태
    
    // 현재 활성 채팅방의 입력 메시지 computed
    const currentMessage = computed({
      get: () => chatInputs.value[activeChatId.value] || '',
      set: (value) => {
        if (activeChatId.value) {
          chatInputs.value[activeChatId.value] = value
        }
      }
    })
    
    // 현재 활성 채팅방의 에러 상태 computed
    const showError = computed(() => {
      return chatErrors.value[activeChatId.value]?.show || false
    })
    
    const currentError = computed(() => {
      return chatErrors.value[activeChatId.value]?.message || ''
    })
const showOriginalTime = ref(false) // 원본 시간 표시 토글
    const isAnalysisCollapsed = ref(false) // Analysis Results 섹션 접기/펼치기 토글 (초기값: 펼쳐진 상태)
    
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
          text: '안녕하세요! 데이터 분석 채팅 어시스턴트입니다.\n\n 사용 방법:\n1. 데이터 타입을 선택하세요 (PCM, INLINE, RAG)\n2. 메시지를 입력하고 전송하세요\n3. Enter 키를 누르거나 전송 버튼을 클릭하세요\n\n 지원하는 데이터 타입:\n• PCM (Process Control Monitor) - 트렌드 분석 및 공통성 분석\n• INLINE (Inline Analysis) - 인라인 분석\n• RAG (Retrieval-Augmented Generation) - AI 기반 분석',
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
        const initialMessage = `현재 제공 가능한 기능들은 아래와 같습니다.\n
          PCM (Process Control Monitor)
          ① PCM Trend, Commonality, Sameness 분석
          ② PCM Trend는 Tech/Device/Para 기준 Box Plot, Site Trend 가능
          ③ Good, Bad Lot의 Commonality, Bad Lot의 Sameness 결과 및 특정 공정의 Trend
          ④ PE Confirm Sheet이력 및 PCM Hold 이력 찾기
          
          Inline (Inline Analysis)
          ① Inline Route/Oper Para Trend는 EQ, Device, Recipe 등 기준으로 Trend Display
          ② PE Confirm Sheet이력 찾기
          
          불량 이력 검색
          ① DB 서버에 Eng'r가 저장한 과거 불량 이력(메일, PPT 파일)을 검색
          ② 검색된 내용에 대한 요약
          ③ 검색된 내용에 파일 다운로드
          → Eng'r가 저장하지 않은 불량 이력은 검색되지 않음`

        return [
          {
            type: 'system',
            text: initialMessage,
            timestamp: new Date(),
            isNewChatroom: true
          },
          ...roomMessages
        ]
      }
      
      return roomMessages
    })
    
    const results = computed(() => {
      const activeResults = chatResults.value[activeChatId.value] || []
      console.log(`📈 Computing results for room ${activeChatId.value}:`, activeResults.length, 'results')
      return activeResults
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

    // formatTime을 헬퍼 함수로 위임
    const formatTime = (timestamp) => formatTimeHelper(timestamp)

      // Deep merge helper: target values take precedence over source
      const stripCodeFences = (value) => {
        if (typeof value !== 'string') return value
        const trimmed = value.trim()
        if (!trimmed) return trimmed
        const fenceMatch = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i)
        return fenceMatch ? fenceMatch[1].trim() : trimmed
      }

      const parseJsonLoose = (value) => {
        if (value === null || value === undefined) return null
        if (typeof value === 'object') return value
        if (typeof value !== 'string') return null
        const cleaned = stripCodeFences(value)
        if (!cleaned) return null
        try {
          const parsed = JSON.parse(cleaned)
          if (typeof parsed === 'string') {
            return parseJsonLoose(parsed)
          }
          return parsed
        } catch (error) {
          console.warn('Failed to parse JSON string:', error, cleaned)
          return null
        }
      }

      const normalizeGraphSpec = (spec) => {
        if (!spec && spec !== 0) return null
        const parsed = parseJsonLoose(spec) ?? spec
        if (!parsed) return null

        if (Array.isArray(parsed)) {
          return {
            data: parsed,
            layout: {},
            config: {}
          }
        }

        let figure = parsed
        if (parsed.figure && typeof parsed.figure === 'object') {
          figure = parsed.figure
        }

        const data = Array.isArray(figure.data)
          ? figure.data
          : Array.isArray(figure.traces)
            ? figure.traces
            : []

        const layout = figure.layout && typeof figure.layout === 'object'
          ? { ...figure.layout }
          : {}

        const config = figure.config && typeof figure.config === 'object'
          ? { ...figure.config }
          : {}

        const frames = Array.isArray(figure.frames) ? [...figure.frames] : []

        return {
          data,
          layout,
          config,
          frames,
          raw: figure
        }
      }

      const isDeclarativeGraphSpec = (spec) => {
        return (
          spec &&
          typeof spec === 'object' &&
          (spec.encodings || spec.schema_version || spec.dataset_index !== undefined || spec.chart_type)
        )
      }

      const buildPlotlyFigureFromSchema = (rawSpec, realDataSets = []) => {
        console.log('🔧 buildPlotlyFigureFromSchema called:', { rawSpec, realDataSets })
        if (!rawSpec || typeof rawSpec !== 'object') {
          console.warn('⚠️ buildPlotlyFigureFromSchema: invalid rawSpec')
          return null
        }

        const datasetIndex = Number.isInteger(rawSpec.dataset_index) ? rawSpec.dataset_index : 0
        const dataset = realDataSets[datasetIndex] || realDataSets[0] || []
        console.log('🔧 dataset:', dataset?.length, 'rows')
        if (!Array.isArray(dataset) || !dataset.length) {
          console.warn('⚠️ buildPlotlyFigureFromSchema: no dataset')
          return null
        }

        const rows = applyDeclarativeTransforms(dataset, rawSpec.transforms)
        const chartType = (rawSpec.chart_type || rawSpec.type || 'bar').toLowerCase()
        const encodings = rawSpec.encodings || {}
        console.log('🔧 chartType:', chartType, 'encodings:', encodings)

        if (chartType.includes('box')) {
          console.log('✅ Building box plot')
          return buildBoxFigure(rows, encodings, rawSpec)
        }
        if (chartType.includes('line')) {
          console.log('✅ Building line graph')
          return buildLineFigure(rows, encodings, rawSpec, 'line')
        }
        if (chartType.includes('scatter')) {
          console.log('✅ Building scatter plot')
          return buildLineFigure(rows, encodings, rawSpec, 'scatter')
        }
        console.log('✅ Building bar graph (default)')
        return buildBarFigure(rows, encodings, rawSpec)
      }

      const buildGraphSpec = (rawSpec, realDataSets) => {
        console.log('🔍 buildGraphSpec called with:', { rawSpec, realDataSets })
        if (!rawSpec && rawSpec !== 0) {
          console.warn('⚠️ buildGraphSpec: rawSpec is null/undefined')
          return null
        }
        const parsed = parseJsonLoose(rawSpec) ?? rawSpec
        console.log('🔍 buildGraphSpec parsed:', parsed)
        if (!parsed) {
          console.warn('⚠️ buildGraphSpec: parsed is null')
          return null
        }

        if (isDeclarativeGraphSpec(parsed)) {
          console.log('✅ buildGraphSpec: Using declarative spec')
          const figure = buildPlotlyFigureFromSchema(parsed, realDataSets)
          console.log('🔍 buildGraphSpec figure:', figure)
          if (figure) {
            return normalizeGraphSpec(figure)
          }
        }

        console.log('⚠️ buildGraphSpec: Using legacy spec')
        return normalizeGraphSpec(parsed)
      }

      const normalizeRealDataSets = (payload) => {
        console.log('[normalizeRealDataSets] Input payload:', payload)
        console.log('[normalizeRealDataSets] Payload type:', typeof payload)
        console.log('[normalizeRealDataSets] Payload is array:', Array.isArray(payload))
        
        if (payload === null || payload === undefined) {
          console.warn('[normalizeRealDataSets] Payload is null or undefined')
          return []
        }
        
        const items = Array.isArray(payload) ? payload : [payload]
        console.log('[normalizeRealDataSets] Items array length:', items.length)
        
        const datasets = []

        items.forEach((entry, index) => {
          console.log(`[normalizeRealDataSets] Processing entry ${index}:`, entry)
          
          if (entry === null || entry === undefined) {
            console.warn(`[normalizeRealDataSets] Entry ${index} is null or undefined`)
            return
          }
          
          let parsed = entry

          if (typeof parsed === 'string') {
            console.log(`[normalizeRealDataSets] Entry ${index} is string, parsing...`)
            parsed = parseJsonLoose(parsed) ?? parsed
          }

          if (typeof parsed === 'string') {
            console.log(`[normalizeRealDataSets] Entry ${index} still string, parsing again...`)
            parsed = parseJsonLoose(parsed)
          }

          if (Array.isArray(parsed)) {
            console.log(`[normalizeRealDataSets] Entry ${index} is array, length:`, parsed.length)
            console.log(`[normalizeRealDataSets] Entry ${index} first 3 rows:`, parsed.slice(0, 3))
            datasets.push(parsed)
            return
          }

          if (parsed && typeof parsed === 'object') {
            if (Array.isArray(parsed.records)) {
              console.log(`[normalizeRealDataSets] Entry ${index} has records array, length:`, parsed.records.length)
              datasets.push(parsed.records)
              return
            }
            if (Array.isArray(parsed.data)) {
              console.log(`[normalizeRealDataSets] Entry ${index} has data array, length:`, parsed.data.length)
              datasets.push(parsed.data)
              return
            }
            console.log(`[normalizeRealDataSets] Entry ${index} is object, wrapping in array`)
            datasets.push([parsed])
          }
        })

        console.log('[normalizeRealDataSets] Result datasets count:', datasets.length)
        datasets.forEach((ds, i) => {
          console.log(`[normalizeRealDataSets] Dataset ${i} length:`, ds?.length)
          console.log(`[normalizeRealDataSets] Dataset ${i} first row:`, ds?.[0])
        })

        return datasets
      }

      const plotlyGraphTypes = ['bar_graph', 'line_graph', 'box_plot', 'scatter_plot']

      const plotlyTitleMap = {
        bar_graph: 'Bar Graph',
        line_graph: 'Line Graph',
        box_plot: 'Box Plot',
        scatter_plot: 'Scatter Plot',
        general_text: 'Analysis Summary',
        table: 'Table Data'
      }

      const isPlotlyGraphType = (type) => plotlyGraphTypes.includes(type)

    // 응답 데이터로부터 결과 객체 생성하는 함수
    const createResultFromResponseData = (responseData, userMessage, chatId) => {
      try {
        console.log(' Creating result from response data:', responseData)
        console.log(' Response data keys:', responseData ? Object.keys(responseData) : 'no data')
        
        if (!responseData) {
          console.warn('⚠️ No response data')
          return null
        }

        // real_data가 있으면 실제 데이터로 결과 생성, 없으면 메타데이터만 저장
        const realData = responseData.real_data || []
        console.log(' Real data length:', realData.length)
        console.log(' Response result type:', responseData.result)
        console.log(' Real data 첫 번째 샘플:', realData[0])
        if (realData.length > 0) {
          console.log(' Real data에 PARA 컬럼 있음?', realData[0]?.PARA !== undefined)
        }
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
        } else if (responseData.result === 'lot_hold_pe_confirm_module') {
          // Two Dynamic Tables 데이터 처리
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'lot_hold_pe_confirm_module',
            title: 'LOT HOLD PE MODULE Analysis',
            data: null,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: realData,
            resultType: responseData.result,
            userMessage: userMessage
          }
        } else if (responseData.result === 'cpk_achieve_rate_initial') {
          // CPK 달성률 분석 데이터 처리
          const realData = responseData.real_data
          
          console.log('🔍 CPK real_data type:', typeof realData, realData)
          
          // real_data가 없거나 table_data, graph_data가 없으면 analysis report 탭을 생성하지 않음
          if (!realData || 
              (typeof realData === 'object' && (!realData.table_data || !realData.graph_data)) ||
              (Array.isArray(realData) && realData.length === 0)) {
            console.log('❌ CPK data validation failed:', realData)
            return null
          }
          
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'cpk_achieve_rate_initial',
            title: 'CPK 달성률 분석',
            data: null,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            backendData: {
              result: responseData.result,
              real_data: realData,
              success_message: responseData.success_message || 'CPK 달성률 분석이 성공적으로 생성되었습니다.'
            },
            realData: null, // CPK 달성률은 backendData를 사용하므로 realData는 null
            userMessage: userMessage
          }
        } else if (responseData.result === 'low_cpk_chart_trend' || responseData.result === 'low_cpk_analysis_trend') {
          // Low CPK Trend Module 데이터 처리
          const realData = responseData.real_data
          
          // real_data가 없거나 배열이 아니면 analysis report 탭을 생성하지 않음
          if (!realData || !Array.isArray(realData) || realData.length === 0) {
            console.log('❌ Low CPK Trend data validation failed:', realData)
            return null
          }
          
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: responseData.result,
            title: 'Low CPK Trend Analysis',
            data: null,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            backendData: {
              result: responseData.result,
              real_data: realData,
              success_message: responseData.success_message || 'Low CPK Trend 분석이 성공적으로 생성되었습니다.'
            },
            realData: null, // Low CPK Trend는 backendData를 사용하므로 realData는 null
            userMessage: userMessage
          }
        } else if (responseData.result === 'inline_trend_initial') {
          // INLINE Trend Initial 데이터 처리
          const realData = responseData.real_data
          
          // real_data가 없으면 analysis report 탭을 생성하지 않음
          if (!realData || (Array.isArray(realData) && realData.length === 0)) {
            return null
          }
          
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'inline_trend_initial',
            title: 'INLINE Trend Initial Analysis',
            data: null,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: null, // INLINE Trend는 backendData를 사용하므로 realData는 null
            resultType: responseData.result,
            userMessage: userMessage,
            backendData: {
              result: responseData.result,
              criteria: responseData.criteria,
              real_data: responseData.real_data,
              success_message: responseData.success_message,
              llm_spec: responseData.llm_spec       // 👈 추가
            }
          }
        } else if (responseData.result === 'inline_trend_followup') {
          // INLINE Trend Followup 데이터 처리
          const realData = responseData.real_data
          
          // real_data가 없으면 analysis report 탭을 생성하지 않음
          if (!realData || (Array.isArray(realData) && realData.length === 0)) {
            return null
          }
          
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'inline_trend_followup',
            title: 'INLINE Trend Followup Analysis',
            data: null,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: null, // INLINE Trend는 backendData를 사용하므로 realData는 null
            resultType: responseData.result,
            userMessage: userMessage,
            backendData: {
              result: responseData.result,
              criteria: responseData.criteria,
              real_data: responseData.real_data,
              success_message: responseData.success_message,
              llm_spec: responseData.llm_spec       // 👈 추가
            }
          }
        } else if (responseData.analysis_type === 'excel_analysis' || responseData.analysis_type === 'excel_chart' || responseData.analysis_type === 'excel_summary') {
          // 엑셀 분석 결과 처리
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: responseData.analysis_type,
            title: `Excel Analysis - ${responseData.file_name || 'File'}`,
            data: responseData.data || {},
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            realData: responseData.data?.raw_data || responseData.data?.chart_data || [],
            resultType: responseData.analysis_type,
            userMessage: userMessage,
            summary: responseData.summary,
            chartConfig: responseData.chart_config,
            fileName: responseData.file_name,
            metadata: responseData,
            successMessage: responseData.success_message || ''
          }
        } else if (
          plotlyGraphTypes.includes(responseData.analysis_type) ||
          responseData.analysis_type === 'general_text' ||
          responseData.analysis_type === 'table'
        ) {
          console.log('📊 Processing Plotly/Table/Text type:', responseData.analysis_type)
          console.log('📊 responseData.graph_spec:', responseData.graph_spec)
          console.log('📊 responseData.real_data:', responseData.real_data)
          console.log('📊 responseData.real_data type:', typeof responseData.real_data)
          console.log('📊 responseData.real_data is array:', Array.isArray(responseData.real_data))
          if (Array.isArray(responseData.real_data)) {
            console.log('📊 responseData.real_data length:', responseData.real_data.length)
            console.log('📊 responseData.real_data first 3 rows:', responseData.real_data.slice(0, 3))
          }
          
          const analysisType = responseData.analysis_type
          const realDataSets = normalizeRealDataSets(responseData.real_data)
          console.log('📊 realDataSets after normalize:', realDataSets)
          console.log('📊 realDataSets length:', realDataSets?.length)
          console.log('📊 realDataSets[0] length:', realDataSets?.[0]?.length)
          console.log('📊 realDataSets[0] first 3 rows:', realDataSets?.[0]?.slice(0, 3))
          
          const primaryRealData = realDataSets[0] || []
          const hasGraphSpec = plotlyGraphTypes.includes(analysisType)
          console.log('📊 hasGraphSpec:', hasGraphSpec, 'analysisType:', analysisType)
          
          // Process graph_spec (always array)
          let graphSpec = null
          let graphSpecs = null
          
          if (hasGraphSpec && responseData.graph_spec && Array.isArray(responseData.graph_spec)) {
            const specArray = responseData.graph_spec
            console.log('📊 Processing graph_spec array, length:', specArray.length)
            
            if (specArray.length === 0) {
              console.warn('⚠️ Empty graph_spec array')
            }
            // Case 1: Template (first item has split_by)
            else if (specArray[0]?.split_by && typeof specArray[0].split_by === 'string' && specArray[0].split_by.trim()) {
              console.log('📊 Detected template (split_by found):', specArray[0].split_by)
              const template = specArray[0]
              const splitBy = template.split_by
              
              if (primaryRealData.length > 0) {
                console.log(`📊 Expanding template by column: ${splitBy}`)
                
                // Extract unique values from split_by column
                const uniqueValues = [...new Set(primaryRealData.map(row => row[splitBy]))]
                  .filter(val => val !== null && val !== undefined)
                  .slice(0, 10) // Limit to 10 graphs max
                
                console.log(`📊 Found ${uniqueValues.length} unique values:`, uniqueValues)
                
                // Create spec for each unique value
                graphSpecs = uniqueValues.map(value => {
                  // Deep copy template
                  const spec = JSON.parse(JSON.stringify(template))
                  const splitByColumn = spec.split_by
                  delete spec.split_by // Remove split_by from spec
                  
                  // Replace {{SPLIT_VALUE}} placeholder
                  let specStr = JSON.stringify(spec)
                  specStr = specStr.replace(/\{\{SPLIT_VALUE\}\}/g, String(value))
                  const expandedSpec = JSON.parse(specStr)
                  
                  // Add filter transform for this split value
                  if (!expandedSpec.transforms) {
                    expandedSpec.transforms = []
                  }
                  // Add filter at the beginning to filter data by split value
                  expandedSpec.transforms.unshift({
                    type: 'filter',
                    field: splitByColumn,
                    op: '==',
                    value: value
                  })
                  
                  // Add title to layout showing the split value
                  if (!expandedSpec.layout) {
                    expandedSpec.layout = {}
                  }
                  if (!expandedSpec.layout.title) {
                    expandedSpec.layout.title = {
                      text: `${splitByColumn} = ${value}`,
                      font: { size: 16 }
                    }
                  }
                  
                  console.log(`📊 Creating graph for ${splitByColumn}=${value}`)
                  
                  // Build graph spec
                  return buildGraphSpec(expandedSpec, realDataSets)
                }).filter(spec => spec !== null)
                
                console.log('📊 graphSpecs after template expansion:', graphSpecs.length, 'specs')
              } else {
                console.warn('⚠️ Template found but no data to expand')
              }
            }
            // Case 2: Single spec
            else if (specArray.length === 1) {
              console.log('📊 Processing single spec')
              graphSpec = buildGraphSpec(specArray[0], realDataSets)
              console.log('📊 graphSpec after build:', graphSpec)
              if (graphSpec?.data) {
                console.log('📊 graphSpec.data traces:', graphSpec.data.length)
              }
            }
            // Case 3: Multiple specs
            else {
              console.log('📊 Processing multiple specs:', specArray.length)
              graphSpecs = specArray.map((spec, index) => {
                const built = buildGraphSpec(spec, realDataSets)
                console.log(`📊 Built graphSpec ${index}:`, built)
                return built
              }).filter(spec => spec !== null)
              
              console.log('📊 graphSpecs after build:', graphSpecs.length, 'specs')
            }
          }
          
          const successMessage = responseData.success_message || responseData.summary || ''
          const baseTitle = plotlyTitleMap[analysisType] || 'Excel Analysis'
          const fileSuffix = responseData.file_name ? ` - ${responseData.file_name}` : ''

          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: analysisType,
            title: `${baseTitle}${fileSuffix}`,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql,
            fileName: responseData.file_name || null,
            successMessage,
            summary: responseData.summary,
            graphSpec,
            graphSpecs, // New field for multiple graphs
            realData: primaryRealData,
            realDataSets,
            metadata: responseData,
            resultType: analysisType
          }
          console.log('📊 Created result with graphSpec:', result.graphSpec)
          console.log('📊 Created result with graphSpecs:', result.graphSpecs?.length || 0, 'specs')

          if (analysisType === 'table') {
            result.data = primaryRealData
          }

          if (analysisType === 'general_text') {
            result.textContent = successMessage || responseData.text || ''
          }
        } else if (responseData.result_type || responseData.result) {
          // real_data가 없어도 메타데이터만으로 결과 생성
          const resultType = responseData.result_type || responseData.result
          result = {
            id: `history_${chatId}_${Date.now()}`,
            type: 'metadata_only',
            title: `${resultType?.toUpperCase() || 'Data'} Analysis`,
            isActive: false,
            timestamp: new Date(),
            chatId: chatId,
            sql: responseData.sql || responseData.SQL,
            realData: realData,
            resultType: resultType,
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

    // scrollToBottom을 헬퍼 함수로 위임
    const scrollToBottom = async () => {
      await scrollToBottomHelper(messagesContainer.value)
    }

    const addMessage = (type, text, isEditable = false, originalMessage = null, messageType = 'text', files = null) => {
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
        isError: type === 'bot' && text.includes('❌'),
        messageType, // 'text', 'file_list' 등
        files, // 파일 목록 데이터
        // 수정 관련 속성들 추가
        isEditing: false,
        editText: ''
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

    // 타이핑 애니메이션과 함께 bot 메시지 추가
    const addBotMessageWithTyping = (text) => {
      if (!activeChatId.value) return
      
      // 빈 메시지로 시작
      addMessage('bot', '')
      const messages = chatMessages.value[activeChatId.value]
      const messageIndex = messages.length - 1
      
      // 타이핑 애니메이션 시작
      typeText(messageIndex, text)
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
      
      // 현재 채팅방의 에러 상태 설정
      if (!chatErrors.value[activeChatId.value]) {
        chatErrors.value[activeChatId.value] = {}
      }
      chatErrors.value[activeChatId.value].message = errorText
      chatErrors.value[activeChatId.value].show = true
      
      // 원본 메시지를 현재 채팅방의 입력창에 자동 입력
      chatInputs.value[activeChatId.value] = originalMessageText
      
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
      
      // 현재 채팅방의 에러 상태 초기화
      if (chatErrors.value[activeChatId.value]) {
        chatErrors.value[activeChatId.value].message = ''
        chatErrors.value[activeChatId.value].show = false
      }
    }



    // 파일 다운로드 함수
    const downloadFile = async (fileName, filePath) => {
      try {
        console.log(' Downloading file:', fileName, filePath)
        
        // 파일 내용 가져오기
        const fileContent = await fetchFileContent(filePath)
        
        // Blob 생성
        const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' })
        
        // 다운로드 링크 생성
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = fileName
        
        // 링크 클릭으로 다운로드 실행
        document.body.appendChild(link)
        link.click()
        
        // 정리
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        console.log('✅ File downloaded successfully:', fileName)
      } catch (error) {
        console.error('❌ Error downloading file:', error)
        // 에러 메시지를 채팅에 표시
        // 파일 다운로드 실패 - 백엔드에서 에러 메시지 처리
      }
    }

    // 리사이즈 기능을 헬퍼 함수로 위임
    const startResize = (event) => {
      const resizeState = {
        isResizing: true,
        currentResizeBar: event.target,
        startX: event.clientX,
        startWidths: {
          sidebar: sidebar.value?.offsetWidth || 280,
          chatSection: chatSection.value?.offsetWidth || 400,
          resultsSidebar: resultsSidebar.value?.offsetWidth || 500
        }
      }
      
      const refs = {
        sidebar: sidebar.value,
        chatSection: chatSection.value,
        resultsSidebar: resultsSidebar.value,
        resizeBar1: resizeBar1.value,
        resizeBar2: resizeBar2.value
      }
      
      // 헬퍼 함수 호출 및 cleanup 함수 저장
      startResizeHelper(event, resizeState, refs)
      
      // 상태 업데이트
      isResizing.value = resizeState.isResizing
      currentResizeBar.value = resizeState.currentResizeBar
      startX.value = resizeState.startX
      startWidths.value = resizeState.startWidths
    }

    // 전체화면 모달 제어 함수들을 헬퍼 함수로 위임
    const openFullscreen = (result) => {
      const fullscreenState = {
        fullscreenResult: result,
        showFullscreen: true
      }
      openFullscreenHelper(result, fullscreenState)
      fullscreenResult.value = fullscreenState.fullscreenResult
      showFullscreen.value = fullscreenState.showFullscreen
    }

    const closeFullscreen = () => {
      const fullscreenState = {
        fullscreenResult: fullscreenResult.value,
        showFullscreen: showFullscreen.value
      }
      closeFullscreenHelper(fullscreenState)
      fullscreenResult.value = fullscreenState.fullscreenResult
      showFullscreen.value = fullscreenState.showFullscreen
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
        
        // 데이터 로드 성공 - 백엔드에서 메시지 처리
      } catch (error) {
        console.error('Failed to load PCM data:', error)
        // 데이터 로드 실패 - 백엔드에서 에러 메시지 처리
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
        
        // 데이터 새로고침 성공 - 백엔드에서 메시지 처리
      } catch (error) {
        console.error('Failed to refresh data:', error)
        // 데이터 새로고침 실패 - 백엔드에서 에러 메시지 처리
      } finally {
        isDataLoading.value = false
      }
    }

    // 현재 업데이트 중인 bot 메시지 인덱스 추적
    const currentBotMessageIndex = ref(-1)
    
    // 타이핑 애니메이션 관련 변수
    const isTyping = ref(false)
    const typingTimeout = ref(null)
    const currentTypingText = ref('')

    // 타이핑 애니메이션 함수
    const typeText = (messageIndex, targetText, speed = 50) => {
      return new Promise((resolve) => {
        const messages = chatMessages.value[activeChatId.value]
        if (!messages || !messages[messageIndex] || messages[messageIndex].type !== 'bot') {
          resolve()
          return
        }

        // 이전 타이핑 중단
        if (typingTimeout.value) {
          clearTimeout(typingTimeout.value)
        }

        isTyping.value = true
        currentTypingText.value = ''
        let currentIndex = 0

        const typeNextChar = () => {
          if (currentIndex < targetText.length) {
            currentTypingText.value += targetText[currentIndex]
            messages[messageIndex].text = currentTypingText.value + '|'  // 타이핑 커서 추가
            messages[messageIndex].timestamp = new Date()
            currentIndex++
            
            typingTimeout.value = setTimeout(typeNextChar, speed)
          } else {
            // 타이핑 완료 시 커서 제거
            messages[messageIndex].text = targetText
            isTyping.value = false
            currentTypingText.value = ''
            resolve()
          }
        }

        typeNextChar()
      })
    }

    // Bot 메시지 업데이트 함수 (타이핑 애니메이션 포함)
    const updateBotMessage = async (messageIndex, newText) => {
      const messages = chatMessages.value[activeChatId.value]
      if (messages && messages[messageIndex] && messages[messageIndex].type === 'bot') {
        // 이전 타이핑 중단
        if (typingTimeout.value) {
          clearTimeout(typingTimeout.value)
        }
        
        // 타이핑 애니메이션으로 텍스트 업데이트
        await typeText(messageIndex, newText)
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
        // 초기화 - bot 메시지 인덱스 리셋
        currentBotMessageIndex.value = -1
        
        // DCC도 기존 chat API를 사용
        await streamChatAPI(selectedDataType.value, message, activeChatId.value, (data) => {
          // 스트리밍 데이터 처리
          console.log(' Received streaming data:', data)
          
          if (data.progress_message) {
            // 진행 상황 메시지 처리 - 같은 메시지 업데이트
            if (currentBotMessageIndex.value === -1) {
              // 첫 번째 진행 메시지 - progress_message로 직접 추가
              addMessage('bot', data.progress_message)
              const messages = chatMessages.value[activeChatId.value]
              currentBotMessageIndex.value = messages.length - 1
            } else {
              // 기존 메시지 업데이트
              updateBotMessage(currentBotMessageIndex.value, data.progress_message)
            }
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
            
            // 백엔드에서 전송한 성공 메시지가 있으면 표시
            if (data.response.success_message) {
              if (currentBotMessageIndex.value === -1) {
                // 첫 번째 메시지인 경우 success_message로 직접 추가
                addMessage('bot', data.response.success_message)
                const messages = chatMessages.value[activeChatId.value]
                currentBotMessageIndex.value = messages.length - 1
              } else {
                // 기존 메시지 업데이트
                updateBotMessage(currentBotMessageIndex.value, data.response.success_message)
              }
            }
            
            // 실제 응답 데이터 처리
            currentChatResponse.value = data

            console.log('🔍 Processing response:', data.response)
            console.log('🔍 Response result:', data.response.result)
            console.log('🔍 Response result_type:', data.response.result_type)
            console.log('🔍 Real data exists:', !!data.response.real_data)
            console.log('🔍 Real data type:', typeof data.response.real_data)
            console.log('🔍 Real data length:', data.response.real_data?.length)
            
            // Debug: Check all response fields
            console.log('🚨 ALL RESPONSE FIELDS:', Object.keys(data.response || {}))
            console.log('🚨 CHECKING lot_hold_pe_confirm_module:', data.response.result === 'lot_hold_pe_confirm_module')
            
            if (data.response.real_data && data.response.real_data.length > 0) {
              console.log('🔍 Real data sample:', data.response.real_data.slice(0, 2))
            }
            
            if (data.response.result === 'cpk_achieve_rate_initial') {
              // CPK 달성률 분석 데이터 처리 - createResultFromResponseData 사용
              const realData = data.response.real_data
              
              console.log('🔍 Streaming CPK real_data type:', typeof realData, realData)
              
              // real_data가 없거나 table_data, graph_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || 
                  (typeof realData === 'object' && (!realData.table_data || !realData.graph_data)) ||
                  (Array.isArray(realData) && realData.length === 0)) {
                console.log('❌ Streaming CPK data validation failed:', realData)
                return
              }
              
              const result = createResultFromResponseData(data.response, message, data.chat_id)
              if (result) {
                result.isActive = true
                const currentResults = chatResults.value[activeChatId.value] || []
                currentResults.push(result)
                chatResults.value[activeChatId.value] = currentResults
                console.log('✅ CPK 달성률 분석 결과 추가됨:', result)
              }
            } else if (data.response.result === 'low_cpk_chart_trend' || data.response.result === 'low_cpk_analysis_trend') {
              // Low CPK Trend Module 데이터 처리
              const realData = data.response.real_data
              
              console.log('🔍 Streaming Low CPK Trend real_data type:', typeof realData, realData)
              
              // real_data가 없거나 배열이 아니면 analysis report 탭을 생성하지 않음
              if (!realData || !Array.isArray(realData) || realData.length === 0) {
                console.log('❌ Streaming Low CPK Trend data validation failed:', realData)
                return
              }
              
              const result = createResultFromResponseData(data.response, message, data.chat_id)
              if (result) {
                result.isActive = true
                const currentResults = chatResults.value[activeChatId.value] || []
                currentResults.push(result)
                chatResults.value[activeChatId.value] = currentResults
                console.log('✅ Low CPK Trend 분석 결과 추가됨:', result)
              }
            } else if (data.response.result === 'inline_trend_initial' || data.response.result === 'inline_trend_followup') {
              // INLINE Trend 데이터 처리 - createResultFromResponseData 사용
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              const result = createResultFromResponseData(data.response, message, data.chat_id)
              if (result) {
                result.isActive = true
                const currentResults = chatResults.value[activeChatId.value] || []
                currentResults.push(result)
                chatResults.value[activeChatId.value] = currentResults
              }
            } else if (data.response.result === 'lot_start') {
              // PCM 트렌드 데이터 처리
              const realData = data.response.real_data || []
              if (realData.length === 0) {
                // real_data가 없으면 analysis report 탭을 생성하지 않음
                return
              }
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
              
              // 성공 메시지와 요약은 백엔드에서 success_message로 전송됨
              
            } else if (data.response.result === 'lot_point') {
              // PCM 트렌드 포인트 데이터 처리
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
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
              // 성공 메시지와 요약은 백엔드에서 success_message로 전송됨
            } else if (data.response.result === 'commonality_module') {
              // PCM Commonality 데이터 처리
              let realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              console.log('🔍 Commonality real_data type:', typeof realData)
              console.log('🔍 Commonality real_data keys:', realData ? Object.keys(realData) : 'no data')
              
              // real_data가 객체인 경우 배열로 변환 (백엔드 수정 전 임시 처리)
              if (realData && typeof realData === 'object' && !Array.isArray(realData)) {
                console.log(' Converting object real_data to array for commonality')
                const combinedData = []
                Object.keys(realData).forEach(paraName => {
                  const paraData = realData[paraName]
                  if (Array.isArray(paraData)) {
                    paraData.forEach(row => {
                      combinedData.push({
                        ...row,
                        PARA: paraName
                      })
                    })
                  }
                })
                realData = combinedData
                console.log(' Converted data length:', realData.length)
              }
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'dynamic_table', // commonality에서 dynamic_table로 변경
                title: `PCM Commonality Analysis`,
                data: realData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql,
                realData: realData,
                resultType: data.response.result,
                userMessage: userMessage ? userMessage.text : 'Unknown message',
                // Commonality 정보 추가
                commonalityData: data.response.determined
              }
              
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
            } else if (data.response.result === 'sameness_to_trend') {
              // PCM Sameness to Trend 데이터 처리
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              // 데이터 개수 계산 (객체인 경우 PARA별 데이터 합계)
              let totalRecords = 0
              if (Array.isArray(realData)) {
                totalRecords = realData.length
              } else if (typeof realData === 'object' && realData !== null) {
                totalRecords = Object.values(realData).reduce((sum, paraData) => sum + (Array.isArray(paraData) ? paraData.length : 0), 0)
              }
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'sameness_to_trend',
                title: `PCM Sameness to Trend Analysis`,
                data: realData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql,
                realData: realData,
                resultType: data.response.result,
                graphName: data.response.graph_name || '', // 백엔드에서 제공하는 그래프 이름
                userMessage: userMessage ? userMessage.text : 'Unknown message'
              }
              
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
              
            } else if (data.response.result === 'commonality_to_trend') {
              // PCM Commonality to Trend 데이터 처리
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              // 데이터 개수 계산 (객체인 경우 PARA별 데이터 합계)
              let totalRecords = 0
              if (Array.isArray(realData)) {
                totalRecords = realData.length
              } else if (typeof realData === 'object' && realData !== null) {
                totalRecords = Object.values(realData).reduce((sum, paraData) => sum + (Array.isArray(paraData) ? paraData.length : 0), 0)
              }
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'commonality_to_trend',
                title: `PCM Commonality to Trend Analysis`,
                data: realData,
                isActive: true,
                timestamp: new Date(),
                chatId: data.chat_id,
                messageId: data.message_id,
                responseId: data.response_id,
                sql: data.response.sql,
                realData: realData,
                resultType: data.response.result,
                graphName: data.response.graph_name || '', // 백엔드에서 제공하는 그래프 이름
                userMessage: userMessage ? userMessage.text : 'Unknown message'
              }
              
              // 현재 채팅방의 결과들을 비활성화하고 새 결과 추가
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(r => r.isActive = false)
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
              
            } else if (data.response.result === 'sameness_module') {
              // PCM Sameness 데이터 처리 (DynamicTable.vue 사용)
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'dynamic_table',
                title: `PCM Sameness Analysis`,
                data: realData,
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
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
              
            } else if (data.response.result === 'commonality_module') {
              // PCM Commonality 데이터 처리 (DynamicTable.vue 사용)
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'dynamic_table',
                title: `PCM Commonality Analysis`,
                data: realData,
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
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
              
            } else if (data.response.result === 'lot_hold_pe_confirm_module') {
              // Two Dynamic Tables 데이터 처리
              const realData = data.response.real_data
              
              // real_data가 없으면 analysis report 탭을 생성하지 않음
              if (!realData || (Array.isArray(realData) && realData.length === 0)) {
                return
              }
              
              console.log('✅ TWO TABLES DETECTED! Processing:', data.response.result)
              console.log('🔍 Full response:', JSON.stringify(data.response, null, 2))
              console.log('🔍 Real data type:', typeof realData)
              console.log('🔍 Real data content:', realData)
              console.log('🔍 Real data first item:', realData?.[0])
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const newResult = {
                id: `two_tables_${activeChatId.value}_${Date.now()}`,
                type: 'lot_hold_pe_confirm_module',
                title: 'LOT HOLD PE MODULE Analysis',
                data: null,
                realData: realData,
                timestamp: new Date(),
                isActive: true,
                chatId: data.chat_id,
                resultType: data.response.result,
                sql: data.response.sql,
                userMessage: userMessage?.content || 'Unknown query'
              }
              
              // 기존 결과들 비활성화
              const currentResults = chatResults.value[activeChatId.value] || []
              currentResults.forEach(result => result.isActive = false)
              
              // 새 결과 추가
              currentResults.push(newResult)
              chatResults.value[activeChatId.value] = currentResults
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
              
            }
            // 그래프나 RAG가 아닌 모든 응답은 테이블로 처리 (real_data가 있을 때만)
            else if (data.response.real_data && data.response.real_data.length > 0) {
              const realData = data.response.real_data
              
              // 현재 유저 메시지 찾기
              const currentMessages = chatMessages.value[activeChatId.value] || []
              const userMessage = currentMessages.find(msg => msg.type === 'user' && msg.isEditable)
              
              const resultType = data.response.result_type || data.response.result
              const newResult = {
                id: data.response_id || `local_${Date.now()}`, // 백엔드에서 받는 response_id 사용
                type: 'dynamic_table',
                title: `${resultType?.toUpperCase()} Analysis`,
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
              
              // 성공 메시지는 백엔드에서 success_message로 전송됨
            }

            else if (data.response.result === 'rag') {
              // RAG 응답 처리 - 파일 목록을 구조화된 메시지로 처리
              if (data.response.files) {
                const files = data.response.files || []
                
                // 파일 목록을 특별한 메시지 타입으로 추가
                addMessage('bot', ' 검색된 파일 목록:', false, null, 'file_list', files)
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
        addBotMessageWithTyping(`❌ 스트리밍 API 오류: ${error.message}`)
      }
    }

    // 키보드 입력 처리 함수
    const handleKeyDown = (event) => {
      console.log('🔍 Key pressed:', event.key, 'KeyCode:', event.keyCode, 'Code:', event.code)
      
      if (event.key === 'Tab' || event.keyCode === 9) {
        // Tab: 메시지 전송
        console.log('🔍 Tab detected, sending message')
        event.preventDefault()
        event.stopPropagation()
        sendMessage()
      } else if (event.key === 'Enter' || event.keyCode === 13) {
        // Enter: 줄바꿈 (기본 동작 허용)
        console.log('🔍 Enter detected, allowing new line')
        // preventDefault()를 호출하지 않아서 자동으로 줄바꿈됨
        
        // 줄바꿈 후 높이 조정
        nextTick(() => {
          adjustTextareaHeight()
        })
      }
    }

    // textarea 높이 자동 조정 함수를 헬퍼 함수로 위임
    const adjustTextareaHeight = () => {
      adjustTextareaHeightHelper(messageInput.value)
    }

    const sendMessage = async () => {
      const message = currentMessage.value.trim()
      
      console.log('📤 sendMessage called')
      console.log('📤 message:', message)
      console.log('📤 selectedFile:', selectedFile.value)
      console.log('📤 selectedDataType:', selectedDataType.value)
      
      // 메시지가 없거나 로딩 중이면 리턴
      if (!message || isLoading.value) return
      
      // 활성 채팅방이 없으면 첫 번째 채팅방 선택
      if (!activeChatId.value && chatRooms.value.length > 0) {
        await selectChatRoom(chatRooms.value[0].id)
      }
      
      // 채팅방이 여전히 없으면 에러
      if (!activeChatId.value) {
        // 채팅방 선택 필요 - 백엔드에서 에러 메시지 처리
        return
      }
      
      // 새 채팅방 표시 제거 (첫 번째 메시지 전송 시)
      if (newChatroomDisplay.value[activeChatId.value]) {
        newChatroomDisplay.value[activeChatId.value] = false
      }
      
      // 새 메시지 전송 시 기존 에러 메시지들 제거
      clearErrorMessages()
      
      isLoading.value = true
      
      // 데이터 타입이 'excel'이면 무조건 /excel_analysis_stream으로 전송
      if (selectedDataType.value === 'excel') {
        console.log('🚀 Sending to /excel_analysis_stream (file:', selectedFile.value ? selectedFile.value.name : 'none', ')')
        await uploadExcelFile(selectedFile.value, message)
        selectedFile.value = null // 업로드 후 파일 제거
        chatInputs.value[activeChatId.value] = ''
        
        // textarea 높이 초기화
        nextTick(() => {
          adjustTextareaHeight()
        })
        
        isLoading.value = false
        return
      }
      
      console.log('📨 Processing as regular message to /chat')
      
      // 일반 메시지 처리
      // Add user message (모든 사용자 메시지는 수정 가능)
      addMessage('user', message, true)
      chatInputs.value[activeChatId.value] = ''
      
      // textarea 높이 초기화
      nextTick(() => {
        adjustTextareaHeight()
      })
      
      // 채팅방 정보 업데이트
      updateChatRoomInfo(message)
      updateChatRoomName(message)
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Process the message
      await processUserMessage(message)
      
      isLoading.value = false
    }

    // 엑셀 파일 업로드 관련 함수들
    const triggerFileUpload = () => {
      console.log('📁 File upload button clicked')
      console.log('📁 selectedDataType:', selectedDataType.value)
      console.log('📁 fileInput ref:', fileInput.value)
      
      if (fileInput.value) {
        fileInput.value.click()
        console.log('📁 File input clicked via ref')
      } else {
        console.error('❌ fileInput ref is null, trying DOM query')
        // ref가 작동하지 않으면 DOM에서 직접 찾기
        const fileInputElement = document.querySelector('input[type="file"]')
        if (fileInputElement) {
          fileInputElement.click()
          console.log('📁 File input clicked via DOM query')
        } else {
          console.error('❌ File input element not found in DOM')
        }
      }
    }

    // 파일 선택 핸들러 (파일 선택만 처리)
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (!file) return

      // 파일 형식 검증
      const allowedTypes = ['.xlsx', '.xls', '.csv']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      
      if (!allowedTypes.includes(fileExtension)) {
        showError('지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일만 업로드 가능합니다.')
        event.target.value = ''
        return
      }

      // 파일 크기 검증 (10MB 제한)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        showError('파일 크기가 너무 큽니다. 10MB 이하의 파일을 업로드해주세요.')
        event.target.value = ''
        return
      }

      // 파일 선택 완료
      selectedFile.value = file
      console.log('📁 File selected:', file.name)
      
      // 파일 입력 초기화 (같은 파일을 다시 선택 가능하도록)
      event.target.value = ''
    }

    // 선택된 파일 제거
    const removeSelectedFile = () => {
      selectedFile.value = null
      console.log('📁 File removed')
      }

    // 파일 크기 포맷팅
    // formatFileSize를 헬퍼 함수로 위임
    const formatFileSize = (bytes) => formatFileSizeHelper(bytes)

    // 실제 파일 업로드 처리 함수
    const uploadExcelFile = async (file, prompt) => {
      try {
      // 사용자 메시지 추가
        const userMessageText = file 
          ? `📁 ${file.name} 업로드: ${prompt}` 
          : prompt
        addMessage('user', userMessageText, true)
        
        currentBotMessageIndex.value = -1
        // API 호출 - analyzeExcelFileStream 함수 사용
        await analyzeExcelFileStream(file, prompt, activeChatId.value, (data) => {
          if (data.progress_message) {
            // 진행 상황 메시지
            if (currentBotMessageIndex.value === -1) {
            addMessage('bot', data.progress_message, false)
              const messages = chatMessages.value[activeChatId.value]
              currentBotMessageIndex.value = messages.length - 1
            } else {
              updateBotMessage(currentBotMessageIndex.value, data.progress_message)
            }
          } else if (data.data) {
            // 분석 결과 처리
            const result = data.data

            // success_message -> final message
            const successMessage = result.success_message || result.summary
            if (successMessage) {
              if (currentBotMessageIndex.value === -1) {
                addMessage('bot', successMessage, false)
                const messages = chatMessages.value[activeChatId.value]
                currentBotMessageIndex.value = messages.length - 1
              } else {
                updateBotMessage(currentBotMessageIndex.value, successMessage)
              }
            }
            
            // general_text 타입일 때는 analysis result를 생성하지 않음 (봇 메시지만 표시)
            if (result.analysis_type === 'general_text') {
              console.log('⏭️ Skipping analysis result for general_text type (bot message only)')
            } else {
              const createdResult = createResultFromResponseData(result, prompt, activeChatId.value)
              if (createdResult) {
                createdResult.isActive = true
                const currentResults = chatResults.value[activeChatId.value] || []
                currentResults.push(createdResult)
                chatResults.value[activeChatId.value] = currentResults
                console.log('✅ Excel analysis result added:', createdResult)
              }
            }
          } else if (data.msg) {
            // 에러 메시지
            addMessage('bot', data.msg, false)
          }
        })
      } catch (error) {
        console.error('파일 업로드 오류:', error)
        addMessage('bot', `파일 업로드 중 오류가 발생했습니다: ${error.message}`, false)
      }
    }

    // 메시지 수정 관련 함수들
    const startEdit = (messageIndex) => {
      const messages = chatMessages.value[activeChatId.value]
      if (!messages || !messages[messageIndex]) return
      
      const message = messages[messageIndex]
      if (message.type !== 'user') return
      
      // 수정 모드 시작
      message.isEditing = true
      message.editText = message.text // 원본 텍스트를 편집 텍스트로 복사
      
      // 다음 tick에서 입력 필드에 포커스
      nextTick(() => {
        const editInput = document.querySelector('.message-edit-input')
        if (editInput) {
          editInput.focus()
          editInput.select()
        }
      })
    }
    
    const cancelEdit = (messageIndex) => {
      const messages = chatMessages.value[activeChatId.value]
      if (!messages || !messages[messageIndex]) return
      
      const message = messages[messageIndex]
      message.isEditing = false
      message.editText = ''
    }
    
    const saveEdit = async (messageIndex) => {
      const messages = chatMessages.value[activeChatId.value]
      if (!messages || !messages[messageIndex]) return
      
      const message = messages[messageIndex]
      if (message.type !== 'user' || !message.isEditing) return
      
      const newText = message.editText.trim()
      if (!newText || newText === message.text) {
        // 텍스트가 변경되지 않았으면 수정 모드만 종료
        message.isEditing = false
        message.editText = ''
        return
      }
      
      // 기존 응답에서 chat_id 찾기
      const currentResults = chatResults.value[activeChatId.value] || []
      const lastResult = currentResults[currentResults.length - 1]
      const originalChatId = lastResult?.chatId || null
      
      console.log('🔍 Found original chat_id:', originalChatId)
      console.log('🔍 Last result:', lastResult)
      
      if (!originalChatId) {
        console.warn('⚠️ 기존 chat_id를 찾을 수 없어 일반 채팅으로 처리합니다.')
        // 기존 방식으로 처리
        message.text = newText
        message.isEditing = false
        message.editText = ''
        await processUserMessage(newText)
        return
      }
      
      try {
        // 수정 모드 종료
        message.isEditing = false
        message.editText = ''
        
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
        
        // 메시지 수정 API 호출
        isLoading.value = true
        // 메시지 수정 중 - 백엔드에서 진행 메시지 처리
        
        const editResponse = await editMessageAPI(
          selectedDataType.value, 
          newText, 
          activeChatId.value, 
          originalChatId
        )
        
        console.log('✅ Message edit response:', editResponse)
        console.log('✅ Response keys:', editResponse.response ? Object.keys(editResponse.response) : 'no response')
        console.log('✅ Response contains real_data:', editResponse.response && 'real_data' in editResponse.response)
        if (editResponse.response && editResponse.response.real_data) {
          console.log('✅ Real data records:', editResponse.response.real_data.length)
          console.log('✅ Real data sample:', editResponse.response.real_data.slice(0, 2))
        } else {
          console.log('❌ No real_data found in response')
          console.log('❌ Response content:', editResponse.response)
        }
        
        // 성공 메시지 추가
        // 메시지 수정 성공 - 백엔드에서 성공 메시지 처리
        
        // 결과 업데이트 (기존 결과를 새로운 응답으로 교체)
        if (editResponse.response && editResponse.response.real_data) {
          const newResult = createResultFromResponseData(editResponse.response, newText, editResponse.chat_id)
          if (newResult) {
            // 새 결과를 활성화
            newResult.isActive = true
            
            // 기존 결과를 새 결과로 교체
            const currentResults = chatResults.value[activeChatId.value] || []
            if (currentResults.length > 0) {
              // 기존 결과들을 비활성화
              currentResults.forEach(r => r.isActive = false)
              // 마지막 결과를 새 결과로 교체
              currentResults[currentResults.length - 1] = newResult
            } else {
              // 결과가 없으면 새로 추가
              currentResults.push(newResult)
            }
            chatResults.value[activeChatId.value] = currentResults
            
            console.log('✅ Updated results with new data:', newResult)
          }
        } else {
          console.warn('⚠️ No real_data in edit response:', editResponse.response)
        }
        
        isLoading.value = false
        scrollToBottom()
        
      } catch (error) {
        console.error('❌ Error editing message:', error)
        // 메시지 수정 실패 - 백엔드에서 에러 메시지 처리
        isLoading.value = false
      }
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
      // 모든 결과 클리어 - 백엔드에서 메시지 처리
    }

    // Analysis Results 섹션 토글 함수
    const toggleAnalysisSection = () => {
      isAnalysisCollapsed.value = !isAnalysisCollapsed.value
    }

    // 채팅방 데이터 로드
    const loadChatRooms = async () => {
      isLoadingChatRooms.value = true
      try {
        console.log(' Starting to load chatrooms...')
        const rooms = await getChatRooms()
        console.log(' Received rooms from API:', rooms)
        
        if (!rooms || rooms.length === 0) {
          console.warn('⚠️ No rooms received from API')
          chatRooms.value = []
          return
        }
        
        chatRooms.value = rooms.map(room => {
          console.log(' Processing room:', room)
          return {
            id: room.id,
            name: room.name || `채팅방 #${room.id}`, // 백엔드에서 받은 이름 사용, 없으면 기본값
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
                // 사용자 메시지 추가 (chat_time 기준)
                messages.push({
                  type: 'user',
                  text: conv.user_message,
                  timestamp: new Date(conv.chat_time),
                  chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
                  originalTime: conv.chat_time // 원본 시간 문자열 저장
                })
                
                // bot_response를 파싱하여 적절히 처리
                let botResponseText = conv.bot_response
                let responseData = null
                
                console.log('🔍 Parsing bot response:', conv.bot_response)
                
                try {
                  const parsed = JSON.parse(conv.bot_response)
                  console.log('✅ Parsed response data:', parsed)
                  
                  // success_message가 있으면 우선 사용
                  if (parsed.success_message) {
                    botResponseText = parsed.success_message
                    console.log('✅ Using success_message from backend:', parsed.success_message)
                  } else if (parsed.result) {
                    console.log('🔍 Processing result (fallback):', parsed.result)
                    // success_message가 없는 경우에만 기존 로직 사용
                    if (parsed.result === 'lot_start') {
                      botResponseText = `✅ PCM 트렌드 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
                    } else if (parsed.result === 'lot_point') {
                      botResponseText = `✅ PCM 트렌드 포인트 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
                    } else if (parsed.result === 'commonality_module') {
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
                  } else {
                    console.warn('⚠️ No success_message or result field in parsed response')
                  }
                  
                  responseData = parsed
                  
                  // 응답 데이터가 있으면 결과 생성 (real_data가 없어도 메타데이터는 저장)
                  if (responseData) {
                    const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
                    if (result) {
                      results.push(result)
                    }
                  }
                } catch (e) {
                  // JSON 파싱 실패시 원본 텍스트 사용
                  console.warn('❌ Failed to parse bot response:', e)
                  console.log(' Raw bot response:', conv.bot_response)
                }
                
                // 봇 응답 메시지 추가 (response_time 기준)
                messages.push({
                  type: 'bot',
                  text: botResponseText,
                  timestamp: new Date(conv.response_time),
                  chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
                  responseData: responseData, // 파싱된 응답 데이터 저장
                  originalTime: conv.response_time // 원본 시간 문자열 저장
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
              text: '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, INLINE, RAG 분석에 대해 질문해주세요.',
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
        // 채팅방 목록 로드 실패 - 백엔드에서 에러 메시지 처리
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
          // 사용자 메시지 추가 (chat_time 기준)
          messages.push({
            type: 'user',
            text: conv.user_message,
            timestamp: new Date(conv.chat_time),
            chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
            originalTime: conv.chat_time // 원본 시간 문자열 저장
          })
          
          // bot_response를 파싱하여 적절히 처리
          let botResponseText = conv.bot_response
          let responseData = null
          
          console.log('🔍 Parsing bot response (refresh):', conv.bot_response)
          
          try {
            const parsed = JSON.parse(conv.bot_response)
            console.log('✅ Parsed response data (refresh):', parsed)
            
            // success_message가 있으면 우선 사용
            if (parsed.success_message) {
              botResponseText = parsed.success_message
              console.log('✅ Using success_message from backend (refresh):', parsed.success_message)
            } else if (parsed.result) {
              console.log('🔍 Processing result (refresh fallback):', parsed.result)
              // success_message가 없는 경우에만 기존 로직 사용
              if (parsed.result === 'lot_start') {
                botResponseText = `✅ PCM 트렌드 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
              } else if (parsed.result === 'lot_point') {
                botResponseText = `✅ PCM 트렌드 포인트 분석이 완료되었습니다!\n• SQL: ${parsed.sql || 'N/A'}\n• Chat ID: ${conv.chat_id}`
              } else if (parsed.result === 'commonality_module') {
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
            } else {
              console.warn('⚠️ No success_message or result field in parsed response (refresh)')
            }
            
            responseData = parsed
            
            // 응답 데이터가 있으면 결과 생성 (real_data가 없어도 메타데이터는 저장)
            if (responseData) {
              const result = createResultFromResponseData(responseData, conv.user_message, conv.chat_id)
              if (result) {
                results.push(result)
              }
            }
          } catch (e) {
            // JSON 파싱 실패시 원본 텍스트 사용
            console.warn('❌ Failed to parse bot response (refresh):', e)
            console.log(' Raw bot response (refresh):', conv.bot_response)
          }
          
          // 봇 응답 메시지 추가 (response_time 기준)
          messages.push({
            type: 'bot',
            text: botResponseText,
            timestamp: new Date(conv.response_time),
            chatId: conv.chat_id, // 백엔드에서 받은 chat_id 사용
            responseData: responseData, // 파싱된 응답 데이터 저장
            originalTime: conv.response_time // 원본 시간 문자열 저장
          })
        })
        
        chatMessages.value = {
          ...chatMessages.value,
          [roomId]: messages
        }
        chatResults.value[roomId] = results
        
      } catch (error) {
        console.error(`Failed to refresh history for room ${roomId}:`, error)
        // 채팅방 히스토리 새로고침 실패 - 백엔드에서 에러 메시지 처리
      }
    }
    
    // 채팅방 관련 함수들을 헬퍼 함수로 위임
    const selectChatRoom = async (roomId) => {
      const state = {
        activeChatId,
        chatRooms,
        chatMessages,
        chatResults,
        selectedDataType
      }
      await selectChatRoomHelper(roomId, state, scrollToBottom)
    }

    const createNewChatRoom = async (newRoom) => {
      const state = {
        chatRooms,
        activeChatId,
        selectedDataType,
        chatMessages,
        chatResults,
        chatInputs,
        chatErrors,
        newChatroomDisplay
      }
      await createNewChatRoomHelper(state, loadChatRooms)
    }

    const deleteChatRoom = async (roomId) => {
      const state = {
        chatRooms,
        activeChatId,
        chatMessages,
        chatResults,
        chatInputs,
        chatErrors,
        newChatroomDisplay
      }
      await deleteChatRoomHelper(roomId, state, selectChatRoom, loadChatRooms)
    }

    // 채팅방 정보 업데이트 함수들을 헬퍼 함수로 위임
    const updateChatRoomInfo = (message) => {
      const state = {
        chatRooms,
        activeChatId
      }
      updateChatRoomInfoHelper(message, state)
    }
    
    const updateChatRoomName = (message) => {
      const state = {
        chatRooms,
        activeChatId
      }
      updateChatRoomNameHelper(message, state)
    }

    const handleUpdateRoomName = ({ roomId, name }) => {
      handleUpdateRoomNameHelper({ roomId, name })
    }

    // 인증 관련 함수들
    const checkAuthentication = () => {
      isUserAuthenticated.value = isAuthenticated()
      if (isUserAuthenticated.value) {
        currentUser.value = getUserFromToken()
        console.log('✅ User authenticated:', currentUser.value?.userId)
      } else {
        currentUser.value = null
        console.log('❌ User not authenticated')
      }
    }

    const logout = () => {
      authLogout()
      checkAuthentication()
    }

    const handleSSOCallback = () => {
      const token = getTokenFromUrl()
      if (token) {
        handleSSOLogin(token)
        checkAuthentication()
        // SSO 로그인 후 채팅방 목록 새로고침
        loadChatRooms()
      }
    }

    // currentMessage 변경 시 textarea 높이 조정
    watch(currentMessage, () => {
      nextTick(() => {
        adjustTextareaHeight()
      })
    })

    // activeChatId 변경 시 textarea 높이 조정
    watch(activeChatId, () => {
      nextTick(() => {
        adjustTextareaHeight()
      })
    })

    // selectedDataType 변경 감지
    watch(selectedDataType, (newValue, oldValue) => {
      console.log('🔄 selectedDataType changed:', oldValue, '->', newValue)
    })

    onMounted(async () => {
      // 인증 상태 확인
      checkAuthentication()
      
      // SSO 콜백 처리
      handleSSOCallback()
      
      // 인증된 사용자만 채팅방 데이터 로드
      if (isUserAuthenticated.value) {
        await loadChatRooms()
      }
      
      // textarea 초기 높이 설정
      nextTick(() => {
        adjustTextareaHeight()
      })
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
        startEdit,
        cancelEdit,
        saveEdit,
        newChatroomDisplay,
        handleErrorMessage,
        clearErrorMessages,
        // 파일 다운로드 관련
        downloadFile,
        // 엑셀 파일 업로드 관련
        fileInput,
        selectedFile,
        triggerFileUpload,
        handleFileSelect,
        removeSelectedFile,
        formatFileSize,

        // 에러 상태
        currentError,
        showError,
        chatInputs,
        chatErrors,
        showOriginalTime,
        // Analysis Results 토글
        isAnalysisCollapsed,
        toggleAnalysisSection,
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
        startResize,
        handleUpdateRoomName,
        // 인증 관련
        currentUser,
        isUserAuthenticated,
        logout,
        checkAuthentication,
        isPlotlyGraphType
      }
  }
})
</script>

<style src="./styles/app.css">
</style>

