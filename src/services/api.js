// API 서비스
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000/api'

// PCM 데이터를 가져오는 함수
export const fetchPCMData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/pcm-data`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching PCM data:', error)
    // 에러 발생 시 기본 데이터 반환
    return getDefaultPCMData()
  }
}

// 기본 PCM 데이터 (API가 없을 때 사용)
export const getDefaultPCMData = () => {
  return [
    [1, 10, 20, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
    [2, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
    [3, 11, 19, 15, 16, 17, 'B', 30, 15, 1, 25, 6],
    [4, 12, 21, 15, 16, 17, 'B', 30, 15, 1, 25, 6],
    [5, 9, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6],
    [6, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
    [7, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
    [8, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
    [9, 12, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6],
    [10, 8, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6]
  ]
}

// 데이터 새로고침 함수
export const refreshPCMData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/pcm-data/refresh`, {
      method: 'POST'
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error refreshing PCM data:', error)
    throw error
  }
}

// 특정 기간의 데이터 가져오기
export const fetchPCMDataByDateRange = async (startDate, endDate) => {
  try {
    const response = await fetch(`${API_BASE_URL}/pcm-data?startDate=${startDate}&endDate=${endDate}`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching PCM data by date range:', error)
    return getDefaultPCMData()
  }
}

// 특정 디바이스의 데이터 가져오기
export const fetchPCMDataByDevice = async (deviceType) => {
  try {
    const response = await fetch(`${API_BASE_URL}/pcm-data/device/${deviceType}`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error fetching PCM data by device:', error)
    return getDefaultPCMData().filter(row => row[6] === deviceType)
  }
} 