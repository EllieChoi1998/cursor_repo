// API 서비스 - 환경변수에서 백엔드 URL 읽기
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'

// 디버깅을 위한 콘솔 출력 (개발 환경에서만)
if (process.env.NODE_ENV === 'development') {
  console.log('🔗 API Base URL:', API_BASE_URL)
}

// 채팅방 관련 API 함수들
export const createChatRoom = async (dataType) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatrooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data_type: dataType
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data  // 직접 반환 (이미 chatroom 객체)
  } catch (error) {
    console.error('Error creating chatroom:', error)
    throw error
  }
}

// API 명세에 맞는 채팅방 목록 조회
export const getChatRooms = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatrooms`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data.chatrooms
  } catch (error) {
    console.error('Error fetching chatrooms:', error)
    throw error
  }
}

// API 명세에 맞는 채팅방 히스토리 조회
export const getChatRoomHistory = async (chatroomId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatrooms/${chatroomId}/history`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching chatroom history:', error)
    throw error
  }
}



export const deleteChatRoom = async (chatroomId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatrooms/${chatroomId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error deleting chatroom:', error)
    throw error
  }
}

// 스트리밍 채팅 API
export const streamChatAPI = async (choice, message, chatroomId, onData) => {
  console.log('🚀 Sending chat request:', { choice, message, chatroomId })
  
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        choice: choice,
        message: message,
        chatroom_id: chatroomId
      })
    })
    
    console.log('📡 Response status:', response.status, response.statusText)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.trim()) {
          console.log('📝 Raw line received:', line)
        }
        
        if (line.startsWith('data: ')) {
          try {
            const jsonString = line.slice(6).trim()
            console.log('🔍 Parsing JSON:', jsonString)
            const data = JSON.parse(jsonString)
            console.log('✅ Parsed data:', data)
            onData(data)
          } catch (e) {
            console.warn('❌ Failed to parse streaming data:', e, 'Line:', line)
          }
        }
      }
    }
  } catch (error) {
    console.error('Error in streaming chat API:', error)
    throw error
  }
}

// PCM 데이터를 가져오는 함수 (스트리밍 채팅 API 사용)
export const fetchPCMData = async () => {
  // 스트리밍 채팅 API를 통해 PCM 데이터 요청
  return new Promise((resolve, reject) => {
    streamChatAPI('pcm', 'pcm trend', null, (data) => {
      if (data.msg) {
        // 백엔드 에러 응답 처리
        reject(new Error(`백엔드 오류: ${data.msg}`))
      } else if (data.response && data.response.result === 'lot_start') {
        const realData = data.response.real_data
        const chartData = generatePCMDataWithRealData(realData)
        resolve(chartData)
      }
    }).catch(reject)
  })
}

// 기본 PCM 데이터 (API가 없을 때 사용) - DataFrame JSON 형태
export const getDefaultPCMData = () => {
  return [
    {
      DATE_WAFER_ID: 1,
      MIN: 10,
      MAX: 20,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'A',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 2,
      MIN: 11,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'A',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 3,
      MIN: 11,
      MAX: 19,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'B',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 4,
      MIN: 12,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'B',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 5,
      MIN: 9,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'C',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 6,
      MIN: 11,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'A',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 7,
      MIN: 11,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'A',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 8,
      MIN: 11,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'A',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 9,
      MIN: 12,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'C',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    },
    {
      DATE_WAFER_ID: 10,
      MIN: 8,
      MAX: 21,
      Q1: 15,
      Q2: 16,
      Q3: 17,
      DEVICE: 'C',
      USL: 30,
      TGT: 15,
      LSL: 1,
      UCL: 25,
      LCL: 6
    }
  ]
}

// real_data를 활용한 PCM 데이터 생성 (DataFrame JSON 형태)
export const generatePCMDataWithRealData = (realData) => {
  // realData가 이미 DataFrame JSON 형태인 경우 그대로 반환
  if (Array.isArray(realData)) {
    return realData
  }
  
  // realData가 숫자인 경우 (기존 방식 호환성)
  const baseData = getDefaultPCMData()
  const multiplier = realData / 1000
  
  return baseData.map((row, index) => {
    return {
      DATE_WAFER_ID: row.DATE_WAFER_ID,
      MIN: Math.round((row.MIN * multiplier) * 10) / 10,
      MAX: Math.round((row.MAX * multiplier) * 10) / 10,
      Q1: Math.round((row.Q1 * multiplier) * 10) / 10,
      Q2: Math.round((row.Q2 * multiplier) * 10) / 10,
      Q3: Math.round((row.Q3 * multiplier) * 10) / 10,
      DEVICE: row.DEVICE,
      USL: row.USL,
      TGT: row.TGT,
      LSL: row.LSL,
      UCL: row.UCL,
      LCL: row.LCL
    }
  })
}

