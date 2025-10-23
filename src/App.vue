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
                              <strong>유사도 점수:</strong> {{ ((file.similarity || file.score) * 100).toFixed(2) }}%
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
                    @keydown="handleKeyDown"
                    placeholder="Type your message here... (Enter for new line, Tab to send)"
                    class="chat-input"
                    :disabled="isLoading"
                    rows="1"
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
                  >
                    <span v-if="isLoading">⏳</span>
                    <span v-else>📤</span>
                  </button>

                </div>
                
                <!-- 숨겨진 파일 입력 -->
                <input 
                  ref="fileInput"
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  @change="handleFileUpload"
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
import TwoDynamicTables from './components/TwoDynamicTables.vue'
import ChatRoomList from './components/ChatRoomList.vue'
import RAGAnswerList from './components/RAGAnswerList.vue'
import INLINETrendChart from './components/INLINETrendChart.vue'
import CPKAchieveRateChart from './components/CPKAchieveRateChart.vue'
import LLMDrivenInlineChart from './components/LLMDrivenInlineChart.vue'

import {
  streamChatAPI,
  editMessageAPI,
  generatePCMDataWithRealData,
  generateCommonalityDataWithRealData,
  createChatRoom,
  getChatRooms,
  getChatRoomHistory,
  deleteChatRoom as deleteChatRoomAPI,
  fetchFileContent
} from './services/api.js'
import { API_BASE_URL } from './services/api.js'
import { isErrorResponse, extractErrorMessage } from './config/dataTypes.js'
import { 
  isAuthenticated, 
  getUserFromToken, 
  handleSSOLogin, 
  getTokenFromUrl, 
  logout as authLogout 
} from './utils/auth.js'

