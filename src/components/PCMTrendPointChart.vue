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

      // PARA별 객체 구조인지 확인 (PARA1, PARA2, ... 형태)
      if (typeof props.data === 'object' && !Array.isArray(props.data)) {
        const keys = Object.keys(props.data)
        console.log('PCMTrendPointChart - 객체 구조 감지, 키들:', keys)
        
        // PARA로 시작하는 키들이 있는지 확인하거나, 첫 번째 값이 배열인지 확인
        const firstKey = keys[0]
        if (firstKey && Array.isArray(props.data[firstKey])) {
          console.log('PCMTrendPointChart - PARA별 객체 구조 확인됨')
          
          // 모든 PARA 데이터를 하나의 배열로 합치기
          const allData = []
          keys.forEach(paraKey => {
            const paraData = props.data[paraKey]
            if (Array.isArray(paraData)) {
              console.log(`PCMTrendPointChart - ${paraKey}: ${paraData.length}개 데이터`)
              console.log(`PCMTrendPointChart - ${paraKey} 첫 번째 데이터:`, paraData[0])
              
              // 각 데이터에 PARA 정보 추가
              paraData.forEach(row => {
                allData.push({
                  ...row,
                  PARA: paraKey
                })
              })
            }
          })
          console.log('PCMTrendPointChart - 전체 병합된 데이터:', allData.length, '개')
          console.log('PCMTrendPointChart - 병합된 데이터 샘플:', allData[0])
          return allData
        }
      }

      // real_data 구조인지 확인 (중첩된 경우)
      if (props.data.real_data && typeof props.data.real_data === 'object') {
        console.log('PCMTrendPointChart - real_data 중첩 구조 감지:', Object.keys(props.data.real_data))
        // real_data 안의 모든 PARA 데이터를 하나의 배열로 합치기
        const allData = []
        Object.keys(props.data.real_data).forEach(paraKey => {
          const paraData = props.data.real_data[paraKey]
          if (Array.isArray(paraData)) {
            // 각 데이터에 PARA 정보 추가
            paraData.forEach(row => {
              allData.push({
                ...row,
                PARA: paraKey
              })
            })
          }
        })
        console.log('PCMTrendPointChart - real_data에서 추출한 전체 데이터:', allData.length, '개')
        return allData
      }

      // 기존 구조 처리 (배열)
      if (Array.isArray(props.data)) {
        console.log('PCMTrendPointChart - 배열 구조 감지')
        if (props.data.length === 0) {
          console.log('PCMTrendPointChart - props.data가 빈 배열')
          return []
        }
        
        // props.data[0]이 배열인 경우 (기존 방식)
        const data = props.data[0]
        if (Array.isArray(data)) {
          console.log('PCMTrendPointChart - props.data[0] 배열 구조 사용')
          return data
        }
        
        // props.data 자체가 데이터 배열인 경우
        if (props.data[0] && props.data[0].DATE_WAFER_ID !== undefined) {
          console.log('PCMTrendPointChart - props.data 직접 사용')
          return props.data
        }
      }
      
      console.log('PCMTrendPointChart - 알 수 없는 데이터 구조')
      return []
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

    // 원본 createChart 함수 기반으로 수정
    const createSingleChart = (container, inputData, chartTitle = null) => {
      if (!container) return
      
      // 입력 데이터가 없으면 전체 데이터 사용
      const data = inputData || getRealData()
      if (!data || data.length === 0) {
        console.log('PCMTrendPointChart - 차트 생성할 데이터가 없음')
        return
      }

      console.log(`PCMTrendPointChart 차트 생성: ${chartTitle || 'Default'} - ${data.length}개 데이터`)
      
      // PCM_SITE별로 그룹화
      const siteGroups = {}
      data.forEach(row => {
        if (!siteGroups[row.PCM_SITE]) siteGroups[row.PCM_SITE] = { x: [], y: [] }
        siteGroups[row.PCM_SITE].x.push(row.DATE_WAFER_ID)
        siteGroups[row.PCM_SITE].y.push(row.VALUE)
      })
      
      // 각 site별 trace 생성
      const traces = Object.keys(siteGroups).map(site => ({
        type: 'scatter',
        mode: 'lines+markers',
        x: siteGroups[site].x,
        y: siteGroups[site].y,
        name: `Site ${site}`,
        marker: { size: 6 },
        line: { width: 1.5 }
      }))
      
      // x축 라벨 생성 (적절한 간격으로 표시)
      const xOrder = [...new Set(data.map(row => row.DATE_WAFER_ID))].sort((a, b) => a - b)
      const maxLabels = 50
      const step = Math.max(1, Math.floor(xOrder.length / maxLabels))
      const sampledLabels = xOrder.filter((_, index) => index % step === 0)
      
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
          title: 'Value',
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        height: props.height,
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
        siteGroups: Object.keys(siteGroups)
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