// real_data를 활용한 Commonality 데이터 생성 (DataFrame JSON 형태)
export const generateCommonalityDataWithRealData = (realData, determinedData) => {
  // realData가 이미 DataFrame JSON 형태인 경우 그대로 사용
  let data
  if (Array.isArray(realData)) {
    data = realData
  } else {
    // realData가 숫자인 경우 (기존 방식 호환성)
    const baseData = getDefaultPCMData()
    const multiplier = realData / 1000
    
    data = baseData.map((row, index) => {
      return {
        DATE_WAFER_ID: row.DATE_WAFER_ID,
        MIN: Math.round((row.MIN * multiplier) * 10) / 10,
        MAX: Math.round((row.MAX * multiplier) * 10) / 10,
        Q1: Math.round((row.Q1 * multiplier) * 10) / 10,
        Q2: Math.round((row.Q2 * multiplier) * 10) / 10,
        Q3: Math.round((row.Q3 * multiplier) * 10) / 10,
        DEVICE: row.DEVICE,
        USL: row.USL,
        TGT: row.TGT,
        LSL: row.LSL,
        UCL: row.UCL,
        LCL: row.LCL
      }
    })
  }
  
  // determined 데이터가 있으면 활용, 없으면 기본값 사용
  const goodLots = determinedData?.good_lot_name_list || ['11111', 'AABCDDD']
  const badLots = determinedData?.bad_lot_name_list || ['ABCCCD', 'BBBCCCCD']
  const goodWafers = determinedData?.good_wafer_name_list || ['WAFER001', 'WAFER002']
  const badWafers = determinedData?.bad_wafer_name_list || ['WAFER003', 'WAFER004']
  
  return {
    data: data,
    commonality: {
      good_lots: goodLots,
      bad_lots: badLots,
      good_wafers: goodWafers,
      bad_wafers: badWafers,
      real_data: realData
    }
  }
}

// 데이터 새로고침 함수 (스트리밍 채팅 API 사용)
export const refreshPCMData = async () => {
  // 스트리밍 채팅 API를 통해 PCM 데이터 새로고침 요청
  return new Promise((resolve, reject) => {
    streamChatAPI('auto', 'refresh pcm data', null, (data) => {
      if (data.msg) {
        // 백엔드 에러 응답 처리
        reject(new Error(`백엔드 오류: ${data.msg}`))
      } else if (data.response && data.response.result === 'lot_start') {
        const realData = data.response.real_data
        const chartData = generatePCMDataWithRealData(realData)
        resolve(chartData)
      }
    }).catch(reject)
  })
}

// 특정 기간의 데이터 가져오기 (스트리밍 채팅 API 사용)
export const fetchPCMDataByDateRange = async (startDate, endDate) => {
  // 스트리밍 채팅 API를 통해 특정 기간 PCM 데이터 요청
  return new Promise((resolve, reject) => {
    const message = `pcm trend from ${startDate} to ${endDate}`
    streamChatAPI('PCM', message, null, (data) => {
      if (data.msg) {
        // 백엔드 에러 응답 처리
        reject(new Error(`백엔드 오류: ${data.msg}`))
      } else if (data.response && data.response.result === 'lot_start') {
        const realData = data.response.real_data
        const chartData = generatePCMDataWithRealData(realData)
        resolve(chartData)
      }
    }).catch(reject)
  })
}

// 특정 디바이스의 데이터 가져오기 (스트리밍 채팅 API 사용)
export const fetchPCMDataByDevice = async (deviceType) => {
  // 스트리밍 채팅 API를 통해 특정 디바이스 PCM 데이터 요청
  return new Promise((resolve, reject) => {
    const message = `pcm trend for device ${deviceType}`
    streamChatAPI('PCM', message, null, (data) => {
      if (data.msg) {
        // 백엔드 에러 응답 처리
        reject(new Error(`백엔드 오류: ${data.msg}`))
      } else if (data.response && data.response.result === 'lot_start') {
        const realData = data.response.real_data
        const chartData = generatePCMDataWithRealData(realData)
        // 디바이스 필터링
        const filteredData = chartData.filter(row => row.DEVICE === deviceType)
        resolve(filteredData)
      }
    }).catch(reject)
  })
} 