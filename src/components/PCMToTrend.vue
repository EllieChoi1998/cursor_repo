<template>
  <div class="pcm-to-trend">
    <!-- MAIN_ROUTE_DESC-PARA 쌍으로 그룹화된 차트들 -->
    <div v-if="groupEntries.length > 1" class="multi-para-charts">
      <div 
        v-for="(group, index) in groupEntries" 
        :key="group.key"
        class="para-chart-container"
      >
        <div class="para-chart-header">
          <h3>{{ resultTypeName }} - {{ formatGroupLabel(group) }}</h3>
          <div class="para-chart-info">
            <span class="data-count">{{ getGroupData(group).length }} records</span>
          </div>
        </div>
        <div 
          :ref="el => setChartRef(el, index)"
          class="chart-container"
        ></div>
      </div>
    </div>
    
    <!-- 단일 MAIN_ROUTE_DESC-PARA 쌍이거나 컬럼이 없는 경우 기존 로직 -->
    <div v-else class="single-chart">
      <div v-if="groupEntries.length === 1" class="para-chart-header">
        <h3>{{ resultTypeName }} - {{ formatGroupLabel(groupEntries[0]) }}</h3>
        <div class="para-chart-info">
          <span class="data-count">{{ getGroupData(groupEntries[0]).length }} records</span>
        </div>
      </div>
      <div ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch, computed, nextTick } from 'vue'
import Plotly from 'plotly.js-dist'

// Plotly 초기화 설정
const PlotlyConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
  displaylogo: false,
  scrollZoom: true,
  staticPlot: false,
  toImageButtonOptions: {
    format: 'png',
    filename: 'pcm_chart',
    height: 600,
    width: 800,
    scale: 1
  }
}

