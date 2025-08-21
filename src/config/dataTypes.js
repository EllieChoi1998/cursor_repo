// 확장 가능한 데이터 타입 설정
// 새로운 데이터 타입과 Plotly 차트를 쉽게 추가할 수 있는 설정 파일
// 모든 데이터는 POST /chat 엔드포인트를 통해 스트리밍으로 처리됨

export const DATA_TYPES = {
  PCM: {
    name: 'PCM',
    displayName: 'Process Control Monitor',
    description: 'PCM 트렌드 분석 및 데이터 시각화',
    supportedResults: ['lot_start', 'commonality_start', 'lot_point'],
    chartTypes: {
      lot_start: {
        type: 'box',
        component: 'PCMTrendChart',
        title: 'PCM Trend Analysis',
        description: 'Box plot showing PCM data distribution by device type'
      },
      lot_point: {
        type: 'line',
        component: 'PCMTrendPointChart',
        title: 'PCM Trend Point Chart',
        description: 'Line+marker chart showing PCM_SITE별 trend by DATE_WAFER_ID'
      },
      commonality_start: {
        type: 'table',
        component: 'CommonalityTable',
        title: 'Commonality Analysis',
        description: 'Detailed table with commonality analysis results'
      }
    },
    dataProcessor: 'generatePCMDataWithRealData',
    commonalityProcessor: 'generateCommonalityDataWithRealData'
  },
  INLINE: {
    name: 'INLINE',
    displayName: 'Inline Analysis',
    description: 'Inline Analysis 분석 및 성능 모니터링',
    supportedResults: ['inline_analysis', 'inline_trend'],
    chartTypes: {
      inline_analysis: {
        type: 'scatter',
        component: 'InlineAnalysisChart',
        title: 'INLINE Analysis Chart',
        description: 'Scatter plot showing INLINE analysis results'
      },
      inline_trend: {
        type: 'line',
        component: 'InlineTrendChart',
        title: 'INLINE Trend Chart',
        description: 'Line chart showing INLINE trends over time'
      }
    },
    dataProcessor: 'generateInlineDataWithRealData',
    // 향후 INLINE 전용 차트 컴포넌트 추가 예정
  },
  RAG: {
    name: 'RAG',
    displayName: 'Retrieval-Augmented Generation',
    description: 'RAG 기반 데이터 분석 및 인사이트',
    supportedResults: ['rag_analysis', 'rag_summary'],
    chartTypes: {
      rag_analysis: {
        type: 'bar',
        component: 'RAGAnalysisChart',
        title: 'RAG Analysis Results',
        description: 'Bar chart showing RAG analysis results'
      },
      rag_summary: {
        type: 'text',
        component: 'RAGSummaryComponent',
        title: 'RAG Summary',
        description: 'Text-based summary of RAG analysis'
      }
    },
    dataProcessor: 'generateRAGDataWithRealData',
    // 향후 RAG 전용 컴포넌트 추가 예정
  }
}

// 데이터 프로세서 매핑
export const DATA_PROCESSORS = {
  generatePCMDataWithRealData: (realData) => {
    // PCM 데이터 생성 로직 (api.js에서 import)
    return null // 실제로는 api.js에서 import
  },
  generateCommonalityDataWithRealData: (realData, determinedData) => {
    // Commonality 데이터 생성 로직 (api.js에서 import)
    return null // 실제로는 api.js에서 import
  },
  generateInlineDataWithRealData: (realData) => {
    // INLINE 데이터 생성 로직 (향후 구현)
    return []
  },
  generateRAGDataWithRealData: (realData) => {
    // RAG 데이터 생성 로직 (향후 구현)
    return {}
  }
}

// 차트 컴포넌트 매핑
export const CHART_COMPONENTS = {
  PCMTrendChart: 'PCMTrendChart',
  CommonalityTable: 'CommonalityTable',
  InlineAnalysisChart: 'InlineAnalysisChart', // 향후 구현
  InlineTrendChart: 'InlineTrendChart', // 향후 구현
  RAGAnalysisChart: 'RAGAnalysisChart', // 향후 구현
  RAGSummaryComponent: 'RAGSummaryComponent' // 향후 구현
}

// API 엔드포인트 설정 - 모든 데이터는 스트리밍 채팅 API를 통해 처리
export const API_ENDPOINTS = {
  chat: '/chat' // 모든 데이터 요청은 이 엔드포인트를 통해 스트리밍으로 처리
}

// 스트리밍 응답 처리 설정
export const STREAMING_CONFIG = {
  chunkSize: 1024,
  timeout: 30000, // 30초
  retryAttempts: 3,
  retryDelay: 1000 // 1초
}

// 스트리밍 기반 데이터 처리 방식
export const STREAMING_DATA_FLOW = {
  // 모든 데이터 요청은 POST /chat 엔드포인트로 전송
  endpoint: '/chat',
  method: 'POST',
  
  // 요청 구조
  requestFormat: {
    choice: 'PCM|INLINE|RAG', // 데이터 타입 선택
    message: '사용자 메시지', // 구체적인 요청 내용
    chatroom_id: '채팅방 ID' // 선택사항
  },
  
  // 응답 구조 (Server-Sent Events)
  responseFormat: {
    type: 'data',
    data: {
      chat_id: '채팅 ID',
      response: {
        result: 'lot_start|commonality_start|inline_analysis|...',
        real_data: 'DataFrame JSON 또는 숫자',
        sql: '실행된 SQL 쿼리',
        determined: '추가 데이터 (commonality의 경우)'
      }
    }
  },
  
  // 에러 응답 구조
  errorResponseFormat: {
    msg: '에러 메시지' // 백엔드에서 문제 발생 시 반환되는 에러 메시지
  }
}

// 새로운 데이터 타입 추가를 위한 헬퍼 함수
export const addDataType = (key, config) => {
  DATA_TYPES[key] = config
}

// 새로운 차트 타입 추가를 위한 헬퍼 함수
export const addChartType = (dataTypeKey, resultKey, chartConfig) => {
  if (DATA_TYPES[dataTypeKey]) {
    DATA_TYPES[dataTypeKey].chartTypes[resultKey] = chartConfig
  }
}

// 데이터 타입 유효성 검사
export const isValidDataType = (choice) => {
  return Object.keys(DATA_TYPES).includes(choice.toUpperCase())
}

// 결과 타입 유효성 검사
export const isValidResultType = (choice, result) => {
  const dataType = DATA_TYPES[choice.toUpperCase()]
  return dataType && dataType.supportedResults.includes(result)
}

// 차트 타입 가져오기
export const getChartType = (choice, result) => {
  const dataType = DATA_TYPES[choice.toUpperCase()]
  return dataType?.chartTypes[result] || null
}

// 에러 응답 검사 함수
export const isErrorResponse = (data) => {
  return data && typeof data === 'object' && 'msg' in data
}

// 에러 메시지 추출 함수
export const extractErrorMessage = (data) => {
  if (isErrorResponse(data)) {
    return data.msg
  }
  return null
}

// 응답 데이터 검증 함수
export const validateResponse = (data) => {
  if (isErrorResponse(data)) {
    throw new Error(`백엔드 오류: ${data.msg}`)
  }
  
  if (!data || typeof data !== 'object') {
    throw new Error('유효하지 않은 응답 데이터')
  }
  
  return true
} 