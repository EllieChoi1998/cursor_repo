<template>
  <div class="cpk-achieve-rate-chart">
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>

    <!-- 데이터가 없을 때 안내 메시지 -->
    <div v-if="!hasData" class="no-data-message">
      <p>분석할 데이터가 없습니다. real_data가 제공되지 않았습니다.</p>
    </div>

    <!-- 데이터가 있을 때 테이블과 차트 표시 -->
    <div v-else class="analysis-container">
      <!-- 데이터 테이블 -->
      <div class="table-container">
        <h3>CPK 달성률 데이터</h3>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>AREA</th>
                <th v-for="period in periodColumns" :key="period">{{ period }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="area in areas" :key="area">
                <td class="area-cell">{{ area }}</td>
                <td v-for="period in periodColumns" :key="period" class="value-cell">
                  {{ getValue(area, period) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 전체 달성률 차트 -->
      <div class="charts-container">
        <h3>전체 IQC 1.67 달성율</h3>
        <div class="chart-item total-chart">
          <div class="chart-box" ref="totalChartRef"></div>
        </div>
      </div>

      <!-- 각 AREA별 바그래프 -->
      <div class="charts-container">
        <h3>AREA별 달성률 차트</h3>
        <div class="charts-grid">
          <div
            v-for="area in areas"
            :key="area"
            class="chart-item"
          >
            <div class="chart-title">{{ area }}별 IQC 1.67 달성율</div>
            <div class="chart-box" :ref="el => setChartRef(area, el)"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted, watch, nextTick } from 'vue'
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
    filename: 'cpk_achieve_rate_chart',
    height: 400,
    width: 600,
    scale: 1
  }
}

