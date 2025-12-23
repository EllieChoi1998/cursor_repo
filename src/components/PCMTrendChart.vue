<template>
  <div class="pcm-trend-chart">
    <!-- PARA별로 그룹화된 차트들 -->
    <div v-if="paraTypes.length > 1" class="multi-para-charts">
      <div 
        v-for="(paraType, index) in paraTypes" 
        :key="paraType"
        class="para-chart-container"
      >
        <div class="para-chart-header">
          <h3>{{ title }} - PARA: {{ paraType }}</h3>
          <div class="para-chart-info">
            <span class="data-count">{{ getParaData(paraType).length }} records</span>
          </div>
        </div>
        <div 
          :ref="el => setChartRef(el, index)"
          class="chart-container"
        ></div>
      </div>
    </div>
    
    <!-- 단일 PARA 또는 PARA 컬럼이 없는 경우 기존 로직 -->
    <div v-else class="single-chart">
      <div v-if="paraTypes.length === 1" class="para-chart-header">
        <h3>{{ title }} - PARA: {{ paraTypes[0] }}</h3>
        <div class="para-chart-info">
          <span class="data-count">{{ getDisplayData().length }} records</span>
        </div>
      </div>
      <div ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch, computed, nextTick } from 'vue'
import Plotly from 'plotly.js-dist'

