// Mock API Server for Development
const express = require('express')
const cors = require('cors')
const app = express()
const PORT = process.env.PORT || 3000

// CORS 설정
app.use(cors())
app.use(express.json())

// Mock PCM 데이터
let mockPCMData = [
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

// 랜덤 데이터 생성 함수
const generateRandomData = () => {
  const newData = []
  for (let i = 1; i <= 15; i++) {
    const device = ['A', 'B', 'C'][Math.floor(Math.random() * 3)]
    const baseValue = 10 + Math.random() * 10
    const min = baseValue - 2
    const max = baseValue + 2
    const q1 = baseValue - 1
    const q2 = baseValue
    const q3 = baseValue + 1
    
    newData.push([
      i, // DATE_WAFER_ID
      Math.round(min * 10) / 10, // MIN
      Math.round(max * 10) / 10, // MAX
      Math.round(q1 * 10) / 10,  // Q1
      Math.round(q2 * 10) / 10,  // Q2
      Math.round(q3 * 10) / 10,  // Q3
      device,                     // DEVICE
      30,                         // USL
      15,                         // TGT
      1,                          // LSL
      25,                         // UCL
      6                           // LCL
    ])
  }
  return newData
}

// API 라우트

// PCM 데이터 조회
app.get('/api/pcm-data', (req, res) => {
  const { startDate, endDate } = req.query
  
  let filteredData = mockPCMData
  
  // 날짜 필터링
  if (startDate && endDate) {
    filteredData = mockPCMData.filter(row => {
      const dateId = row[0]
      return dateId >= parseInt(startDate) && dateId <= parseInt(endDate)
    })
  }
  
  // 랜덤 지연 시간 (실제 API 느낌을 위해)
  setTimeout(() => {
    res.json(filteredData)
  }, Math.random() * 1000 + 200)
})

// 데이터 새로고침
app.post('/api/pcm-data/refresh', (req, res) => {
  // 새로운 랜덤 데이터 생성
  mockPCMData = generateRandomData()
  
  setTimeout(() => {
    res.json({
      message: 'Data refreshed successfully',
      data: mockPCMData
    })
  }, Math.random() * 1000 + 500)
})

// 특정 디바이스 데이터 조회
app.get('/api/pcm-data/device/:deviceType', (req, res) => {
  const { deviceType } = req.params
  const filteredData = mockPCMData.filter(row => row[6] === deviceType)
  
  setTimeout(() => {
    res.json(filteredData)
  }, Math.random() * 500 + 100)
})

// 서버 상태 확인
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    dataCount: mockPCMData.length
  })
})

// 서버 시작
app.listen(PORT, () => {
  console.log(`🚀 Mock API Server running on http://localhost:${PORT}`)
  console.log(`📊 Available endpoints:`)
  console.log(`   GET  /api/pcm-data`)
  console.log(`   POST /api/pcm-data/refresh`)
  console.log(`   GET  /api/pcm-data/device/:deviceType`)
  console.log(`   GET  /api/health`)
  console.log(`\n💡 To use this mock server, set VUE_APP_API_BASE_URL=http://localhost:${PORT}/api in your .env file`)
})

module.exports = app 