export default defineComponent({
  name: 'CPKAchieveRateChart',
  props: {
    backendData: {
      type: Object,
      default: () => ({
        result: 'cpk_achieve_rate_initial',
        real_data: JSON.stringify([]),
        success_message: 'CPK 달성률 분석이 성공적으로 생성되었습니다.'
      })
    },
    height: {
      type: Number,
      default: 400
    },
    title: {
      type: String,
      default: 'CPK 달성률 분석'
    }
  },
  setup(props) {
    // 차트 DOM 참조를 AREA별로 저장
    const chartRefs = ref({}) // { [area: string]: HTMLElement }
    const totalChartRef = ref(null)

    const setChartRef = (area, el) => {
      if (!el) {
        delete chartRefs.value[area]
      } else {
        chartRefs.value[area] = el
      }
    }

    // 데이터 파싱
    const parsedData = computed(() => {
      try {
        const realData = props.backendData.real_data
        
        // 이미 객체인 경우 그대로 사용
        if (typeof realData === 'object' && realData !== null) {
          console.log(' real_data is already an object:', realData)
          return realData
        }
        
        // 문자열인 경우 JSON 파싱
        if (typeof realData === 'string') {
          const data = JSON.parse(realData) || {}
          console.log(' parsed real_data from string:', data)
          return data
        }
        
        console.log(' real_data is neither object nor string:', typeof realData, realData)
        return {}
      } catch (e) {
        console.error('데이터 파싱 오류:', e)
        console.error('real_data 값:', props.backendData.real_data)
        return {}
      }
    })

    // 테이블 데이터 추출
    const tableData = computed(() => {
      return parsedData.value.table_data || []
    })

    // 그래프 데이터 추출
    const graphData = computed(() => {
      const data = parsedData.value.graph_data || []
      console.log(' Raw graph_data:', data)
      if (data.length > 0) {
        console.log(' First graph_data item:', data[0])
        console.log(' Available fields in graph_data:', Object.keys(data[0] || {}))
      }
      return data
    })

    // 데이터가 있는지 확인
    const hasData = computed(() => {
      return tableData.value.length > 0 || graphData.value.length > 0
    })

    // 성공 메시지
    const successMessage = computed(() => props.backendData.success_message || '')

    // AREA 목록 추출 (table_data에서 추출, Total 제외)
    const areas = computed(() => {
      if (!hasData.value) return []
      const areaSet = new Set()
      tableData.value.forEach(row => {
        if (row.AREA && row.AREA !== 'Total') {
          areaSet.add(row.AREA)
        }
      })
      console.log(' Areas from table_data (excluding Total):', Array.from(areaSet))
      return Array.from(areaSet).sort()
    })

    // 기간 컬럼 목록 추출 (AREA를 제외한 모든 컬럼)
    const periodColumns = computed(() => {
      if (!hasData.value) return []
      const firstRow = tableData.value[0]
      if (!firstRow) return []
      
      return Object.keys(firstRow)
        .filter(key => key !== 'AREA')
        .sort()
    })

    // 특정 AREA와 기간의 값 가져오기 (table_data에서)
    const getValue = (area, period) => {
      console.log(' getValue called with:', { area, period })
      console.log(' tableData.value:', tableData.value)
      
      const row = tableData.value.find(r => r.AREA === area)
      console.log(' found row:', row)
      
      if (!row) {
        console.log('❌ No row found for area:', area)
        return '-'
      }
      
      if (row[period] === undefined || row[period] === null) {
        console.log('❌ No value found for period:', period, 'in row:', row)
        return '-'
      }
      
      const value = Number(row[period])
      const result = Number.isFinite(value) ? value.toFixed(1) : '-'
      console.log('✅ getValue result:', result)
      return result
    }

    // 색상 팔레트
    const getColorPalette = () => ([
      '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
      '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
      '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
      '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
    ])

    // 간단한 테스트 차트 생성
    const createTestChart = async () => {
      try {
        console.log(' Creating test chart...')
        console.log(' totalChartRef.value:', totalChartRef.value)
        
        if (!totalChartRef.value) {
          console.log('❌ totalChartRef.value is null for test chart')
          return
        }

        // 기존 차트 제거
        try { Plotly.purge(totalChartRef.value) } catch (_) {}

        // 간단한 테스트 데이터
        const testTrace = {
          type: 'bar',
          x: ['Test1', 'Test2', 'Test3'],
          y: [10, 20, 30],
          name: 'Test Chart'
        }

        const testLayout = {
          title: 'Test Chart',
          height: 400
        }

        console.log(' Plotly.newPlot called for test chart:', { 
          containerEl: totalChartRef.value, 
          trace: testTrace, 
          layout: testLayout 
        })
        
        await Plotly.newPlot(totalChartRef.value, [testTrace], testLayout, PlotlyConfig)
        
        console.log('✅ Test chart successfully created')
      } catch (err) {
        console.error('Test chart creation error:', err)
      }
    }

    // 전체 달성률 차트 생성 (Total + 각 AREA별 라인)
    const createTotalChart = async () => {
      try {
        console.log(' Creating total chart...')
        console.log(' totalChartRef.value:', totalChartRef.value)
        console.log(' graphData.value:', graphData.value)
        
        if (!totalChartRef.value) {
          console.log('❌ totalChartRef.value is null')
          return
        }

        // 기존 차트 제거
        try { Plotly.purge(totalChartRef.value) } catch (_) {}

        // Total 데이터 찾기 - 여러 가능한 필드명 확인
        let totalData = graphData.value.filter(r => r.area === 'Total')
        if (totalData.length === 0) {
          totalData = graphData.value.filter(r => r.AREA === 'Total')
        }
        if (totalData.length === 0) {
          totalData = graphData.value.filter(r => r.Area === 'Total')
        }
        console.log(' Total data found:', totalData)
        console.log(' All unique area values:', [...new Set(graphData.value.map(r => r.area || r.AREA || r.Area))])
        
        if (totalData.length === 0) {
          console.log('❌ No Total data found')
          return
        }

        // Total 바그래프 생성
        const totalXValues = totalData.map(d => d.RDATE)
        const totalYValues = totalData.map(d => Number(d.Rate))
        
        const traces = [{
          type: 'bar',
          x: totalXValues,
          y: totalYValues,
          name: '전체 Total',
          marker: { 
            color: '#636EFA',
            line: { color: '#636EFA', width: 1 }
          },
          text: totalYValues.map(v => `${v.toFixed(1)}%`),
          textposition: 'outside',
          hovertemplate: '<b>전체 Total</b><br>날짜: %{x}<br>달성률: %{y}%<br><extra></extra>'
        }]

        // 각 AREA별 라인 추가 (Total 제외, 파란색 제외) - 여러 가능한 필드명 확인
        const palette = getColorPalette()
        // 파란색(#636EFA) 제외하고 색상 팔레트 사용
        const nonBluePalette = palette.filter(color => color !== '#636EFA')
        
        areas.value.forEach((area, index) => {
          // Total은 바그래프로만 표시하므로 라인 추가하지 않음
          if (area === 'Total') {
            console.log(`⏭️ Skipping Total area line (already shown as bar)`)
            return
          }
          
          let areaData = graphData.value.filter(r => r.area === area)
          if (areaData.length === 0) {
            areaData = graphData.value.filter(r => r.AREA === area)
          }
          if (areaData.length === 0) {
            areaData = graphData.value.filter(r => r.Area === area)
          }
          console.log(` Adding line for ${area}:`, areaData)
          if (areaData.length > 0) {
            const xValues = areaData.map(d => d.RDATE)
            const yValues = areaData.map(d => Number(d.Rate))
            
            traces.push({
              type: 'scatter',
              x: xValues,
              y: yValues,
              mode: 'lines+markers',
              name: `${area} Area`,
              line: { 
                color: nonBluePalette[index % nonBluePalette.length],
                width: 2
              },
              marker: { 
                color: nonBluePalette[index % nonBluePalette.length],
                size: 6
              },
              hovertemplate: `<b>${area} Area</b><br>날짜: %{x}<br>달성률: %{y}%<br><extra></extra>`
            })
          }
        })

        const layout = {
          title: {
            text: '전체 IQC 1.67 달성율',
            font: { size: 18, color: '#333' }
          },
          xaxis: {
            title: { text: '날짜', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            tickangle: 0
          },
          yaxis: {
            title: { text: '달성률 (%)', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            range: [0, 100]
          },
          height: props.height,
          margin: { l: 60, r: 30, t: 80, b: 120 },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest',
          showlegend: true,
          legend: {
            orientation: 'h',
            y: -0.2,
            xanchor: 'center',
            x: 0.5,
            font: { size: 12 },
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            bordercolor: '#ccc',
            borderwidth: 1
          }
        }

        console.log(' Plotly.newPlot called for total chart:', { 
          containerEl: totalChartRef.value, 
          traces, 
          layout 
        })
        
        await Plotly.newPlot(totalChartRef.value, traces, layout, PlotlyConfig)
        
        console.log('✅ Total chart successfully created')
      } catch (err) {
        console.error('전체 차트 생성 오류:', err)
        console.error('Total chart error details:', {
          containerEl: totalChartRef.value,
          traces,
          layout,
          error: err
        })
        if (totalChartRef.value) {
          totalChartRef.value.innerHTML = `
            <div style="padding:12px;text-align:center;color:#666;">
              <h4>전체 차트 생성 실패</h4>
              <p>${err?.message ?? err}</p>
            </div>
          `
        }
      }
    }

    // 특정 AREA의 바그래프 생성
    const createBarChart = async (area, containerEl) => {
      try {
        console.log(` Creating bar chart for ${area}...`)
        console.log(' containerEl:', containerEl)
        console.log(' graphData.value:', graphData.value)
        
        if (!containerEl) {
          console.log(`❌ containerEl is null for area: ${area}`)
          return
        }

        // 기존 차트 제거
        try { Plotly.purge(containerEl) } catch (_) {}

        // 해당 AREA의 그래프 데이터 찾기 - 여러 가능한 필드명 확인
        let areaGraphData = graphData.value.filter(r => r.area === area)
        if (areaGraphData.length === 0) {
          areaGraphData = graphData.value.filter(r => r.AREA === area)
        }
        if (areaGraphData.length === 0) {
          areaGraphData = graphData.value.filter(r => r.Area === area)
        }
        console.log(` Area data for ${area}:`, areaGraphData)
        
        if (areaGraphData.length === 0) {
          console.log(`❌ No data found for area: ${area}`)
          return
        }

        // 날짜별 데이터 준비
        const xValues = areaGraphData.map(d => d.RDATE)
        const yValues = areaGraphData.map(d => Number(d.Rate))
        
        console.log(` Chart data for ${area}:`, { xValues, yValues })
        
        if (yValues.length === 0) {
          console.log(`❌ No valid yValues for ${area}`)
          return
        }

        // 바그래프 트레이스 생성
        const trace = {
          type: 'bar',
          x: xValues,
          y: yValues,
          marker: {
            color: '#636EFA',
            line: {
              color: '#636EFA',
              width: 1
            }
          },
          text: yValues.map(v => `${v.toFixed(1)}%`),
          textposition: 'outside',
          hovertemplate: `<b>${area}</b><br>` +
                        `날짜: %{x}<br>` +
                        `달성률: %{y}%<br>` +
                        `<extra></extra>`,
          showlegend: false
        }

        // 레이아웃 설정
        const layout = {
          
          xaxis: {
            title: { text: '날짜', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            tickangle: 0
          },
          yaxis: {
            title: { text: '달성률 (%)', font: { size: 12 } },
            showgrid: true,
            gridcolor: '#f0f0f0',
            range: [0, 100] // 0-100% 범위로 고정
          },
          height: props.height,
          margin: { l: 60, r: 30, t: 60, b: 80 },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest'
        }

        console.log(` Plotly.newPlot called for ${area}:`, { containerEl, trace, layout })
        
        await Plotly.newPlot(containerEl, [trace], layout, PlotlyConfig)
        
        console.log(`✅ Chart successfully created for ${area}`)
      } catch (err) {
        console.error(`[${area}] 차트 생성 오류:`, err)
        console.error(`[${area}] Error details:`, {
          containerEl,
          trace,
          layout,
          error: err
        })
        if (containerEl) {
          containerEl.innerHTML = `
            <div style="padding:12px;text-align:center;color:#666;">
              <h4>차트 생성 실패 (AREA: ${area})</h4>
              <p>${err?.message ?? err}</p>
            </div>
          `
        }
      }
    }

    // 모든 차트 생성
    const createAllCharts = async () => {
      console.log(' Creating charts...')
      console.log(' hasData:', hasData.value)
      console.log(' tableData:', tableData.value)
      console.log(' graphData:', graphData.value)
      console.log(' areas:', areas.value)
      console.log(' Plotly available:', typeof Plotly !== 'undefined')
      
      if (!hasData.value) {
        console.log('❌ No data available for chart creation')
        return
      }

      if (typeof Plotly === 'undefined') {
        console.error('❌ Plotly is not loaded!')
        return
      }

      await nextTick()
      
      // 간단한 테스트 차트 먼저 생성
      console.log(' Creating test chart...')
      await createTestChart()
      
      // 전체 차트 생성
      console.log(' Creating total chart...')
      await createTotalChart()
      
      // 각 AREA별 차트 생성
      console.log(' Creating individual area charts...')
      console.log(' chartRefs.value:', chartRefs.value)
      
      for (const area of areas.value) {
        const el = chartRefs.value[area]
        console.log(` Creating chart for ${area}:`, el)
        
        if (!el) {
          console.log(`❌ No DOM element found for area: ${area}`)
          continue
        }
        
        await createBarChart(area, el)
      }
      
      console.log('✅ All charts created')
    }

    onMounted(createAllCharts)

    // 데이터 변경 시 차트 재생성
    watch(() => props.backendData, createAllCharts, { deep: true })
    watch(parsedData, createAllCharts)
    watch(tableData, createAllCharts)
    watch(graphData, createAllCharts)
    watch(areas, createAllCharts)
    watch(() => props.height, createAllCharts)

    return {
      successMessage,
      hasData,
      areas,
      periodColumns,
      getValue,
      setChartRef,
      totalChartRef
    }
  }
})
</script>

<style scoped>
.cpk-achieve-rate-chart {
  width: 100%;
  position: relative;
}

.success-message {
  padding: 10px;
  margin-bottom: 15px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  color: #155724;
  font-size: 14px;
}

.no-data-message {
  padding: 20px;
  text-align: center;
  color: #666;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.analysis-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.table-container h3,
.charts-container h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  background-color: #f8f9fa;
  color: #333;
  font-weight: 600;
  padding: 12px 8px;
  text-align: center;
  border-bottom: 2px solid #dee2e6;
  white-space: nowrap;
}

.data-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
}

.area-cell {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
  text-align: left !important;
  padding-left: 12px !important;
}

.value-cell {
  font-weight: 500;
  color: #555;
}

.charts-container {
  width: 100%;
  margin-bottom: 30px;
}

.total-chart {
  width: 100%;
  max-width: none;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.chart-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
  text-align: center;
}

.chart-box {
  width: 100%;
  min-height: 400px;
  border: 1px solid #f1f1f1;
  border-radius: 4px;
  background: white;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .analysis-container {
    gap: 20px;
  }
  
  .chart-item {
    padding: 10px;
  }
  
  .chart-box {
    min-height: 300px;
  }
}
</style>
