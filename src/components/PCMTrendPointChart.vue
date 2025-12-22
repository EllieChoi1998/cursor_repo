<template>
  <div class="pcm-trend-point-chart">
    <!-- 데이터가 없는 경우 메시지 표시 -->
    <div v-if="!hasRealData" class="no-data-message">
      <div class="no-data-content">
        <i class="no-data-icon">📊</i>
        <h3>데이터가 없습니다</h3>
        <p>백엔드에서 real_data를 받지 못했습니다.</p>
      </div>
    </div>
    
    <!-- PARA별로 그룹화된 차트들 -->
    <div v-else-if="paraTypes.length > 1" class="multi-para-charts">
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
          <span class="data-count">{{ getRealData().length }} records</span>
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
  name: 'PCMTrendPointChart',
  props: {
    data: {
      type: Array,
      default: () => [
        { DATE_WAFER_ID: 1, PCM_SITE: '1', VALUE: 10, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 1, PCM_SITE: '2', VALUE: 11, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 1, PCM_SITE: '3', VALUE: 12, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 1, PCM_SITE: '4', VALUE: 13, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 1, PCM_SITE: '5', VALUE: 14, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 2, PCM_SITE: '1', VALUE: 11, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 2, PCM_SITE: '2', VALUE: 12, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 2, PCM_SITE: '3', VALUE: 13, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 2, PCM_SITE: '4', VALUE: 14, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 2, PCM_SITE: '5', VALUE: 15, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 3, PCM_SITE: '1', VALUE: 10, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 3, PCM_SITE: '2', VALUE: 11, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 3, PCM_SITE: '3', VALUE: 12, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 3, PCM_SITE: '4', VALUE: 13, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 3, PCM_SITE: '5', VALUE: 14, PARA: 'PARA_A' },
        { DATE_WAFER_ID: 4, PCM_SITE: '1', VALUE: 12, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 4, PCM_SITE: '2', VALUE: 13, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 4, PCM_SITE: '3', VALUE: 14, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 4, PCM_SITE: '4', VALUE: 15, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 4, PCM_SITE: '5', VALUE: 16, PARA: 'PARA_B' },
        { DATE_WAFER_ID: 5, PCM_SITE: '1', VALUE: 14, PARA: 'PARA_C' },
        { DATE_WAFER_ID: 5, PCM_SITE: '2', VALUE: 13, PARA: 'PARA_C' },
        { DATE_WAFER_ID: 5, PCM_SITE: '3', VALUE: 13, PARA: 'PARA_C' },
        { DATE_WAFER_ID: 5, PCM_SITE: '4', VALUE: 12, PARA: 'PARA_C' },
        { DATE_WAFER_ID: 5, PCM_SITE: '5', VALUE: 11, PARA: 'PARA_C' }
      ]
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'PCM Trend Point Chart'
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

    const VALID_SORT_CRITERIA = ['TIMELY', 'DEVICE', 'TEST_EQ']

    /**
     * backend payload가 아래처럼 바뀌어도 견고하게 처리:
     * - Array rows
     * - { real_data: <rows|para-map>, sort_criteria: '...' }
     * - { PARA1: [...], PARA2: [...], sort_criteria: '...' }
     * - { real_data: { PARA1: [...], ... }, sort_criteria: '...' }
     */
    const extractPayload = (input) => {
      let sortCriteria = null
      let source = input

      if (!source) return { rows: [], sortCriteria }

      // wrapper: { real_data, sort_criteria }
      if (typeof source === 'object' && !Array.isArray(source)) {
        if (source.sort_criteria) sortCriteria = source.sort_criteria
        if (source.sortCriteria) sortCriteria = source.sortCriteria

        if (source.real_data !== undefined) {
          source = source.real_data
        }
      }

      // wrapper: { real_data: { ... } } 형태가 한 번 더 중첩될 수 있음
      if (source && typeof source === 'object' && !Array.isArray(source) && source.real_data !== undefined) {
        if (!sortCriteria && source.sort_criteria) sortCriteria = source.sort_criteria
        if (!sortCriteria && source.sortCriteria) sortCriteria = source.sortCriteria
        source = source.real_data
      }

      // Array 형태
      if (Array.isArray(source)) {
        if (source.length === 0) return { rows: [], sortCriteria }
        // legacy: [ [rows] ]
        if (Array.isArray(source[0])) return { rows: source[0], sortCriteria }
        return { rows: source, sortCriteria }
      }

      // PARA map 형태: { PARA1: [..], PARA2: [..], ... } (+ metadata keys)
      if (source && typeof source === 'object') {
        const keys = Object.keys(source)
        const merged = []
        keys.forEach((key) => {
          const value = source[key]
          if (Array.isArray(value)) {
            value.forEach((row) => {
              merged.push({ ...(row || {}), PARA: key })
            })
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
      // 날짜/문자열 정렬은 localeCompare로 안정적으로 처리
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

    // 색상 팔레트 (DEVICE/TEST_EQ 등 공통 사용)
    const getGroupColor = (groupName, alpha = 1) => {
      const palette = [
        [102, 126, 234],
        [118, 75, 162],
        [255, 128, 10],
        [46, 204, 113],
        [231, 76, 60],
        [52, 152, 219],
        [155, 89, 182],
        [241, 196, 15],
        [230, 126, 34],
        [26, 188, 156],
        [192, 57, 43],
        [142, 68, 173],
        [39, 174, 96],
        [211, 84, 0],
        [41, 128, 185],
        [243, 156, 18],
        [149, 165, 166],
        [44, 62, 80],
        [127, 140, 141],
        [189, 195, 199]
      ]

      const name = groupName === null || groupName === undefined ? 'Series' : String(groupName)
      let hash = 0
      for (let i = 0; i < name.length; i++) {
        const char = name.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash &= hash
      }
      const idx = Math.abs(hash) % palette.length
      const [r, g, b] = palette[idx]
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    // (MIN/Q1/Q2/Q3/MAX) 요약값만 있을 때 박스 데이터 생성
    const generateBoxPlotDataFromSummary = (min, q1, q2, q3, max, count = 30) => {
      const minVal = coerceNumber(min)
      const q1Val = coerceNumber(q1)
      const q2Val = coerceNumber(q2)
      const q3Val = coerceNumber(q3)
      const maxVal = coerceNumber(max)
      if ([minVal, q1Val, q2Val, q3Val, maxVal].some(v => v === null)) return []

      const data = []
      const q1Count = Math.floor(count * 0.25)
      const q2Count = Math.floor(count * 0.25)
      const q3Count = Math.floor(count * 0.25)
      const q4Count = count - q1Count - q2Count - q3Count

      for (let i = 0; i < q1Count; i++) data.push(minVal + Math.random() * (q1Val - minVal))
      for (let i = 0; i < q2Count; i++) data.push(q1Val + Math.random() * (q2Val - q1Val))
      for (let i = 0; i < q3Count; i++) data.push(q2Val + Math.random() * (q3Val - q2Val))
      for (let i = 0; i < q4Count; i++) data.push(q3Val + Math.random() * (maxVal - q3Val))

      return data
    }

    // 실제 데이터 추출 함수 (PARA별 객체 구조 처리)
    const getRealData = () => {
      console.log('PCMTrendPointChart - props.data 확인:', props.data)
      console.log('PCMTrendPointChart - props.data 타입:', typeof props.data)
      console.log('PCMTrendPointChart - props.data 키들:', props.data ? Object.keys(props.data) : 'None')
      
      // 데이터가 없는 경우
      if (!props.data) {
        console.log('PCMTrendPointChart - props.data가 없음')
        return []
      }

      const payload = extractPayload(props.data)
      const rows = payload.rows || []
      console.log('PCMTrendPointChart - extractPayload rows:', rows.length, 'sort_criteria:', payload.sortCriteria)
      if (!rows.length) return []
      console.log('PCMTrendPointChart - rows sample:', rows[0])
      return rows
    }

    // real_data 존재 여부 확인
    const hasRealData = computed(() => {
      const data = getRealData()
      const hasData = data && data.length > 0
      console.log('PCMTrendPointChart - hasRealData:', hasData, '데이터 개수:', data ? data.length : 0)
      return hasData
    })

    // PARA 타입별로 데이터 그룹화
    const paraTypes = computed(() => {
      const data = getRealData()
      if (!data || data.length === 0) {
        console.log('PCMTrendPointChart - 실제 데이터가 없음')
        return []
      }
      
      const types = [...new Set(data.map(row => row.PARA).filter(para => para !== undefined && para !== null))]
      console.log('PCMTrendPointChart - PARA 타입 확인:', types)
      console.log('PCMTrendPointChart - 전체 데이터 개수:', data.length)
      console.log('PCMTrendPointChart - 첫 번째 데이터 샘플:', data[0])
      
      return types.sort()
    })

    const getParaData = (paraType) => {
      return getRealData().filter(row => row.PARA === paraType)
    }

    const setChartRef = (el, index) => {
      if (el) {
        chartRefs.value[index] = el
      }
    }

    // 원본 createChart 함수 기반으로 수정 (box + spec lines + sort_criteria)
    const createSingleChart = (container, inputData, chartTitle = null) => {
      if (!container) return
      
      // 입력 데이터가 없으면 전체 데이터 사용
      const data = inputData || getRealData()
      if (!data || data.length === 0) {
        console.log('PCMTrendPointChart - 차트 생성할 데이터가 없음')
        return
      }

      console.log(`PCMTrendPointChart 차트 생성: ${chartTitle || 'Default'} - ${data.length}개 데이터`)

      const currentSort = sortCriteria.value
      const colorField = currentSort === 'TEST_EQ' ? 'TEST_EQ' : 'DEVICE' // TIMELY/DEVICE => DEVICE, TEST_EQ => TEST_EQ

      // 파이썬 로직과 동일하게 정렬 기준 반영
      const sorted = [...data].sort((a, b) => {
        if (currentSort === 'DEVICE' || currentSort === 'TEST_EQ') {
          const aKey = a?.[currentSort]
          const bKey = b?.[currentSort]
          const cmpKey = String(aKey ?? '').localeCompare(String(bKey ?? ''), undefined, { numeric: true, sensitivity: 'base' })
          if (cmpKey !== 0) return cmpKey
        }
        return compareMaybeNumeric(a?.DATE_WAFER_ID, b?.DATE_WAFER_ID)
      })

      // x축 카테고리 순서(출현 순서 유지) - Plotly/px.box의 category_orders 효과
      const categoryOrder = uniqueInOrder(sorted.map((row) => row?.DATE_WAFER_ID))

      // tick label 샘플링
      const maxLabels = props.maxLabels || 50
      const step = Math.max(1, Math.floor(categoryOrder.length / maxLabels))
      const sampledLabels = categoryOrder.filter((_, index) => index % step === 0)

      // 그룹 필드가 없으면 안전하게 fallback
      const resolvedGroupField = (sorted.length && sorted[0] && sorted[0][colorField] !== undefined)
        ? colorField
        : (sorted.length && sorted[0] && sorted[0].DEVICE !== undefined)
          ? 'DEVICE'
          : (sorted.length && sorted[0] && sorted[0].PCM_SITE !== undefined)
            ? 'PCM_SITE'
            : null

      const groupKeys = uniqueInOrder(sorted.map((row) => resolvedGroupField ? row?.[resolvedGroupField] : 'Series'))

      const hasSummary = sorted.some((row) =>
        row && row.MIN !== undefined && row.MAX !== undefined && row.Q1 !== undefined && row.Q2 !== undefined && row.Q3 !== undefined
      )
      const hasValue = sorted.some((row) => row && row.VALUE !== undefined)

      // Box traces (overlay)
      const boxTraces = groupKeys.map((groupKey) => {
        const rows = sorted.filter((row) => {
          if (!resolvedGroupField) return true
          return row?.[resolvedGroupField] === groupKey
        })

        const x = []
        const y = []

        if (hasSummary) {
          rows.forEach((row) => {
            const values = generateBoxPlotDataFromSummary(row.MIN, row.Q1, row.Q2, row.Q3, row.MAX)
            if (!values.length) return
            values.forEach((val) => {
              x.push(row.DATE_WAFER_ID)
              y.push(val)
            })
          })
        } else if (hasValue) {
          rows.forEach((row) => {
            const val = coerceNumber(row.VALUE)
            if (val === null) return
            x.push(row.DATE_WAFER_ID)
            y.push(val)
          })
        }

        const traceName = resolvedGroupField ? `${resolvedGroupField}: ${groupKey}` : String(groupKey ?? 'Series')
        const baseColor = getGroupColor(groupKey)
        return {
          type: 'box',
          name: traceName,
          x,
          y,
          boxpoints: 'outliers',
          marker: { color: baseColor, size: 4 },
          line: { color: baseColor, width: 2 },
          fillcolor: getGroupColor(groupKey, 0.35),
          showlegend: true
        }
      }).filter((t) => Array.isArray(t.y) && t.y.length > 0)

      // Spec/control lines (가능한 경우에만)
      const firstRowByDate = new Map()
      sorted.forEach((row) => {
        const key = row?.DATE_WAFER_ID
        if (!firstRowByDate.has(key)) firstRowByDate.set(key, row)
      })
      const seriesByDate = (field) => categoryOrder.map((date) => coerceNumber(firstRowByDate.get(date)?.[field]))
      const shouldDrawLine = (arr) => arr.some((v) => typeof v === 'number' && Number.isFinite(v))

      const usl = seriesByDate('USL')
      const tgt = seriesByDate('TGT')
      const lsl = seriesByDate('LSL')
      const ucl = seriesByDate('UCL')
      const lcl = seriesByDate('LCL')

      const lineTraces = []
      if (shouldDrawLine(usl)) {
        lineTraces.push({
          type: 'scatter',
          mode: 'lines',
          name: 'USL',
          x: categoryOrder,
          y: usl,
          line: { color: 'rgba(255, 0, 0, 0.8)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(tgt)) {
        lineTraces.push({
          type: 'scatter',
          mode: 'lines',
          name: 'TGT',
          x: categoryOrder,
          y: tgt,
          line: { color: 'rgba(0, 0, 0, 0.5)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(lsl)) {
        lineTraces.push({
          type: 'scatter',
          mode: 'lines',
          name: 'LSL',
          x: categoryOrder,
          y: lsl,
          line: { color: 'rgba(255, 0, 0, 0.8)', width: 2 },
          showlegend: true
        })
      }
      if (shouldDrawLine(ucl)) {
        lineTraces.push({
          type: 'scatter',
          mode: 'lines',
          name: 'UCL',
          x: categoryOrder,
          y: ucl,
          line: { color: 'rgba(255, 128, 10, 0.5)', width: 2, dash: 'dash' },
          showlegend: true
        })
      }
      if (shouldDrawLine(lcl)) {
        lineTraces.push({
          type: 'scatter',
          mode: 'lines',
          name: 'LCL',
          x: categoryOrder,
          y: lcl,
          line: { color: 'rgba(255, 128, 10, 0.5)', width: 2, dash: 'dash' },
          showlegend: true
        })
      }

      const traces = [...boxTraces, ...lineTraces]
      
      const layout = {
        title: {
          text: chartTitle || props.title,
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
          categoryarray: categoryOrder
        },
        yaxis: {
          title: 'Value',
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
      
      console.log('PCMTrendPointChart - Plotly 차트 생성 시도:', {
        container: container,
        tracesCount: traces.length,
        dataLength: data.length,
        sort_criteria: currentSort,
        color_field: colorField
      })
      
      Plotly.newPlot(container, traces, layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        scrollZoom: true
      }).then(() => {
        console.log('PCMTrendPointChart - Plotly 차트 생성 완료')
      }).catch(error => {
        console.error('PCMTrendPointChart - Plotly 차트 생성 실패:', error)
      })
    }

    const createCharts = async () => {
      console.log('PCMTrendPointChart - createCharts 시작')
      
      // real_data가 없으면 차트 생성하지 않음
      if (!hasRealData.value) {
        console.log('PCMTrendPointChart: real_data가 없어서 차트 생성 중단')
        return
      }
      
      const data = getRealData()
      if (!data || data.length === 0) {
        console.log('PCMTrendPointChart: 데이터가 없어서 차트 생성 중단')
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
        console.log(`PCMTrendPointChart: ${paraTypes.value.length}개의 PARA 타입별 차트 생성`, paraTypes.value)
        paraTypes.value.forEach((paraType, index) => {
          const paraData = getParaData(paraType)
          console.log(`PCMTrendPointChart: PARA ${paraType} 데이터 개수: ${paraData.length}`)
          const container = chartRefs.value[index]
          if (container && paraData.length > 0) {
            createSingleChart(container, paraData, `${props.title} - PARA: ${paraType}`)
          }
        })
      } else {
        // 단일 PARA 또는 PARA 컬럼이 없는 경우
        console.log('PCMTrendPointChart: 단일 차트 생성, PARA 타입:', paraTypes.value)
        if (chartContainer.value) {
          createSingleChart(chartContainer.value, data, props.title)
        }
      }
    }

    onMounted(() => {
      console.log('PCMTrendPointChart 마운트됨')
      console.log('PCMTrendPointChart 마운트됨 - props.data:', props.data)
      console.log('PCMTrendPointChart 마운트됨 - getRealData():', getRealData())
      console.log('PCMTrendPointChart 마운트됨 - PARA 타입들:', paraTypes.value)
      createCharts()
    })

    watch(() => props.data, () => {
      console.log('PCMTrendPointChart - props.data 변경됨:', props.data)
      createCharts()
    }, { deep: true })
    watch(() => props.height, createCharts)
    watch(() => props.title, createCharts)
    watch(() => props.maxLabels, createCharts)
    watch(() => props.dataSampling, createCharts)

    return {
      chartContainer,
      chartRefs,
      paraTypes,
      hasRealData,
      getRealData,
      getParaData,
      setChartRef
    }
  }
})
</script>

<style scoped>
.pcm-trend-point-chart {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.no-data-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed #dee2e6;
}

.no-data-content {
  text-align: center;
  color: #6c757d;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.no-data-content h3 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #495057;
}

.no-data-content p {
  margin: 0;
  font-size: 16px;
  color: #6c757d;
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