export default defineComponent({
  name: 'App',
  components: {
    PCMTrendChart,
    PCMTrendPointChart,
    PCMToTrend,
    DynamicTable,
    TwoDynamicTables,
    ChatRoomList,
    RAGAnswerList,
    INLINETrendChart,
    CPKAchieveRateChart,
    LLMDrivenInlineChart
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

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      
      const now = new Date()
      const messageDate = new Date(timestamp)
      
      // 오늘인지 확인
      const isToday = messageDate.toDateString() === now.toDateString()
      
      if (isToday) {
        // 오늘은 시간만 표시
        return messageDate.toLocaleTimeString('ko-KR', { 
          hour: '2-digit', 
          minute: '2-digit',
          second: '2-digit'
        })
      } else {
        // 다른 날은 날짜와 시간 모두 표시
        return messageDate.toLocaleString('ko-KR', { 
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit', 
          minute: '2-digit',
          second: '2-digit'
        })
      }
    }

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
            metadata: responseData
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

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
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
        const newResultsWidth = Math.max(300, startWidths.value.resultsSidebar - deltaX)
        
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
      // 모달 DOM이 붙은 다음 Plotly가 사이즈를 다시 잡도록 강제
      nextTick(() => {
        window.dispatchEvent(new Event('resize'))
      })
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

    // textarea 높이 자동 조정 함수
    const adjustTextareaHeight = () => {
      const textarea = messageInput.value
      if (textarea) {
        // 높이를 auto로 설정하여 내용에 맞게 조정
        textarea.style.height = 'auto'
        
        // 스크롤 높이를 계산하여 최대 5줄 정도(약 120px)로 제한
        const newHeight = Math.min(textarea.scrollHeight, 120)
        textarea.style.height = newHeight + 'px'
        
        console.log('🔍 Textarea height adjusted:', newHeight + 'px')
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
        // 채팅방 선택 필요 - 백엔드에서 에러 메시지 처리
        return
      }
      
      // 새 채팅방 표시 제거 (첫 번째 메시지 전송 시)
      if (newChatroomDisplay.value[activeChatId.value]) {
        newChatroomDisplay.value[activeChatId.value] = false
      }
      
      // 새 메시지 전송 시 기존 에러 메시지들 제거
      clearErrorMessages()
      
      // Add user message (모든 사용자 메시지는 수정 가능)
      addMessage('user', message, true)
      chatInputs.value[activeChatId.value] = ''
      isLoading.value = true
      
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

    const handleFileUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // 파일 형식 검증
      const allowedTypes = ['.xlsx', '.xls', '.csv']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      
      if (!allowedTypes.includes(fileExtension)) {
        showError('지원하지 않는 파일 형식입니다. .xlsx, .xls, .csv 파일만 업로드 가능합니다.')
        return
      }

      // 파일 크기 검증 (10MB 제한)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        showError('파일 크기가 너무 큽니다. 10MB 이하의 파일을 업로드해주세요.')
        return
      }

      // 활성 채팅방이 없으면 첫 번째 채팅방 선택
      if (!activeChatId.value && chatRooms.value.length > 0) {
        await selectChatRoom(chatRooms.value[0].id)
      }
      
      if (!activeChatId.value) {
        showError('채팅방을 선택해주세요.')
        return
      }

      // 프롬프트가 없으면 기본 메시지 사용
      const prompt = currentMessage.value.trim() || '이 엑셀 파일을 분석해주세요.'

      // 사용자 메시지 추가
      addMessage('user', `📁 ${file.name} 업로드: ${prompt}`, true)
      currentMessage.value = ''
      isLoading.value = true

      try {
        // FormData 생성
        const formData = new FormData()
        formData.append('file', file)
        formData.append('message', prompt)
        formData.append('chatroom_id', activeChatId.value)

        // API 호출
        const response = await fetch('/excel_analysis_stream', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        // 스트리밍 응답 처리
        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.progress_message) {
                  // 진행 상황 메시지
                  addMessage('bot', data.progress_message, false)
                } else if (data.data) {
                  // 분석 결과 처리
                  const result = data.data
                  const createdResult = createResultFromResponseData(result, prompt, activeChatId.value)
                  if (createdResult) {
                    createdResult.isActive = true
                    const currentResults = chatResults.value[activeChatId.value] || []
                    currentResults.push(createdResult)
                    chatResults.value[activeChatId.value] = currentResults
                    console.log('✅ Excel analysis result added:', createdResult)
                  }
                } else if (data.msg) {
                  // 에러 메시지
                  addMessage('bot', data.msg, false)
                }
              } catch (e) {
                console.error('JSON 파싱 오류:', e)
              }
            }
          }
        }

      } catch (error) {
        console.error('파일 업로드 오류:', error)
        addMessage('bot', `파일 업로드 중 오류가 발생했습니다: ${error.message}`, false)
      } finally {
        isLoading.value = false
        // 파일 입력 초기화
        event.target.value = ''
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
    
    // 채팅방 관련 함수들
    const selectChatRoom = async (roomId) => {
      console.log(`🔄 Selecting chatroom ${roomId}`)
      console.log('📊 Previous activeChatId:', activeChatId.value)
      console.log('💬 All chatMessages:', Object.keys(chatMessages.value))
      console.log('📈 All chatResults:', Object.keys(chatResults.value))
      console.log(`💬 Messages for room ${roomId}:`, chatMessages.value[roomId]?.length || 0, 'messages')
      console.log(`📈 Results for room ${roomId}:`, chatResults.value[roomId]?.length || 0, 'results')
      
      activeChatId.value = roomId
      const selectedRoom = chatRooms.value.find(room => room.id === roomId)
      if (selectedRoom) {
        selectedDataType.value = selectedRoom.dataType
        // 히스토리는 이미 loadChatRooms에서 로드되므로 별도 로드 불필요
        console.log(`✅ Selected chatroom ${roomId} with data type: ${selectedRoom.dataType}`)
        console.log(`💬 Final messages count: ${(chatMessages.value[roomId] || []).length}`)
        console.log(`📈 Final results count: ${(chatResults.value[roomId] || []).length}`)
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
        
        // 새 채팅방의 입력 및 에러 상태 초기화
        chatInputs.value[createdRoom.id] = ''
        chatErrors.value[createdRoom.id] = { show: false, message: '' }
        
        // 새 채팅방 표시 활성화
        newChatroomDisplay.value[createdRoom.id] = true
        
        console.log('Successfully created and configured new chatroom:', createdRoom.id)
        
        // 채팅방 목록 새로고침
        await loadChatRooms()
        
      } catch (error) {
        console.error('Failed to create chatroom:', error)
        // 새 채팅방 생성 실패 - 백엔드에서 에러 메시지 처리
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
          delete chatInputs.value[roomId]
          delete chatErrors.value[roomId]
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
        // 채팅방 삭제 실패 - 백엔드에서 에러 메시지 처리
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

    // 채팅방 이름 수정 핸들러 (새로 추가)
    const handleUpdateRoomName = ({ roomId, name }) => {
      console.log('🔄 Chatroom name updated:', { roomId, name })
      // 로컬 상태는 이미 ChatRoomList에서 업데이트되었으므로 추가 작업 불필요
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
        checkAuthentication
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
  height: 80px;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: 100%;
}

.app-header h1 {
  font-size: 2rem;
  margin: 0;
  font-weight: 300;
  grid-column: 2;
  justify-self: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  grid-column: 3;
  justify-self: end;
}

.user-id {
  font-size: 1rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.logout-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 0.5rem;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.login-prompt {
  display: flex;
  align-items: center;
  grid-column: 3;
  justify-self: end;
}

.login-message {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  font-style: italic;
}

/* 인증 관련 스타일 */
.auth-required {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.auth-message {
  text-align: center;
  color: #666;
  padding: 2rem;
}

.auth-message h3 {
  margin-bottom: 1rem;
  color: #333;
  font-size: 1.5rem;
}

.auth-message p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
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
  height: calc(100vh - 130px);
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
  max-width: 100%;
  position: relative;
}

.results-sidebar {
  flex: 1 1 500px;
  min-width: 300px;
  max-width: 100%;
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
  max-width: 95%;
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
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.original-time {
  font-size: 0.65rem;
  color: #bbb;
  font-style: italic;
  cursor: help;
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

.input-controls-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.time-toggle {
  display: flex;
  align-items: center;
}

.time-toggle-btn {
  padding: 0.5rem 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.time-toggle-btn:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.time-toggle-btn.active {
  border-color: #667eea;
  background: #667eea;
  color: white;
}

.analysis-toggle-btn {
  padding: 0.5rem 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 3rem;
}

.analysis-toggle-btn:hover {
  border-color: #28a745;
  background: #f8fff8;
  transform: scale(1.05);
}

.analysis-toggle-btn.collapsed {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.analysis-toggle-btn.collapsed:hover {
  background: #c82333;
  border-color: #c82333;
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
  transition: border-color 0.2s ease, height 0.1s ease;
  resize: none;
  min-height: 45px;
  max-height: 120px;
  font-family: inherit;
  line-height: 1.4;
  overflow-y: auto;
  box-sizing: border-box;
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

.file-upload-button {
  width: 45px;
  height: 45px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: transform 0.2s ease;
  margin-right: 8px;
}

.file-upload-button:hover:not(:disabled) {
  transform: scale(1.05);
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}

.file-upload-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Excel Analysis Results */
.excel-analysis-result {
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.excel-header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ddd;
}

.excel-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.file-name {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.excel-summary {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #007bff;
}

.excel-summary h5 {
  margin: 0 0 0.5rem 0;
  color: #007bff;
}

.summary-content {
  white-space: pre-line;
  line-height: 1.6;
}

.excel-chart {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #28a745;
}

.excel-chart h5 {
  margin: 0 0 0.5rem 0;
  color: #28a745;
}

.chart-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

.excel-data-table {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #ffc107;
}

.excel-data-table h5 {
  margin: 0 0 0.5rem 0;
  color: #ffc107;
}

.data-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

.sample-data h6 {
  margin: 1rem 0 0.5rem 0;
  color: #333;
}

.table-container {
  max-height: 300px;
  overflow: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th,
.data-table td {
  padding: 0.5rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.excel-statistics {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #dc3545;
}

.excel-statistics h5 {
  margin: 0 0 0.5rem 0;
  color: #dc3545;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-item {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-item h6 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 0.9rem;
}

.stat-item ul {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.85rem;
}

.stat-item li {
  margin: 0.25rem 0;
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

.toggle-button {
  padding: 0.5rem;
  border: 1px solid #6c757d;
  background: white;
  color: #6c757d;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 2.5rem;
}

.toggle-button:hover {
  background: #6c757d;
  color: white;
  transform: scale(1.05);
}

.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  transition: all 0.3s ease;
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
    max-width: 100%;
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
  height: 100%;
  display: flex;
  flex-direction: column;
  color: #666;
}

.no-results-content {
  padding: 2rem;
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
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
  /* align-items: center; */
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

/* File List Styles */
.file-list-message {
  max-width: 100%;
}

.file-list {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.file-item:hover {
  background: #e9ecef;
  border-color: #667eea;
}

.file-info {
  flex: 1;
  margin-right: 1rem;
}

.file-name {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.file-preview, .file-score, .file-path {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

.file-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-download-btn {
  padding: 0.5rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.file-download-btn:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
}

.file-download-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
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

/* Message Edit Styles */
.user-message-container {
  width: 100%;
}

.editable-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.message-edit-input {
  flex: 1;
  padding: 0.5rem;
  border: 2px solid #007bff;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  color: #333;
}

.message-edit-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.edit-buttons {
  display: flex;
  gap: 0.25rem;
}

.save-button,
.cancel-button {
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.save-button {
  background: #28a745;
  color: white;
}

.save-button:hover {
  background: #218838;
}

.cancel-button {
  background: #dc3545;
  color: white;
}

.cancel-button:hover {
  background: #c82333;
}

.message-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.message-text {
  flex: 1;
  word-break: break-word;
  line-height: 1.4;
}

.message-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message:hover .message-actions {
  opacity: 1;
}

.edit-action-button {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 4px;
  background: #6c757d;
  color: white;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.edit-action-button:hover {
  background: #5a6268;
}

.edit-action-button:disabled {
  background: #adb5bd;
  cursor: not-allowed;
}

/* INLINETrendChart를 세로 스택으로 강제 */
.inline-vertical .charts-grid {
  display: grid;
  grid-template-columns: 1fr !important; /* ✅ 한 열로 고정 */
  gap: 16px;
}

/* 보기 좋게 보조 스타일(옵션) */
.inline-vertical .single-chart { width: 100%; }
.inline-vertical .chart-box { min-height: 360px; }

</style> 