export default defineComponent({
  name: 'PCMToTrend',
  props: {
    data: {
      type: [Array, Object],
      default: () => ({
        'PARA_A': [
          {
            'Unnamed: 0.1': 1,
            'Unnamed: 0': 1,
            key: '1',
            MAIN_ROUTE_DESC: 'route1',
            MAIN_OPER_DESC: 'oper1',
            EQ_CHAM: 'P0',
            PARA: 'PARA_A',
            MIN: 380.449,
            MAX: 650.336,
            Q1: 457.749,
            Q2: 511.338,
            Q3: 611.338,
            USL: 550,
            TGT: 420,
            LSL: 300,
            UCL: 500,
            LCL: 360
          },
          {
            'Unnamed: 0.1': 2,
            'Unnamed: 0': 2,
            key: '2',
            MAIN_ROUTE_DESC: 'route2',
            MAIN_OPER_DESC: 'oper2',
            EQ_CHAM: 'P1',
            PARA: 'PARA_A',
            MIN: 395.990,
            MAX: 658.184,
            Q1: 450.449,
            Q2: 507.749,
            Q3: 605.338,
            USL: 550,
            TGT: 420,
            LSL: 300,
            UCL: 500,
            LCL: 360
          }
        ]
      })
    },
    height: {
      type: Number,
      default: 600
    },
    resultType: {
      type: String,
      default: 'sameness_to_trend'
    },
    graphName: {
      type: String,
      default: ''
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
    const columns = ['Unnamed: 0.1', 'Unnamed: 0', 'key', 'MAIN_ROUTE_DESC', 'MAIN_OPER_DESC', 'EQ_CHAM', 'PARA', 'MIN', 'MAX', 'Q1', 'Q2', 'Q3', 'USL', 'TGT', 'LSL', 'UCL', 'LCL']

    // 결과 타입에 따른 이름 매핑 (백엔드 graph_name 우선 사용)
    const resultTypeName = computed(() => {
      // 백엔드에서 graph_name이 제공되면 그것을 사용
      if (props.graphName && props.graphName.trim() !== '') {
        return props.graphName
      }
      
      // 그렇지 않으면 기존 매핑 사용 (하위 호환성)
      const typeMap = {
        'sameness_to_trend': 'Sameness to Trend',
        'commonality_to_trend': 'Commonality to Trend'
      }
      return typeMap[props.resultType] || props.resultType
    })

    const normalizeKey = (value) => {
      return value
        .toString()
        .trim()
        .toUpperCase()
        .replace(/[^A-Z0-9]/g, '')
    }

    const findKeyValue = (row, targetKey) => {
      if (!row || typeof row !== 'object') {
        return undefined
      }
      if (row[targetKey] !== undefined) {
        return row[targetKey]
      }
      const normalizedTarget = normalizeKey(targetKey)
      const keys = Object.keys(row)
      const exactMatch = keys.find(key => normalizeKey(key) === normalizedTarget)
      if (exactMatch) {
        return row[exactMatch]
      }
      const startsWithMatch = keys.find(key => normalizeKey(key).startsWith(normalizedTarget))
      if (startsWithMatch) {
        return row[startsWithMatch]
      }
      const containsMatch = keys.find(key => normalizeKey(key).includes(normalizedTarget))
      if (containsMatch) {
        return row[containsMatch]
      }
      return undefined
    }

    const extractRouteDesc = (row) => {
      const mainRoute = findKeyValue(row, 'MAIN_ROUTE_DESC')
      if (mainRoute !== undefined) {
        return mainRoute
      }
      return findKeyValue(row, 'MAIN_ROUTE')
    }

    const extractPara = (row) => {
      return findKeyValue(row, 'PARA')
    }

    const normalizeRouteDesc = (value) => {
      if (value === undefined || value === null) {
        return 'Unknown MAIN_ROUTE_DESC'
      }
      if (typeof value === 'string') {
        const trimmed = value.trim()
        return trimmed === '' ? 'Unknown MAIN_ROUTE_DESC' : trimmed
      }
      return value
    }

    const normalizePara = (value) => {
      if (value === undefined || value === null) {
        return 'Unknown PARA'
      }
      if (typeof value === 'string') {
        const trimmed = value.trim()
        return trimmed === '' ? 'Unknown PARA' : trimmed
      }
      return value
    }

    const normalizedData = computed(() => {
      if (!props.data) {
        return []
      }

      const combined = []
      const appendRow = (row, paraKey = undefined) => {
        if (!row || typeof row !== 'object') {
          return
        }
        const routeDesc = extractRouteDesc(row)
        const para = extractPara(row) ?? paraKey
        combined.push({
          ...row,
          MAIN_ROUTE_DESC: routeDesc ?? row.MAIN_ROUTE_DESC,
          PARA: para ?? row.PARA
        })
      }

      if (Array.isArray(props.data)) {
        props.data.forEach(row => appendRow(row))
        return combined
      }

      if (typeof props.data === 'object' && props.data !== null) {
        Object.entries(props.data).forEach(([paraKey, paraData]) => {
          if (Array.isArray(paraData)) {
            paraData.forEach(row => appendRow(row, paraKey))
          }
        })
        return combined
      }

      return []
    })

    const routeTypes = computed(() => {
      if (!normalizedData.value || normalizedData.value.length === 0) {
        return []
      }
      const types = new Set()
      normalizedData.value.forEach(row => {
        const routeDesc = row.MAIN_ROUTE_DESC ?? extractRouteDesc(row)
        types.add(normalizeRouteDesc(routeDesc))
      })
      return Array.from(types).sort()
    })

    const paraTypes = computed(() => {
      if (!normalizedData.value || normalizedData.value.length === 0) {
        return []
      }
      const types = new Set()
      normalizedData.value.forEach(row => {
        const para = row.PARA ?? extractPara(row)
        types.add(normalizePara(para))
      })
      return Array.from(types).sort()
    })

    // MAIN_ROUTE_DESC-PARA 쌍으로 데이터 그룹화
    const groupEntries = computed(() => {
      if (!normalizedData.value || normalizedData.value.length === 0) {
        console.log('PCMToTrend - 데이터가 없음')
        return []
      }

      const routes = routeTypes.value
      const paras = paraTypes.value
      if (routes.length === 0 || paras.length === 0) {
        return []
      }

      const entries = []
      routes.forEach(routeDesc => {
        paras.forEach(para => {
          entries.push({
            key: `${routeDesc}|||${para}`,
            routeDesc,
            para
          })
        })
      })

      console.log(
        'PCMToTrend - MAIN_ROUTE_DESC 종류:',
        routes
      )
      console.log(
        'PCMToTrend - PARA 종류:',
        paras
      )
      console.log(
        'PCMToTrend - MAIN_ROUTE_DESC/PARA 그룹 조합 수:',
        entries.length
      )
      console.log('PCMToTrend - 전체 데이터 개수:', normalizedData.value.length)
      console.log('PCMToTrend - 첫 번째 데이터 샘플:', normalizedData.value[0])

      const hasRouteCount = normalizedData.value.filter(
        row => extractRouteDesc(row) !== undefined && extractRouteDesc(row) !== null && extractRouteDesc(row) !== ''
      ).length
      const hasParaCount = normalizedData.value.filter(
        row => extractPara(row) !== undefined && extractPara(row) !== null && extractPara(row) !== ''
      ).length
      console.log(`PCMToTrend - MAIN_ROUTE_DESC 컬럼이 있는 데이터: ${hasRouteCount}/${normalizedData.value.length}`)
      console.log(`PCMToTrend - PARA 컬럼이 있는 데이터: ${hasParaCount}/${normalizedData.value.length}`)

      return entries
    })

    const formatGroupLabel = (group) => {
      return `MAIN_ROUTE_DESC: ${group.routeDesc} / PARA: ${group.para}`
    }

    const getGroupData = (group) => {
      if (!normalizedData.value || normalizedData.value.length === 0) {
        return []
      }
      const routeDesc = normalizeRouteDesc(group.routeDesc)
      const para = normalizePara(group.para)
      const groupData = normalizedData.value.filter(
        row => normalizeRouteDesc(row.MAIN_ROUTE_DESC ?? extractRouteDesc(row)) === routeDesc
          && normalizePara(row.PARA ?? extractPara(row)) === para
      )
      console.log(`PCMToTrend: MAIN_ROUTE_DESC ${routeDesc} / PARA ${para} 데이터:`, groupData)
      return groupData
    }

    const setChartRef = (el, index) => {
      if (el) {
        chartRefs.value[index] = el
      }
    }

    const createSingleChart = (container, data, chartTitle = null) => {
      if (!container || !data || data.length === 0) {
        console.log('PCMToTrend: 차트 생성 중단 - 컨테이너 또는 데이터가 없음')
        return
      }

      console.log(`PCMToTrend 차트 생성: ${chartTitle || 'Default'} - ${data.length}개 데이터`)

      try {
        // 데이터를 key 순서대로 정렬
        const sortedData = data.sort((a, b) => {
          // key가 숫자인 경우 숫자로 정렬, 문자열인 경우 문자열로 정렬
          const aKey = a.key
          const bKey = b.key
          
          if (!isNaN(aKey) && !isNaN(bKey)) {
            return Number(aKey) - Number(bKey)
          }
          return aKey.toString().localeCompare(bKey.toString())
        })

        // Extract data for box plots and control lines
        const keys = sortedData.map(row => row.key)
        const usls = sortedData.map(row => row.USL)
        const tgts = sortedData.map(row => row.TGT)
        const lsls = sortedData.map(row => row.LSL)
        const ucls = sortedData.map(row => row.UCL)
        const lcls = sortedData.map(row => row.LCL)

        // Create box plot traces for each EQ_CHAM (PCMTrendChart 방식 사용)
        const eqChamTypes = [...new Set(sortedData.map(row => row.EQ_CHAM))]
        const boxTraces = []
        
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
        
        eqChamTypes.forEach(eqCham => {
          const eqChamData = sortedData.filter(row => row.EQ_CHAM === eqCham)
          
          // Generate box plot data for each key point
          const allBoxData = []
          const allLabels = []
          
          eqChamData.forEach(row => {
            const boxData = generateBoxPlotData(
              row.MIN, 
              row.Q1, 
              row.Q2, 
              row.Q3, 
              row.MAX
            )
            allBoxData.push(...boxData)
            allLabels.push(...Array(boxData.length).fill(row.key))
          })

          boxTraces.push({
            type: 'box',
            x: allLabels,
            y: allBoxData,
            name: `EQ_CHAM ${eqCham}`,
            boxpoints: 'outliers',
            jitter: 0.3,
            pointpos: -1.8,
            marker: {
              color: getEqChamColor(eqCham),
              size: 4
            },
            line: {
              color: getEqChamColor(eqCham),
              width: 2
            },
            fillcolor: getEqChamColor(eqCham, 0.4),
            showlegend: true
          })
        })

        // Create scatter traces for control lines
        const scatterTraces = [
          {
            type: 'scatter',
            x: keys,
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
            x: keys,
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
            x: keys,
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
            x: keys,
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
            x: keys,
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

        // Calculate optimal tick interval for x-axis
        const calculateTickInterval = (totalKeys) => {
          if (totalKeys <= 20) return 1
          if (totalKeys <= 50) return 5
          if (totalKeys <= 100) return 10
          if (totalKeys <= 200) return 20
          if (totalKeys <= 500) return 50
          return Math.ceil(totalKeys / 10)
        }

        const tickInterval = calculateTickInterval(keys.length)
        const tickIndices = []
        for (let i = 0; i < keys.length; i += tickInterval) {
          tickIndices.push(i)
        }
        // Always include the last index if it's not already included
        if (tickIndices[tickIndices.length - 1] !== keys.length - 1) {
          tickIndices.push(keys.length - 1)
        }

        const filteredTickVals = tickIndices.map(i => keys[i])
        const filteredTickText = tickIndices.map(i => keys[i].toString())

        console.log(`PCMToTrend - X-axis tick 설정:`, {
          totalKeys: keys.length,
          tickInterval: tickInterval,
          tickIndices: tickIndices,
          filteredTickVals: filteredTickVals
        })

        // Combine all traces
        const allTraces = [...boxTraces, ...scatterTraces]

        // Layout configuration (PCMTrendChart와 동일한 구조)
        const layout = {
          title: {
            text: chartTitle || `${resultTypeName.value} EQ-Ch 별 Trend`,
            font: {
              size: 16,
              color: '#333'
            }
          },
          xaxis: {
            title: 'Key',
            type: 'category',
            showgrid: true,
            gridcolor: '#f0f0f0',
            showticklabels: true,
            tickangle: 90,
            tickmode: 'array',
            tickvals: filteredTickVals,
            ticktext: filteredTickText,
            tickfont: {
              size: 10,
              color: '#333'
            },
            side: 'bottom',
            tickposition: 'outside',
            categoryorder: 'array',
            categoryarray: keys
          },
          yaxis: {
            title: 'Values',
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

        // Plot the chart (PCMTrendPointChart와 동일한 방식)
        console.log('PCMToTrend - Plotly 차트 생성 시도:', {
          container: container,
          tracesCount: allTraces.length,
          dataLength: data.length,
          eqChamTypes: eqChamTypes
        })
        
        // DOM이 완전히 준비된 후 차트 생성
        setTimeout(() => {
          try {
            Plotly.newPlot(container, allTraces, layout, PlotlyConfig).then(() => {
              console.log('PCMToTrend - Plotly 차트 생성 완료')
            }).catch(error => {
              console.error('PCMToTrend - Plotly 차트 생성 오류:', error)
              // 오류 발생 시 대체 콘텐츠 표시
              container.innerHTML = `<div style="padding: 20px; text-align: center; color: #666;">
                <h4>차트 생성에 실패했습니다</h4>
                <p>오류: ${error.message}</p>
                <p>데이터: ${data.length}개 항목</p>
              </div>`
            })
          } catch (syncError) {
            console.error('PCMToTrend - 동기 차트 생성 오류:', syncError)
            container.innerHTML = `<div style="padding: 20px; text-align: center; color: #666;">
              <h4>차트 초기화에 실패했습니다</h4>
              <p>오류: ${syncError.message}</p>
            </div>`
          }
        }, 100) // 100ms 지연으로 DOM 안정화

      } catch (error) {
        console.error('PCMToTrend: 차트 생성 중 오류 발생:', error)
        // 오류 발생 시 간단한 메시지 표시
        container.innerHTML = `<div style="padding: 20px; text-align: center; color: #666;">
          <p>차트 생성 중 오류가 발생했습니다.</p>
          <p>${error.message}</p>
        </div>`
      }
    }

    const createCharts = async () => {
      try {
        // 데이터가 없거나 유효하지 않으면 차트 생성하지 않음
        if (!props.data) {
          console.log('PCMToTrend: 데이터가 없어서 차트 생성 중단')
          return
        }

        console.log('PCMToTrend: 차트 생성 시작 - 데이터 타입:', typeof props.data)
        console.log('PCMToTrend: 데이터 내용:', props.data)

        if (!normalizedData.value || normalizedData.value.length === 0) {
          console.log('PCMToTrend: 정규화된 데이터가 없어 차트 생성 중단')
          return
        }

        // 모든 기존 차트 정리 (더 안전한 방식)
        if (chartContainer.value) {
          try {
            // Plotly 차트가 있는지 확인 후 정리
            if (chartContainer.value._fullLayout) {
              Plotly.purge(chartContainer.value)
            } else {
              // Plotly 차트가 없으면 직접 내용 제거
              chartContainer.value.innerHTML = ''
            }
          } catch (error) {
            console.warn('PCMToTrend: 기존 차트 정리 중 오류:', error)
            // 오류 발생 시 강제로 내용 제거
            chartContainer.value.innerHTML = ''
          }
        }
        
        chartRefs.value.forEach(ref => {
          if (ref) {
            try {
              if (ref._fullLayout) {
                Plotly.purge(ref)
              } else {
                ref.innerHTML = ''
              }
            } catch (error) {
              console.warn('PCMToTrend: 기존 차트 참조 정리 중 오류:', error)
              ref.innerHTML = ''
            }
          }
        })

        await nextTick()

        if (groupEntries.value.length > 1) {
          // 여러 MAIN_ROUTE_DESC-PARA 쌍이 있는 경우 각각 차트 생성
          console.log(`PCMToTrend: ${groupEntries.value.length}개의 MAIN_ROUTE_DESC-PARA 쌍별 차트 생성`, groupEntries.value)
          groupEntries.value.forEach((group, index) => {
            const groupData = getGroupData(group)
            console.log(`PCMToTrend: MAIN_ROUTE_DESC ${group.routeDesc} / PARA ${group.para} 데이터 개수: ${groupData.length}`)

            const container = chartRefs.value[index]
            if (container) {
              if (groupData.length === 0) {
                console.warn(`PCMToTrend: MAIN_ROUTE_DESC ${group.routeDesc} / PARA ${group.para}에 데이터가 없음`)
                container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">데이터가 없습니다.</div>'
                return
              }
              createSingleChart(container, groupData, `${resultTypeName.value} - ${formatGroupLabel(group)}`)
            } else {
              console.warn(`PCMToTrend: MAIN_ROUTE_DESC ${group.routeDesc} / PARA ${group.para}의 차트 컨테이너를 찾을 수 없음`)
            }
          })
        } else {
          // 단일 MAIN_ROUTE_DESC-PARA 쌍 또는 컬럼이 없는 경우
          console.log('PCMToTrend: 단일 차트 생성, MAIN_ROUTE_DESC-PARA 그룹:', groupEntries.value)
          if (chartContainer.value) {
            let dataToUse
            if (groupEntries.value.length === 1) {
              const firstGroup = groupEntries.value[0]
              dataToUse = getGroupData(firstGroup)
              console.log(`PCMToTrend: MAIN_ROUTE_DESC ${firstGroup.routeDesc} / PARA ${firstGroup.para}의 데이터 사용:`, dataToUse.length)
            } else {
              dataToUse = normalizedData.value
              console.log('PCMToTrend: 전체 데이터 사용:', dataToUse.length)
            }
            
            if (dataToUse.length > 0) {
              createSingleChart(chartContainer.value, dataToUse, resultTypeName.value)
            } else {
              console.warn('PCMToTrend: 사용할 데이터가 없음')
              chartContainer.value.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">데이터가 없습니다.</div>'
            }
          }
        }
      } catch (error) {
        console.error('PCMToTrend: 차트 생성 중 오류 발생:', error)
        // 오류 발생 시 모든 차트 컨테이너에 오류 메시지 표시
        if (chartContainer.value) {
          chartContainer.value.innerHTML = `<div style="padding: 20px; text-align: center; color: #666;">
            <p>차트 생성 중 오류가 발생했습니다.</p>
            <p>${error.message}</p>
          </div>`
        }
        
        chartRefs.value.forEach(ref => {
          if (ref) {
            ref.innerHTML = `<div style="padding: 20px; text-align: center; color: #666;">
              <p>차트 생성 중 오류가 발생했습니다.</p>
              <p>${error.message}</p>
            </div>`
          }
        })
      }
    }

    // Helper function to get colors for different EQ_CHAM
    const getEqChamColor = (eqCham, alpha = 1) => {
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
      
      const getEqChamIndex = (eqChamName) => {
        let hash = 0
        for (let i = 0; i < eqChamName.toString().length; i++) {
          const char = eqChamName.toString().charCodeAt(i)
          hash = ((hash << 5) - hash) + char
          hash = hash & hash
        }
        return Math.abs(hash) % colorPalette.length
      }
      
      const colorIndex = getEqChamIndex(eqCham)
      const [r, g, b] = colorPalette[colorIndex]
      
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    onMounted(() => {
      console.log('PCMToTrend 마운트됨 - 기본 데이터:', props.data)
      console.log('PCMToTrend 마운트됨 - MAIN_ROUTE_DESC/PARA 그룹들:', groupEntries.value)
      createCharts()
    })

    watch(() => props.data, createCharts, { deep: true })
    watch(() => props.height, createCharts)
    watch(() => props.resultType, createCharts)
    watch(() => props.maxLabels, createCharts)
    watch(() => props.dataSampling, createCharts)

    return {
      chartContainer,
      chartRefs,
      normalizedData,
      groupEntries,
      resultTypeName,
      formatGroupLabel,
      getGroupData,
      setChartRef
    }
  }
})
</script>

<style scoped>
.pcm-to-trend {
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