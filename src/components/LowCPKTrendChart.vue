<template>
  <div class="low-cpk-trend-chart">
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>

    <!-- 각 데이터 항목별로 차트 생성 -->
    <div class="charts-container">
      <div
        v-for="(item, index) in chartDataList"
        :key="`chart-${index}`"
        class="single-chart"
      >
        <div class="chart-title">
          {{ item.title }}
        </div>
        <div class="chart-box" :ref="el => setChartRef(index, el)"></div>
      </div>
    </div>

    <!-- 오류 메시지 -->
    <div v-if="errorMessage" class="error-box">
      <strong>차트 생성 실패:</strong> {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import Plotly from 'plotly.js-dist'

const PlotlyConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
  displaylogo: false,
  scrollZoom: true,
  staticPlot: false,
  toImageButtonOptions: {
    format: 'png',
    filename: 'low_cpk_trend_chart',
    height: 600,
    width: 800,
    scale: 1
  }
}

export default defineComponent({
  name: 'LowCPKTrendChart',
  props: {
    backendData: {
      type: Object,
      default: () => ({
        real_data: [],
        success_message: ''
      })
    },
    height: {
      type: Number,
      default: 600
    }
  },
  setup(props) {
    const chartRefs = ref({})
    const errorMessage = ref('')
    const successMessage = computed(() => props.backendData.success_message || '')

    const setChartRef = (index, el) => {
      if (!el) {
        delete chartRefs.value[index]
      } else {
        chartRefs.value[index] = el
      }
    }

    // real_data 파싱
    const chartDataList = computed(() => {
      try {
        let data = props.backendData.real_data
        
        // 문자열인 경우 JSON 파싱
        if (typeof data === 'string') {
          data = JSON.parse(data)
        }
        
        // 배열이 아니면 빈 배열 반환
        if (!Array.isArray(data)) {
          return []
        }
        
        // 각 항목에 title 추가
        return data.map((item, index) => {
          const type = (item.type || '').toUpperCase()
          const selectedRow = Array.isArray(item.selected_row_data) && item.selected_row_data.length > 0 
            ? item.selected_row_data[0] 
            : {}
          
          let title = `${type} Trend Chart ${index + 1}`
          
          // IQC의 경우
          if (type === 'IQC' && selectedRow) {
            const routeDesc = selectedRow.ROUTE_DESC || ''
            const oper = selectedRow.OPER || selectedRow.OPN || ''
            const para = selectedRow.PARA || selectedRow.PARAMETER || ''
            const usl = selectedRow.USL || ''
            const lsl = selectedRow.LSL || ''
            title = `IQC Trend - ${routeDesc} (${oper}) : ${para} (${usl} : ${lsl})`
          }
          // EQC의 경우
          else if (type === 'EQC' && selectedRow) {
            const area = selectedRow.AREA || ''
            const routeDesc = selectedRow.ROUTE_DESC || ''
            const para = selectedRow.PARA || selectedRow.PARAMETER || ''
            const usl = selectedRow.USL || ''
            const lsl = selectedRow.LSL || ''
            title = `${area} Trend - ${routeDesc} : ${para} (${usl} : ${lsl})`
          }
          
          return {
            ...item,
            title,
            index
          }
        })
      } catch (e) {
        console.error('chartDataList 파싱 오류:', e)
        return []
      }
    })

    // 색상 팔레트
    const getColorPalette = () => ([
      '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
      '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
      '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
      '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
    ])

    // IQC 차트 생성
    const createIQCChart = (item, containerEl) => {
      try {
        const graphData = item.graph_data || []
        const selectedRow = Array.isArray(item.selected_row_data) && item.selected_row_data.length > 0 
          ? item.selected_row_data[0] 
          : {}

        if (graphData.length === 0 || !containerEl) return

        // key 값으로 정렬
        const sortedData = [...graphData].sort((a, b) => {
          const keyA = String(a.key || '')
          const keyB = String(b.key || '')
          return keyA.localeCompare(keyB)
        })

        // x축 카테고리 (key 값들)
        const keys = [...new Set(sortedData.map(r => String(r.key || '')))]

        // DEVICE 값들 추출
        const devices = [...new Set(sortedData.map(r => r.DEVICE))].filter(v => v !== null && v !== undefined)
        
        // NO_VAL 컬럼들 찾기
        const noValColumns = []
        if (graphData.length > 0) {
          const firstRow = graphData[0]
          Object.keys(firstRow).forEach(k => {
            if (/^NO_VAL\d+$/.test(k)) {
              noValColumns.push(k)
            }
          })
          noValColumns.sort((a, b) => {
            const numA = parseInt(a.replace('NO_VAL', ''))
            const numB = parseInt(b.replace('NO_VAL', ''))
            return numA - numB
          })
        }

        const traces = []
        const palette = getColorPalette()

        // DEVICE별 박스플롯 생성
        devices.forEach((device, idx) => {
          const color = palette[idx % palette.length]
          const deviceRows = sortedData.filter(r => r.DEVICE === device)
          
          const x = []
          const y = []

          deviceRows.forEach(row => {
            const validValues = []
            noValColumns.forEach(noCol => {
              const v = row[noCol]
              if (v !== null && v !== undefined && v !== 9 && Number.isFinite(Number(v))) {
                validValues.push(Number(v))
              }
            })

            if (validValues.length > 0) {
              const xValue = String(row.key || '')
              validValues.forEach(val => {
                y.push(val)
                x.push(xValue)
              })
            }
          })

          if (y.length > 0) {
            traces.push({
              type: 'box',
              x,
              y,
              name: String(device),
              boxpoints: false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: 0.7,
              showlegend: true,
              legendgroup: String(device),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hoveron: 'boxes'
            })
          }
        })

        // 스펙 라인 추가 (USL, LSL, TGT)
        const pushLine = (value, name, color, dash = 'solid', width = 2) => {
          if (value !== undefined && value !== null) {
            const v = Number(value)
            if (Number.isFinite(v)) {
              traces.push({
                type: 'scatter',
                x: keys,
                y: keys.map(() => v),
                mode: 'lines',
                name: `${name}(${v})`,
                line: { color, width, dash },
                showlegend: true,
                hoverinfo: 'skip',
                legendgroup: 'spec_lines'
              })
            }
          }
        }

        // USL, LSL, TGT 값 가져오기
        const usl = sortedData[0]?.USL || selectedRow.USL
        const lsl = sortedData[0]?.LSL || selectedRow.LSL
        const tgt = sortedData[0]?.TGT || selectedRow.TGT

        pushLine(usl, 'USL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(lsl, 'LSL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(tgt, 'TGT', 'rgba(0, 0, 0, 0.5)', 'dash', 2)

        const layout = {
          xaxis: {
            title: { text: 'Key', font: { size: 12 } },
            type: 'category',
            showgrid: true,
            gridcolor: '#f0f0f0',
            categoryorder: 'array',
            categoryarray: keys,
            tickangle: 90,
            automargin: true
          },
          yaxis: {
            title: { text: 'Values', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            autorange: true
          },
          height: props.height,
          showlegend: true,
          legend: {
            orientation: 'v',
            x: 1.02,
            xanchor: 'left',
            y: 1,
            yanchor: 'top',
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            bordercolor: '#ccc',
            borderwidth: 1,
            font: { size: 10 }
          },
          boxmode: 'overlay',
          margin: { l: 60, r: 150, t: 20, b: 100 },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest'
        }

        Plotly.newPlot(containerEl, traces, layout, PlotlyConfig)
      } catch (err) {
        console.error('IQC 차트 생성 오류:', err)
        errorMessage.value = err?.message ?? String(err)
        if (containerEl) {
          containerEl.innerHTML = `
            <div style="padding:12px;text-align:center;color:#666;">
              <h4>차트 생성 실패</h4>
              <p>${err?.message ?? err}</p>
            </div>
          `
        }
      }
    }

    // EQC 차트 생성
    const createEQCChart = (item, containerEl) => {
      try {
        const graphData = item.graph_data || []
        const selectedRow = Array.isArray(item.selected_row_data) && item.selected_row_data.length > 0 
          ? item.selected_row_data[0] 
          : {}

        if (graphData.length === 0 || !containerEl) return

        // EQMNT_DATE 기준으로 정렬
        const sortedData = [...graphData].sort((a, b) => {
          const dateA = String(a.EQMNT_DATE || '')
          const dateB = String(b.EQMNT_DATE || '')
          return dateA.localeCompare(dateB)
        })

        // x축 카테고리 (key 값들)
        const keys = [...new Set(sortedData.map(r => String(r.key || '')))]

        // MAIN_EQ 값들 추출
        const mainEqs = [...new Set(sortedData.map(r => r.MAIN_EQ))].filter(v => v !== null && v !== undefined)
        
        // NO_VAL 컬럼들 찾기
        const noValColumns = []
        if (graphData.length > 0) {
          const firstRow = graphData[0]
          Object.keys(firstRow).forEach(k => {
            if (/^NO_VAL\d+$/.test(k) || k.includes('NO_VAL')) {
              noValColumns.push(k)
            }
          })
          noValColumns.sort()
        }

        const traces = []
        const palette = getColorPalette()

        // MAIN_EQ별 박스플롯 생성
        mainEqs.forEach((mainEq, idx) => {
          const color = palette[idx % palette.length]
          const eqRows = sortedData.filter(r => r.MAIN_EQ === mainEq)
          
          const x = []
          const y = []

          eqRows.forEach(row => {
            const validValues = []
            noValColumns.forEach(noCol => {
              const v = row[noCol]
              if (v !== null && v !== undefined && v !== 9 && Number.isFinite(Number(v))) {
                validValues.push(Number(v))
              }
            })

            if (validValues.length > 0) {
              const xValue = String(row.key || '')
              validValues.forEach(val => {
                y.push(val)
                x.push(xValue)
              })
            }
          })

          if (y.length > 0) {
            traces.push({
              type: 'box',
              x,
              y,
              name: String(mainEq),
              boxpoints: false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: 0.7,
              showlegend: true,
              legendgroup: String(mainEq),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hoveron: 'boxes'
            })
          }
        })

        // 스펙 라인 추가 (USL, LSL만)
        const pushLine = (value, name, color, dash = 'solid', width = 2) => {
          if (value !== undefined && value !== null) {
            const v = Number(value)
            if (Number.isFinite(v)) {
              traces.push({
                type: 'scatter',
                x: keys,
                y: keys.map(() => v),
                mode: 'lines',
                name: `${name}(${v})`,
                line: { color, width, dash },
                showlegend: true,
                hoverinfo: 'skip',
                legendgroup: 'spec_lines'
              })
            }
          }
        }

        // USL, LSL 값 가져오기
        const usl = sortedData[0]?.USL || selectedRow.USL
        const lsl = sortedData[0]?.LSL || selectedRow.LSL

        pushLine(usl, 'USL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(lsl, 'LSL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)

        const layout = {
          xaxis: {
            title: { text: 'Key', font: { size: 12 } },
            type: 'category',
            showgrid: true,
            gridcolor: '#f0f0f0',
            categoryorder: 'array',
            categoryarray: keys,
            tickangle: 90,
            automargin: true
          },
          yaxis: {
            title: { text: 'Values', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            autorange: true
          },
          height: props.height,
          showlegend: true,
          legend: {
            orientation: 'v',
            x: 1.02,
            xanchor: 'left',
            y: 1,
            yanchor: 'top',
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            bordercolor: '#ccc',
            borderwidth: 1,
            font: { size: 10 }
          },
          boxmode: 'overlay',
          margin: { l: 60, r: 150, t: 20, b: 100 },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest'
        }

        Plotly.newPlot(containerEl, traces, layout, PlotlyConfig)
      } catch (err) {
        console.error('EQC 차트 생성 오류:', err)
        errorMessage.value = err?.message ?? String(err)
        if (containerEl) {
          containerEl.innerHTML = `
            <div style="padding:12px;text-align:center;color:#666;">
              <h4>차트 생성 실패</h4>
              <p>${err?.message ?? err}</p>
            </div>
          `
        }
      }
    }

    // 모든 차트 생성
    const createCharts = async () => {
      errorMessage.value = ''
      
      await nextTick()
      
      if (chartDataList.value.length === 0) {
        return
      }

      for (const item of chartDataList.value) {
        const el = chartRefs.value[item.index]
        if (!el) continue

        // 기존 차트 제거
        try { 
          Plotly.purge(el) 
        } catch (_) {}

        const type = (item.type || '').toUpperCase()
        
        if (type === 'IQC') {
          createIQCChart(item, el)
        } else if (type === 'EQC') {
          createEQCChart(item, el)
        }
      }
    }

    // 리사이즈 처리
    const handleResize = () => {
      Object.values(chartRefs.value).forEach(el => {
        if (el) {
          try { 
            Plotly.Plots.resize(el) 
          } catch (_) {}
        }
      })
    }

    let resizeObs = null
    onMounted(async () => {
      await createCharts()
      window.addEventListener('resize', handleResize)
      if ('ResizeObserver' in window) {
        resizeObs = new ResizeObserver(handleResize)
        Object.values(chartRefs.value).forEach(el => {
          if (el) resizeObs.observe(el)
        })
      }
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
      if (resizeObs) resizeObs.disconnect()
      Object.values(chartRefs.value).forEach(el => {
        if (el) {
          try { 
            Plotly.purge(el) 
          } catch (_) {}
        }
      })
    })

    // 반응형 업데이트
    watch(() => props.backendData, createCharts, { deep: true })
    watch(() => props.height, createCharts)
    watch(chartDataList, createCharts)

    return {
      successMessage,
      chartDataList,
      setChartRef,
      errorMessage
    }
  }
})
</script>

<style scoped>
.low-cpk-trend-chart {
  width: 100%;
  position: relative;
}

.success-message {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  color: #155724;
  font-size: 14px;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.single-chart {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  padding: 12px;
  width: 100%;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.chart-box {
  width: 100%;
  min-height: 500px;
  border: 1px solid #f1f1f1;
  border-radius: 4px;
  background: white;
}

.chart-box:empty::before {
  content: "차트 로딩 중...";
  display: flex;
  align-items: center;
  justify-content: center;
  height: 500px;
  color: #666;
  font-size: 15px;
}

.error-box {
  margin-top: 10px;
  padding: 10px;
  background: #fff3f3;
  border: 1px solid #ffd6d6;
  color: #b33a3a;
  border-radius: 6px;
  font-size: 13px;
}
</style>
