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
          <span class="data-count">{{ data.length }} records</span>
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
      type: Array,
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

    // PARA 타입별로 데이터 그룹화
    const paraTypes = computed(() => {
      const types = [...new Set(props.data.map(row => row.PARA).filter(para => para !== undefined && para !== null))]
      console.log('PCMTrendChart - PARA 타입 확인:', types)
      console.log('PCMTrendChart - 전체 데이터 개수:', props.data.length)
      console.log('PCMTrendChart - 첫 번째 데이터 샘플:', props.data[0])
      return types.sort()
    })

    const getParaData = (paraType) => {
      return props.data.filter(row => row.PARA === paraType)
    }

    const setChartRef = (el, index) => {
      if (el) {
        chartRefs.value[index] = el
      }
    }

    // Helper function to generate data points for box plots
    const generateBoxPlotData = (min, q1, q2, q3, max, count = 30) => {
      const data = []
      
      // Generate data points within each quartile
      const q1Count = Math.floor(count * 0.25)
      const q2Count = Math.floor(count * 0.25)
      const q3Count = Math.floor(count * 0.25)
      const q4Count = count - q1Count - q2Count - q3Count
      
      // Q1 range (min to q1)
      for (let i = 0; i < q1Count; i++) {
        data.push(min + Math.random() * (q1 - min))
      }
      
      // Q2 range (q1 to q2)
      for (let i = 0; i < q2Count; i++) {
        data.push(q1 + Math.random() * (q2 - q1))
      }
      
      // Q3 range (q2 to q3)
      for (let i = 0; i < q3Count; i++) {
        data.push(q2 + Math.random() * (q3 - q2))
      }
      
      // Q4 range (q3 to max)
      for (let i = 0; i < q4Count; i++) {
        data.push(q3 + Math.random() * (max - q3))
      }
      
      return data
    }

    const createSingleChart = (container, data, chartTitle = null) => {
      if (!container || !data || data.length === 0) return

      console.log(`PCMTrendChart 차트 생성: ${chartTitle || 'Default'} - ${data.length}개 데이터`)

      // Extract data for control lines
      const dateWaferIds = data.map(row => row.DATE_WAFER_ID)
      const usls = data.map(row => row.USL)
      const tgts = data.map(row => row.TGT)
      const lsls = data.map(row => row.LSL)
      const ucls = data.map(row => row.UCL)
      const lcls = data.map(row => row.LCL)

      // x축 라벨 생성 (적절한 간격으로 표시)
      const xOrder = [...new Set(dateWaferIds)].sort((a, b) => a - b)
      const maxLabels = 50
      const step = Math.max(1, Math.floor(xOrder.length / maxLabels))
      const sampledLabels = xOrder.filter((_, index) => index % step === 0)

      // Create box plot traces for each device
      const deviceTypes = [...new Set(data.map(row => row.DEVICE))]
      const boxTraces = []
      
      deviceTypes.forEach(device => {
        const deviceData = data.filter(row => row.DEVICE === device)
        
        // Generate box plot data for each date point
        const allBoxData = []
        const allLabels = []
        
        deviceData.forEach(row => {
          const boxData = generateBoxPlotData(
            row.MIN, 
            row.Q1, 
            row.Q2, 
            row.Q3, 
            row.MAX
          )
          allBoxData.push(...boxData)
          allLabels.push(...Array(boxData.length).fill(row.DATE_WAFER_ID))
        })

        boxTraces.push({
          type: 'box',
          x: allLabels,
          y: allBoxData,
          name: `Device ${device}`,
          boxpoints: 'outliers',
          jitter: 0.3,
          pointpos: -1.8,
          marker: {
            color: getDeviceColor(device),
            size: 4
          },
          line: {
            color: getDeviceColor(device),
            width: 2
          },
          fillcolor: getDeviceColor(device, 0.4),
          showlegend: true
        })
      })

      // Create scatter traces for control lines
      const scatterTraces = [
        {
          type: 'scatter',
          x: dateWaferIds,
          y: usls,
          mode: 'lines',
          name: 'USL',
          line: { 
            color: 'rgba(0, 0, 0, 0.8)',
            width: 2
          },
          marker: {
            color: 'rgba(0, 0, 0, 0.8)',
            size: 4
          },
          showlegend: true
        },
        {
          type: 'scatter',
          x: dateWaferIds,
          y: tgts,
          mode: 'lines',
          name: 'TGT',
          line: { 
            color: 'rgba(0, 0, 0, 0.5)',
            width: 2
          },
          marker: {
            color: 'rgba(0, 0, 0, 0.5)',
            size: 4
          },
          showlegend: true
        },
        {
          type: 'scatter',
          x: dateWaferIds,
          y: lsls,
          mode: 'lines',
          name: 'LSL',
          line: { 
            color: 'rgba(0, 0, 0, 0.8)',
            width: 2
          },
          marker: {
            color: 'rgba(0, 0, 0, 0.8)',
            size: 4
          },
          showlegend: true
        },
        {
          type: 'scatter',
          x: dateWaferIds,
          y: ucls,
          mode: 'lines',
          name: 'UCL',
          line: { 
            color: 'rgba(255, 128, 10, 0.5)',
            width: 2,
            dash: 'dash'
          },
          marker: {
            color: 'rgba(255, 128, 10, 0.5)',
            size: 4
          },
          showlegend: true
        },
        {
          type: 'scatter',
          x: dateWaferIds,
          y: lcls,
          mode: 'lines',
          name: 'LCL',
          line: { 
            color: 'rgba(255, 128, 10, 0.5)',
            width: 2,
            dash: 'dash'
          },
          marker: {
            color: 'rgba(255, 128, 10, 0.5)',
            size: 4
          },
          showlegend: true
        }
      ]

      // Combine all traces
      const allTraces = [...boxTraces, ...scatterTraces]

      // Layout configuration
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
          categoryarray: xOrder
        },
        yaxis: {
          title: 'Values',
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        height: props.height,
        showlegend: true,
        legend: {
          x: 0,
          y: 1,
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
          createSingleChart(chartContainer.value, props.data, props.title)
        }
      }
    }

    // Helper function to get colors for different devices
    const getDeviceColor = (device, alpha = 1) => {
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
      
      const getDeviceIndex = (deviceName) => {
        let hash = 0
        for (let i = 0; i < deviceName.toString().length; i++) {
          const char = deviceName.toString().charCodeAt(i)
          hash = ((hash << 5) - hash) + char
          hash = hash & hash
        }
        return Math.abs(hash) % colorPalette.length
      }
      
      const colorIndex = getDeviceIndex(device)
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