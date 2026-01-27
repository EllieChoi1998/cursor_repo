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

    // real_data 파싱 - IQC는 FOR_KEY별로 추가 분할
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
        
        const chartList = []
        let chartIndex = 0
        
        data.forEach((item) => {
          const type = (item.type || '').toUpperCase()
          const graphData = item.graph_data || []
          const sortCriteria = normalizeSortCriteria(item.sort_criteria || item.sortCriteria)
          
          if (type === 'IQC' && graphData.length > 0) {
            // IQC의 경우: FOR_KEY별로 차트를 분할
            const forKeys = [...new Set(graphData.map(row => row.FOR_KEY))].filter(k => k !== null && k !== undefined)
            
            forKeys.forEach(forKey => {
              // FOR_KEY로 데이터 필터링
              const filteredData = graphData.filter(row => row.FOR_KEY === forKey)
              
              if (filteredData.length === 0) return
              
              // FOR_KEY를 파싱하여 title 정보 추출
              const forKeyParts = String(forKey).split('-')
              const para = forKeyParts[0] || ''
              const noVal = forKeyParts[1] || ''
              const usl = forKeyParts[2] || ''
              const tgt = forKeyParts[3] || ''
              const lsl = forKeyParts[4] || ''
              
              // title 생성
              const routeDesc = filteredData[0]?.ROUTE_DESC || ''
              const oper = filteredData[0]?.OPER || filteredData[0]?.OPN || ''
              const title = `IQC Trend - ${routeDesc} (${oper}) : ${para} (${usl} : ${lsl})`
              
              chartList.push({
                type: 'IQC',
                graph_data: filteredData,
                selected_row_data: item.selected_row_data,
                title,
                index: chartIndex++,
                forKey,
                usl,
                lsl,
                tgt,
                sort_criteria: sortCriteria
              })
            })
          } else if (type === 'EQC') {
            // EQC의 경우: 하나의 차트만 생성
            const selectedRow = Array.isArray(item.selected_row_data) && item.selected_row_data.length > 0 
              ? item.selected_row_data[0] 
              : {}
            
            console.log('🔍 EQC selected_row_data:', selectedRow)
            
            // selected_row_data와 graph_data의 첫 행에서 값 찾기
            const firstGraphRow = graphData.length > 0 ? graphData[0] : {}
            
            const area = selectedRow.AREA || firstGraphRow.AREA || 'EQC'
            const routeDesc = selectedRow.ROUTE_DESC || firstGraphRow.ROUTE_DESC || ''
            const para = selectedRow.PARA || selectedRow.PARAMETER || firstGraphRow.PARA || firstGraphRow.PARAMETER || ''
            const usl = selectedRow.USL || firstGraphRow.USL || ''
            const lsl = selectedRow.LSL || firstGraphRow.LSL || ''
            const title = `${area} Trend - ${routeDesc} : ${para} (${usl} : ${lsl})`
            
            console.log('🔍 EQC title:', title)
            
            chartList.push({
              ...item,
              title,
              index: chartIndex++,
              usl,
              lsl,
              sort_criteria: sortCriteria
            })
          } else {
            // 기타 타입
            chartList.push({
              ...item,
              title: `${type} Trend Chart ${chartIndex}`,
              index: chartIndex++,
              sort_criteria: sortCriteria
            })
          }
        })
        
        return chartList
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

    const normalizeSortCriteria = (value) => {
      if (!value) return 'TIMELY'
      const upper = String(value).toUpperCase()
      return upper === 'EQ' ? 'EQ' : 'TIMELY'
    }

    const hasFieldValue = (rows, field) => rows.some(row => (
      row && row[field] !== undefined && row[field] !== null && row[field] !== ''
    ))

    const resolveSortFields = (rows, sortCriteria) => {
      if (sortCriteria === 'EQ') {
        return { sortValueField: 'MAIN_EQ', sortColorField: 'MAIN_EQ' }
      }
      const sortValueField = hasFieldValue(rows, 'TRANS_DATE')
        ? 'TRANS_DATE'
        : (hasFieldValue(rows, 'EQMNT_DATE') ? 'EQMNT_DATE' : 'TRANS_DATE')
      const sortColorField = hasFieldValue(rows, 'DEVICE') ? 'DEVICE' : 'MAIN_EQ'
      return { sortValueField, sortColorField }
    }

    const resolveMainEq = (row) => {
      if (!row) return undefined
      let mainEq = row.MAIN_EQ
      if (!mainEq && row['EQUIP ID']) {
        mainEq = row['EQUIP ID'] + (row['SUB EQUIP ID'] ? `+${row['SUB EQUIP ID']}` : '')
      }
      return mainEq
    }

    // IQC 차트 생성 (FOR_KEY로 이미 필터링된 데이터)
    const createIQCChart = (item, containerEl) => {
      try {
        const graphData = item.graph_data || []
        const sortCriteria = normalizeSortCriteria(item?.sort_criteria || item?.sortCriteria)

        if (graphData.length === 0 || !containerEl) return

        // key 생성: TIMELY는 TRANS_DATE + WAFER_ID, EQ는 MAIN_EQ
        const dataWithKeys = graphData.map(row => {
          const mainEq = resolveMainEq(row)
          if (sortCriteria === 'EQ') {
            const key = mainEq ?? row.MAIN_EQ ?? row.key ?? ''
            return { ...row, MAIN_EQ: mainEq ?? row.MAIN_EQ, key }
          }

          // 기존 key가 있어도 무시하고 무조건 새로 생성
          if (row.TRANS_DATE && row.WAFER_ID) {
            // TRANS_DATE 포맷 변환
            let dateStr = row.TRANS_DATE
            let dateObj = null
            
            // 1. 숫자(timestamp)인 경우 - Unix timestamp (밀리초)
            if (typeof dateStr === 'number') {
              dateObj = new Date(dateStr)
            }
            // 2. Date 객체인 경우
            else if (dateStr instanceof Date) {
              dateObj = dateStr
            }
            // 3. 문자열인 경우
            else if (typeof dateStr === 'string') {
              // "2025-01-15" 또는 "2025/01/15" 같은 형식을 "25-01-15"로 변환
              const parts = dateStr.split(/[-\/T ]/)
              if (parts.length >= 3) {
                const year = parts[0].length === 4 ? parts[0].slice(-2) : parts[0]
                const month = parts[1].padStart(2, '0')
                const day = parts[2].padStart(2, '0')
                dateStr = `${year}-${month}-${day}`
              }
            }
            
            // Date 객체가 생성되었으면 포맷팅
            if (dateObj && !isNaN(dateObj.getTime())) {
              const year = String(dateObj.getFullYear()).slice(-2)
              const month = String(dateObj.getMonth() + 1).padStart(2, '0')
              const day = String(dateObj.getDate()).padStart(2, '0')
              dateStr = `${year}-${month}-${day}`
            }
            
            return { ...row, MAIN_EQ: mainEq ?? row.MAIN_EQ, key: `${dateStr}-${row.WAFER_ID}` }
          }
          // TRANS_DATE나 WAFER_ID가 없으면 원본 반환
          return { ...row, MAIN_EQ: mainEq ?? row.MAIN_EQ }
        })

        const { sortValueField, sortColorField } = resolveSortFields(dataWithKeys, sortCriteria)

        // Python과 동일한 정렬: TIMELY => TRANS_DATE, EQ => MAIN_EQ
        const sortedData = [...dataWithKeys].sort((a, b) => {
          // 1. sort_value 비교
          if (sortValueField === 'MAIN_EQ') {
            const eqA = String(a.MAIN_EQ || '')
            const eqB = String(b.MAIN_EQ || '')
            if (eqA !== eqB) return eqA.localeCompare(eqB, undefined, { numeric: true, sensitivity: 'base' })
          } else {
            const dateA = String(a[sortValueField] || '')
            const dateB = String(b[sortValueField] || '')
            if (dateA !== dateB) return dateA.localeCompare(dateB)
          }
          
          // 2. WAFER_ID 비교
          const waferA = String(a.WAFER_ID || '')
          const waferB = String(b.WAFER_ID || '')
          if (waferA !== waferB) return waferA.localeCompare(waferB)
          
          // 3. USL 비교
          const uslA = Number(a.USL) || 0
          const uslB = Number(b.USL) || 0
          if (uslA !== uslB) return uslA - uslB
          
          // 4. TGT 비교
          const tgtA = Number(a.TGT) || 0
          const tgtB = Number(b.TGT) || 0
          if (tgtA !== tgtB) return tgtA - tgtB
          
          // 5. LSL 비교
          const lslA = Number(a.LSL) || 0
          const lslB = Number(b.LSL) || 0
          return lslA - lslB
        })

        // x축 카테고리 (key 값들)
        const keys = [...new Set(sortedData.map(r => String(r.key || '')))]

        // 정렬/색상 기준별 그룹 값들 추출
        const groupValues = [...new Set(sortedData.map(r => r?.[sortColorField]))]
          .filter(v => v !== null && v !== undefined)
        
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

        console.log('📊 IQC Chart Info:')
        console.log('  - Sort criteria:', sortCriteria, `(${sortValueField}/${sortColorField})`)
        console.log('  - Keys count:', keys.length, keys)
        console.log('  - Groups:', groupValues)
        console.log('  - NO_VAL columns:', noValColumns)
        console.log('  - Total rows:', sortedData.length)
        console.log('  - Sample row (first):', sortedData[0])
        console.log('  - Has key field?', sortedData[0]?.key)
        console.log('  - Has sort color field?', sortedData[0]?.[sortColorField])
        console.log('  - Sample NO_VAL1:', sortedData[0]?.NO_VAL1)

        const traces = []
        const palette = getColorPalette()

        // px.box(y=[col1, col2, ...], color=sort_color)와 동일하게 동작하도록
        // 각 key 위치에서 그룹별로 하나의 박스플롯 생성
        groupValues.forEach((groupValue, idx) => {
          const color = palette[idx % palette.length]
          const x = []
          const y = []
          
          console.log(`\n🔍 Processing group: "${groupValue}"`)
          
          // 각 x 위치(key)별로 데이터 수집
          keys.forEach((keyValue, keyIdx) => {
            // 해당 key와 device를 가진 행들 찾기
            const matchingRows = sortedData.filter(r => 
              String(r.key) === keyValue && r?.[sortColorField] === groupValue
            )
            
            if (keyIdx === 0) {
              // 첫 번째 키에서만 자세히 로깅
              console.log(`  Testing key "${keyValue}" with group "${groupValue}":`)
              console.log(`    - Matching rows: ${matchingRows.length}`)
              if (matchingRows.length === 0) {
                // 매칭 실패 원인 파악
                const sameKeyRows = sortedData.filter(r => String(r.key) === keyValue)
                const sameGroupRows = sortedData.filter(r => r?.[sortColorField] === groupValue)
                console.log(`    - Rows with same key: ${sameKeyRows.length}`)
                console.log(`    - Rows with same group: ${sameGroupRows.length}`)
                if (sameKeyRows.length > 0) {
                  console.log(`    - Sample row's group:`, sameKeyRows[0]?.[sortColorField], `(type: ${typeof sameKeyRows[0]?.[sortColorField]})`)
                  console.log(`    - Looking for group:`, groupValue, `(type: ${typeof groupValue})`)
                }
              }
            }
            
            // 해당 행들의 모든 NO_VAL 값들 수집
            matchingRows.forEach(row => {
              noValColumns.forEach(noCol => {
                const v = row[noCol]
                if (v !== null && v !== undefined && v !== 9 && Number.isFinite(Number(v))) {
                  y.push(Number(v))
                  x.push(keyValue)
                }
              })
            })
          })

          console.log(`  ✅ Total data points for ${groupValue}: ${y.length}`)
          console.log(`  Sample y values:`, y.slice(0, 5))

          if (y.length > 0) {
            traces.push({
              type: 'box',
              x,
              y,
              name: String(groupValue),
              boxpoints: false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: 0.7,
              showlegend: true,
              legendgroup: String(groupValue),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hoveron: 'boxes'
            })
          } else {
            console.warn(`  ⚠️ No data points for group ${groupValue}`)
          }
        })
        
        console.log(`\n📊 Total traces created: ${traces.length}`)

        // 스펙 라인 추가 (USL, LSL, TGT) - chartDataList에서 파싱된 값 사용
        const pushLine = (value, name, color, dash = 'solid', width = 2) => {
          if (value !== undefined && value !== null && value !== '') {
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

        // FOR_KEY에서 파싱된 USL, LSL, TGT 값 사용
        pushLine(item.usl, 'USL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(item.lsl, 'LSL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(item.tgt, 'TGT', 'rgba(0, 0, 0, 0.5)', 'dash', 2)

        const layout = {
          xaxis: {
            title: { text: sortValueField === 'MAIN_EQ' ? 'MAIN_EQ' : 'Date-Wafer', font: { size: 12 } },
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
        console.log('✅ IQC Chart created successfully')
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
        const sortCriteria = normalizeSortCriteria(item?.sort_criteria || item?.sortCriteria)
        const selectedRow = Array.isArray(item.selected_row_data) && item.selected_row_data.length > 0 
          ? item.selected_row_data[0] 
          : {}

        if (graphData.length === 0 || !containerEl) return

        // key 생성: TIMELY는 EQMNT_DATE + MAIN_EQ, EQ는 MAIN_EQ
        const dataWithKeys = graphData.map(row => {
          // 기존 key가 있어도 무시하고 무조건 새로 생성
          const mainEq = resolveMainEq(row)
          if (sortCriteria === 'EQ') {
            const key = mainEq ?? row.MAIN_EQ ?? row.key ?? ''
            return { ...row, key, MAIN_EQ: mainEq ?? row.MAIN_EQ }
          }

          const dateSource = row.EQMNT_DATE ?? row.TRANS_DATE
          if (dateSource) {
            // MAIN_EQ 생성 (백엔드에서 없을 경우)
            const resolvedMainEq = mainEq ?? row.MAIN_EQ
            
            // EQMNT_DATE 포맷 변환
            let dateStr = dateSource
            let dateObj = null
            
            // 1. 숫자(timestamp)인 경우 - Unix timestamp (밀리초)
            if (typeof dateStr === 'number') {
              dateObj = new Date(dateStr)
            }
            // 2. Date 객체인 경우
            else if (dateStr instanceof Date) {
              dateObj = dateStr
            }
            // 3. 문자열인 경우
            else if (typeof dateStr === 'string') {
              // 숫자 문자열이면 timestamp로 변환
              if (/^\d+$/.test(dateStr)) {
                dateObj = new Date(Number(dateStr))
              } else {
                // "2025-01-15" 형식은 그대로 사용
                dateStr = dateStr
              }
            }
            
            // Date 객체가 생성되었으면 YYYY-MM-DD 형식으로 변환
            if (dateObj && !isNaN(dateObj.getTime())) {
              const year = dateObj.getFullYear()
              const month = String(dateObj.getMonth() + 1).padStart(2, '0')
              const day = String(dateObj.getDate()).padStart(2, '0')
              dateStr = `${year}-${month}-${day}`
            }
            
            return { ...row, key: `${dateStr}-${resolvedMainEq || ''}`, MAIN_EQ: resolvedMainEq }
          }
          // EQMNT_DATE가 없으면 원본 반환
          return { ...row, MAIN_EQ: mainEq ?? row.MAIN_EQ }
        })

        const { sortValueField, sortColorField } = resolveSortFields(dataWithKeys, sortCriteria)

        // 정렬 기준
        const sortedData = [...dataWithKeys].sort((a, b) => {
          if (sortValueField === 'MAIN_EQ') {
            const eqA = String(a.MAIN_EQ || '')
            const eqB = String(b.MAIN_EQ || '')
            if (eqA !== eqB) return eqA.localeCompare(eqB, undefined, { numeric: true, sensitivity: 'base' })
          }
          const dateField = sortValueField === 'TRANS_DATE' ? 'TRANS_DATE' : 'EQMNT_DATE'
          const dateA = String(a[dateField] || '')
          const dateB = String(b[dateField] || '')
          return dateA.localeCompare(dateB)
        })

        // x축 카테고리 (key 값들)
        const keys = [...new Set(sortedData.map(r => String(r.key || '')))]

        // 정렬/색상 기준별 그룹 값들 추출
        const groupValues = [...new Set(sortedData.map(r => r?.[sortColorField]))]
          .filter(v => v !== null && v !== undefined)
        
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

        // 그룹별 박스플롯 생성
        groupValues.forEach((groupValue, idx) => {
          const color = palette[idx % palette.length]
          const eqRows = sortedData.filter(r => r?.[sortColorField] === groupValue)
          
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
              name: String(groupValue),
              boxpoints: false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: 0.7,
              showlegend: true,
              legendgroup: String(groupValue),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hoveron: 'boxes'
            })
          }
        })

        // 스펙 라인 추가 (USL, LSL만)
        const pushLine = (value, name, color, dash = 'solid', width = 2) => {
          if (value !== undefined && value !== null && value !== '') {
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

        // USL, LSL 값 가져오기 - chartDataList에서 파싱된 값 사용
        pushLine(item.usl, 'USL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)
        pushLine(item.lsl, 'LSL', 'rgba(0, 0, 0, 0.8)', 'solid', 2)

        const layout = {
          xaxis: {
            title: { text: sortValueField === 'MAIN_EQ' ? 'MAIN_EQ' : 'EQMNT_DATE-MAIN_EQ', font: { size: 12 } },
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
  content: "트렌드 데이터 찾을 수 없음";
  display: flex;
  align-items: center;
  justify-content: center;
  height: 500px;
  color: #999;
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