export default defineComponent({
  name: 'PCMTrendChart',
  props: {
    data: {
      type: [Array, Object],
      default: () => [
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
          LCL: 6,
          PARA: 'PARA_A'
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
          LCL: 6,
          PARA: 'PARA_A'
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
          LCL: 6,
          PARA: 'PARA_B'
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
          LCL: 6,
          PARA: 'PARA_B'
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
          LCL: 6,
          PARA: 'PARA_C'
        },
        {
          DATE_WAFER_ID: 6,
          MIN: 13,
          MAX: 22,
          Q1: 16,
          Q2: 17,
          Q3: 18,
          DEVICE: 'A',
          USL: 30,
          TGT: 15,
          LSL: 1,
          UCL: 25,
          LCL: 6,
          PARA: 'PARA_C'
        },
        {
          DATE_WAFER_ID: 7,
          MIN: 8,
          MAX: 18,
          Q1: 14,
          Q2: 15,
          Q3: 16,
          DEVICE: 'C',
          USL: 30,
          TGT: 15,
          LSL: 1,
          UCL: 25,
          LCL: 6,
          PARA: 'PARA_A'
        },
        {
          DATE_WAFER_ID: 8,
          MIN: 14,
          MAX: 23,
          Q1: 17,
          Q2: 18,
          Q3: 19,
          DEVICE: 'B',
          USL: 30,
          TGT: 15,
          LSL: 1,
          UCL: 25,
          LCL: 6,
          PARA: 'PARA_C'
        }
      ]
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'PCM Trend Analysis'
    },
    maxLabels: {
      type: Number,
      default: 50
    },
    dataSampling: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    const chartContainer = ref(null)
    const chartRefs = ref([])
    const columns = ['DATE_WAFER_ID', 'MIN', 'MAX', 'Q1', 'Q2', 'Q3', 'DEVICE', 'USL', 'TGT', 'LSL', 'UCL', 'LCL', 'PARA']

    const VALID_SORT_CRITERIA = ['TIMELY', 'DEVICE', 'TEST_EQ']

    const coerceNumber = (value) => {
      if (value === null || value === undefined) return null
      if (typeof value === 'number') return Number.isFinite(value) ? value : null
      const parsed = Number(value)
      return Number.isFinite(parsed) ? parsed : null
    }

    const compareMaybeNumeric = (a, b) => {
      const aNum = coerceNumber(a)
      const bNum = coerceNumber(b)
      if (aNum !== null && bNum !== null) return aNum - bNum
      return String(a ?? '').localeCompare(String(b ?? ''), undefined, { numeric: true, sensitivity: 'base' })
    }

    const uniqueInOrder = (arr) => {
      const seen = new Set()
      const out = []
      arr.forEach((v) => {
        const key = v === null || v === undefined ? '__missing__' : String(v)
        if (!seen.has(key)) {
          seen.add(key)
          out.push(v)
        }
      })
      return out
    }

    /**
     * lot_start 응답이 아래처럼 와도 안전하게 처리:
     * - Array rows
     * - { real_data: <rows|para-map>, SORT_CRITERIA: '...' }
     * - { PARA1: [...], PARA2: [...], SORT_CRITERIA: '...' }
     */
    const extractPayload = (input) => {
      let sortCriteria = null
      let source = input

      if (!source) return { rows: [], sortCriteria }

      if (typeof source === 'object' && !Array.isArray(source)) {
        if (source.SORT_CRITERIA) sortCriteria = source.SORT_CRITERIA
        if (source.sortCriteria) sortCriteria = source.sortCriteria
        if (source.real_data !== undefined) source = source.real_data
        // # ellie: 12/22 note - 수정 필요함 여기 지금 적용이 안돼고 있음!!
        console.log(`‼️‼️‼️ sort_criteria: `, sortCriteria)
      }

      if (Array.isArray(source)) {
        if (source.length === 0) return { rows: [], sortCriteria }
        // legacy: [ [rows] ]
        if (Array.isArray(source[0])) return { rows: source[0], sortCriteria }
        return { rows: source, sortCriteria }
      }

      if (source && typeof source === 'object') {
        const keys = Object.keys(source)
        const merged = []
        keys.forEach((key) => {
          const value = source[key]
          if (Array.isArray(value)) {
            value.forEach((row) => merged.push({ ...(row || {}), PARA: key }))
          }
        })
        return { rows: merged, sortCriteria }
      }

      return { rows: [], sortCriteria }
    }

    const sortCriteria = computed(() => {
      const payload = extractPayload(props.data)
      const raw = payload.sortCriteria
      if (typeof raw !== 'string') return 'TIMELY'
      const upper = raw.toUpperCase()
      return VALID_SORT_CRITERIA.includes(upper) ? upper : 'TIMELY'
    })

    const getDisplayData = () => {
      const payload = extractPayload(props.data)
      return payload.rows || []
    }

    // PARA 타입별로 데이터 그룹화
    const paraTypes = computed(() => {
      const rows = getDisplayData()
      if (!rows || rows.length === 0) {
        console.log('PCMTrendChart - 데이터가 없음')
        return []
      }
      
      const types = [...new Set(rows.map(row => row.PARA).filter(para => para !== undefined && para !== null))]
      console.log('PCMTrendChart - PARA 타입 확인:', types)
      console.log('PCMTrendChart - 전체 데이터 개수:', rows.length)
      console.log('PCMTrendChart - 첫 번째 데이터 샘플:', rows[0])
      
      // 모든 데이터에 PARA 컬럼이 있는지 확인
      const hasParaCount = rows.filter(row => row.PARA !== undefined && row.PARA !== null).length
      console.log(`PCMTrendChart - PARA 컬럼이 있는 데이터: ${hasParaCount}/${rows.length}`)
      
      return types.sort()
    })

    const getParaData = (paraType) => {
      return getDisplayData().filter(row => row.PARA === paraType)
    }

    const setChartRef = (el, index) => {
      if (el) {
        chartRefs.value[index] = el
      }
    }

    // Helper function to generate data points for box plots
    const generateBoxPlotData = (min, q1, q2, q3, max, count = 30) => {
      const data = []
      const minVal = coerceNumber(min)
      const q1Val = coerceNumber(q1)
      const q2Val = coerceNumber(q2)
      const q3Val = coerceNumber(q3)
      const maxVal = coerceNumber(max)
      if ([minVal, q1Val, q2Val, q3Val, maxVal].some(v => v === null)) return []
      
      // Generate data points within each quartile
      const q1Count = Math.floor(count * 0.25)
      const q2Count = Math.floor(count * 0.25)
      const q3Count = Math.floor(count * 0.25)
      const q4Count = count - q1Count - q2Count - q3Count
      
      // Q1 range (min to q1)
      for (let i = 0; i < q1Count; i++) {
        data.push(minVal + Math.random() * (q1Val - minVal))
      }
      
      // Q2 range (q1 to q2)
      for (let i = 0; i < q2Count; i++) {
        data.push(q1Val + Math.random() * (q2Val - q1Val))
      }
      
      // Q3 range (q2 to q3)
      for (let i = 0; i < q3Count; i++) {
        data.push(q2Val + Math.random() * (q3Val - q2Val))
      }
      
      // Q4 range (q3 to max)
      for (let i = 0; i < q4Count; i++) {
        data.push(q3Val + Math.random() * (maxVal - q3Val))
      }
      
      return data
    }

    const createSingleChart = (container, data, chartTitle = null) => {
      if (!container || !data || data.length === 0) return

      console.log(`PCMTrendChart 차트 생성: ${chartTitle || 'Default'} - ${data.length}개 데이터`)

      const currentSort = sortCriteria.value
      const colorField = currentSort === 'TEST_EQ' ? 'TEST_EQ' : 'DEVICE' // TIMELY/DEVICE는 DEVICE 고정
      const resolvedColorField = data.some(row => row && row[colorField] !== undefined) ? colorField : 'DEVICE'

      // 파이썬 로직과 동일한 정렬: TIMELY => DATE, DEVICE/TEST_EQ => (criteria, DATE)
      const sorted = [...data].sort((a, b) => {
        if (currentSort === 'DEVICE' || currentSort === 'TEST_EQ') {
          const aKey = a?.[currentSort]
          const bKey = b?.[currentSort]
          const cmpKey = String(aKey ?? '').localeCompare(String(bKey ?? ''), undefined, { numeric: true, sensitivity: 'base' })
          if (cmpKey !== 0) return cmpKey
        }
        return compareMaybeNumeric(a?.DATE_WAFER_ID, b?.DATE_WAFER_ID)
      })

      // x축 카테고리 순서(등장 순서 유지)
      const xOrder = uniqueInOrder(sorted.map(row => row?.DATE_WAFER_ID))

      const maxLabels = props.maxLabels || 50
      const labelStep = Math.max(1, Math.floor(xOrder.length / maxLabels))
      const sampledLabels = xOrder.filter((_, index) => index % labelStep === 0)

      // 그룹(색상) 키 목록
      const groupKeys = uniqueInOrder(sorted.map(row => row?.[resolvedColorField]))

      // Create box plot traces for each group (DEVICE or TEST_EQ)
      const boxTraces = groupKeys.map(groupKey => {
        const groupRows = sorted.filter(row => row?.[resolvedColorField] === groupKey)
        const allBoxData = []
        const allLabels = []

        groupRows.forEach(row => {
          const boxData = generateBoxPlotData(row.MIN, row.Q1, row.Q2, row.Q3, row.MAX)
          if (!boxData.length) return
          allBoxData.push(...boxData)
          allLabels.push(...Array(boxData.length).fill(row.DATE_WAFER_ID))
        })

        if (!allBoxData.length) return null

        return {
          type: 'box',
          x: allLabels,
          y: allBoxData,
          name: `${resolvedColorField} ${groupKey}`,
          boxpoints: 'outliers',
          jitter: 0.3,
          pointpos: -1.8,
          marker: {
            color: getSeriesColor(groupKey),
            size: 4
          },
          line: {
            color: getSeriesColor(groupKey),
            width: 2
          },
          fillcolor: getSeriesColor(groupKey, 0.4),
          showlegend: true
        }
      }).filter(Boolean)

      // control line: 날짜별 첫 row를 사용 (중복 x 방지)
      const firstRowByDate = new Map()
      sorted.forEach((row) => {
        const key = row?.DATE_WAFER_ID
        if (!firstRowByDate.has(key)) firstRowByDate.set(key, row)
      })

      const seriesByDate = (field) => xOrder.map((date) => coerceNumber(firstRowByDate.get(date)?.[field]))
      const shouldDrawLine = (arr) => arr.some(v => typeof v === 'number' && Number.isFinite(v))

      const usls = seriesByDate('USL')
      const tgts = seriesByDate('TGT')
      const lsls = seriesByDate('LSL')
      const ucls = seriesByDate('UCL')
      const lcls = seriesByDate('LCL')

      const scatterTraces = []
      if (shouldDrawLine(usls)) {
        scatterTraces.push({
          type: 'scatter',
          x: xOrder,
          y: usls,
          mode: 'lines',
          name: 'USL',
          line: { color: 'rgba(255, 0, 0, 0.8)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(tgts)) {
        scatterTraces.push({
          type: 'scatter',
          x: xOrder,
          y: tgts,
          mode: 'lines',
          name: 'TGT',
          line: { color: 'rgba(0, 0, 0, 0.5)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(lsls)) {
        scatterTraces.push({
          type: 'scatter',
          x: xOrder,
          y: lsls,
          mode: 'lines',
          name: 'LSL',
          line: { color: 'rgba(255, 0, 0, 0.8)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(ucls)) {
        scatterTraces.push({
          type: 'scatter',
          x: xOrder,
          y: ucls,
          mode: 'lines',
          name: 'UCL',
          line: { color: 'rgba(255, 128, 10, 0.5)', width: 2, dash: 'dash' },
          showlegend: true
        })
      }
      if (shouldDrawLine(lcls)) {
        scatterTraces.push({
          type: 'scatter',
          x: xOrder,
          y: lcls,
          mode: 'lines',
          name: 'LCL',
          line: { color: 'rgba(255, 128, 10, 0.5)', width: 2, dash: 'dash' },
          showlegend: true
        })
      }

      // Combine all traces
      const allTraces = [...boxTraces, ...scatterTraces]

      const formatMaybeDate = (value) => {
        if (value === null || value === undefined) return 'N/A'
        const str = String(value)
        // e.g. "2025-06-1:36:57:54_A..." or "2025-06-01 ..."
        const match = str.match(/^(\d{4}-\d{2}-\d{1,2})/)
        if (match) return match[1]
        return str
      }

      const formatSpecValue = (value) => {
        const num = coerceNumber(value)
        if (num === null) return 'N/A'
        if (Number.isInteger(num)) return String(num)
        // up to 4 decimals, trim trailing zeros
        return String(Number(num.toFixed(4)))
      }

      const pickFirstFinite = (rows, field) => {
        for (const row of rows) {
          const val = coerceNumber(row?.[field])
          if (val !== null) return val
        }
        return null
      }

      const fromVal = xOrder.length ? formatMaybeDate(xOrder[0]) : 'N/A'
      const toVal = xOrder.length ? formatMaybeDate(xOrder[xOrder.length - 1]) : 'N/A'
      const uslVal = formatSpecValue(pickFirstFinite(sorted, 'USL'))
      const tgtVal = formatSpecValue(pickFirstFinite(sorted, 'TGT'))
      const lslVal = formatSpecValue(pickFirstFinite(sorted, 'LSL'))

      // PARA 이름은 chartTitle에 포함된 "PARA: xxx"가 있으면 우선 사용, 없으면 props.title 사용
      const paraMatch = String(chartTitle || '').match(/PARA:\s*([^\s<]+)\s*$/)
      const paraLabel = paraMatch ? paraMatch[1] : (paraTypes.value.length === 1 ? paraTypes.value[0] : null)
      const baseTitle = paraLabel ? `${paraLabel} PCM Trend` : (chartTitle || props.title)
      const fullTitle = `${baseTitle}<br>From: ${fromVal}    To: ${toVal}<br>USL : (${uslVal}) - TGT : (${tgtVal}) - LSL : (${lslVal})`

      // Layout configuration
      const layout = {
        title: {
          text: fullTitle,
          font: {
            size: 16,
            color: '#333'
          }
        },
        xaxis: {
          title: 'Date Wafer ID',
          type: 'category',
          showgrid: true,
          gridcolor: '#f0f0f0',
          showticklabels: true,
          tickangle: 90,
          tickmode: 'array',
          tickvals: sampledLabels,
          ticktext: sampledLabels.map(val => val.toString()),
          tickfont: {
            size: 9,
            color: '#333'
          },
          automargin: true,
          side: 'bottom',
          tickposition: 'outside',
          categoryorder: 'array',
          categoryarray: xOrder
        },
        yaxis: {
          title: 'Values',
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        height: props.height,
        boxmode: 'overlay',
        showlegend: true,
        legend: {
          orientation: 'v', 
          x: 1, 
          xanchor: 'left', 
          y: 1,
          yanchor: 'top', 
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          bordercolor: '#ccc',
          borderwidth: 1
        },
        margin: {
          l: 60,
          r: 40,
          t: 80,
          b: 150
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        hovermode: 'closest'
      }

      // Plot the chart
      Plotly.newPlot(container, allTraces, layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        scrollZoom: true
      })
    }

    const createCharts = async () => {
      // 데이터가 없거나 유효하지 않으면 차트 생성하지 않음
      const rows = getDisplayData()
      if (!rows || rows.length === 0) {
        console.log('PCMTrendChart: 데이터가 없어서 차트 생성 중단')
        return
      }

      // 모든 기존 차트 정리
      if (chartContainer.value) {
        Plotly.purge(chartContainer.value)
      }
      chartRefs.value.forEach(ref => {
        if (ref) {
          Plotly.purge(ref)
        }
      })

      await nextTick()

      if (paraTypes.value.length > 1) {
        // 여러 PARA 타입이 있는 경우 각각 차트 생성
        console.log(`PCMTrendChart: ${paraTypes.value.length}개의 PARA 타입별 차트 생성`, paraTypes.value)
        paraTypes.value.forEach((paraType, index) => {
          const paraData = getParaData(paraType)
          console.log(`PCMTrendChart: PARA ${paraType} 데이터 개수: ${paraData.length}`)
          const container = chartRefs.value[index]
          if (container && paraData.length > 0) {
            createSingleChart(container, paraData, `${props.title} - PARA: ${paraType}`)
          }
        })
      } else {
        // 단일 PARA 또는 PARA 컬럼이 없는 경우
        console.log('PCMTrendChart: 단일 차트 생성, PARA 타입:', paraTypes.value)
        if (chartContainer.value) {
          createSingleChart(chartContainer.value, rows, props.title)
        }
      }
    }

    // Helper function to get colors for groups (DEVICE/TEST_EQ)
    const getSeriesColor = (groupKey, alpha = 1) => {
      const colorPalette = [
        [102, 126, 234], // 블루
        [118, 75, 162],  // 퍼플
        [255, 128, 10],  // 오렌지
        [46, 204, 113],  // 그린
        [231, 76, 60],   // 레드
        [52, 152, 219],  // 라이트 블루
        [155, 89, 182],  // 바이올렛
        [241, 196, 15],  // 옐로우
        [230, 126, 34],  // 카로트
        [26, 188, 156],  // 터쿼이즈
        [192, 57, 43],   // 다크 레드
        [142, 68, 173],  // 다크 퍼플
        [39, 174, 96],   // 다크 그린
        [211, 84, 0],    // 다크 오렌지
        [41, 128, 185],  // 다크 블루
        [243, 156, 18],  // 다크 옐로우
        [149, 165, 166], // 그레이
        [44, 62, 80],    // 다크 그레이
        [127, 140, 141], // 라이트 그레이
        [189, 195, 199]  // 베이지
      ]
      
      const getIndex = (name) => {
        let hash = 0
        const str = (name === null || name === undefined) ? 'Series' : name.toString()
        for (let i = 0; i < str.length; i++) {
          const char = str.charCodeAt(i)
          hash = ((hash << 5) - hash) + char
          hash = hash & hash
        }
        return Math.abs(hash) % colorPalette.length
      }
      
      const colorIndex = getIndex(groupKey)
      const [r, g, b] = colorPalette[colorIndex]
      
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    onMounted(() => {
      console.log('PCMTrendChart 마운트됨 - 기본 데이터:', props.data)
      console.log('PCMTrendChart 마운트됨 - PARA 타입들:', paraTypes.value)
      createCharts()
    })

    watch(() => props.data, createCharts, { deep: true })
    watch(() => props.height, createCharts)
    watch(() => props.title, createCharts)
    watch(() => props.maxLabels, createCharts)
    watch(() => props.dataSampling, createCharts)

    return {
      chartContainer,
      chartRefs,
      paraTypes,
      getDisplayData,
      getParaData,
      setChartRef
    }
  }
})
</script>

<style scoped>
.pcm-trend-chart {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.multi-para-charts {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.para-chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.para-chart-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.para-chart-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.para-chart-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.data-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.chart-container {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background: white;
}

.single-chart .chart-container {
  margin-top: 0;
}

.single-chart .para-chart-header + .chart-container {
  border-top: none;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .para-chart-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .para-chart-header h3 {
    font-size: 16px;
  }
  
  .multi-para-charts {
    gap: 20px;
  }
}
</style> 
