<template>
  <div class="dynamic-box-chart">
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>

    <!-- FOR_KEY별 멀티 차트 컨테이너 -->
    <div class="charts-grid">
      <div
        v-for="fk in forKeyList"
        :key="fk"
        class="single-chart"
      >
        <div class="chart-title">
          {{ title }} ({{ criteria }} 기준) | FOR_KEY: {{ fk }}
        </div>
        <div class="chart-box" :ref="el => setChartRef(fk, el)"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch, computed, nextTick } from 'vue'
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
    filename: 'box_chart',
    height: 600,
    width: 800,
    scale: 1
  }
}

export default defineComponent({
  name: 'DynamicBoxChart',
  props: {
    backendData: {
      type: Object,
      default: () => ({
        result: 'inline_trend_initial',
        criteria: 'DEVICE',
        real_data: JSON.stringify([]),
        success_message: '차트가 성공적으로 생성되었습니다.'
      })
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'INLINE Trend Box Plot Chart'
    }
  },
  setup(props) {
    // 여러 개 차트 DOM을 FOR_KEY 키로 보관
    const chartRefs = ref({}) // { [forKey: string]: HTMLElement }

    const setChartRef = (forKey, el) => {
      if (!el) {
        delete chartRefs.value[forKey]
      } else {
        chartRefs.value[forKey] = el
      }
    }

    const parseNumberOrNull = (v) => {
      if (v === null || v === undefined || v === 9) return null // 9는 결측 코드
      const n = typeof v === 'string' ? Number(v) : v
      return Number.isFinite(n) ? n : null
    }

    const parsedData = computed(() => {
      try {
        const arr = JSON.parse(props.backendData.real_data) || []
        return arr.map((r) => {
          const out = { ...r }
          Object.keys(out).forEach((k) => {
            // NO_VAL1..N 숫자 변환
            if (/^NO_VAL\d+$/.test(k)) {
              out[k] = parseNumberOrNull(out[k])
            }
            // key는 문자열
            if (k === 'key') {
              out.key = String(out.key ?? '')
            }
          })
          return out
        })
      } catch (e) {
        console.error('데이터 파싱 오류:', e)
        return []
      }
    })

    const successMessage = computed(() => props.backendData.success_message || '')
    const criteria = computed(() => props.backendData.criteria || 'DEVICE')

    // NO_VAL1..N 컬럼 목록
    const noValColumns = computed(() => {
      if (parsedData.value.length === 0) return []
      const firstRow = parsedData.value[0]
      return Object.keys(firstRow)
        .filter((k) => /^NO_VAL\d+$/.test(k))
        .sort((a, b) => Number(a.replace('NO_VAL', '')) - Number(b.replace('NO_VAL', '')))
    })

    // FOR_KEY 목록 (중복 제거 + 정렬)
    const forKeyList = computed(() => {
      const all = parsedData.value
        .map((r) => r.FOR_KEY)
        .filter((v) => v !== null && v !== undefined)
        .map(String)

      const uniq = Array.from(new Set(all))

      // 자연스러운 정렬 (숫자+문자 혼합에 대해 날짜/숫자 우선, 그 외 사전순)
      return uniq.sort((a, b) => {
        const ad = new Date(a), bd = new Date(b)
        if (!isNaN(ad) && !isNaN(bd)) return ad - bd
        const an = Number(a), bn = Number(b)
        if (Number.isFinite(an) && Number.isFinite(bn)) return an - bn
        return a.localeCompare(b)
      })
    })

    const getColorPalette = () => ([
      '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
      '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
      '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
      '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
    ])

    const sortByKey = (aKey, bKey) => {
      const ad = new Date(aKey), bd = new Date(bKey)
      if (!isNaN(ad) && !isNaN(bd)) return ad - bd
      const an = Number(aKey), bn = Number(bKey)
      if (Number.isFinite(an) && Number.isFinite(bn)) return an - bn
      return String(aKey).localeCompare(String(bKey))
    }

    const buildAndPlotForGroup = async (forKey, containerEl) => {
      try {
        const groupRows = parsedData.value.filter((r) => String(r.FOR_KEY) === String(forKey))
        if (groupRows.length === 0 || !containerEl) return

        // 기존 차트 purge
        try { Plotly.purge(containerEl) } catch (_) {}

        // key 기준 정렬
        const sortedData = [...groupRows].sort((a, b) => sortByKey(String(a.key || ''), String(b.key || '')))

        // x축 카테고리
        const keys = [...new Set(sortedData.map(r => String(r.key)))].sort(sortByKey)

        // criteria 값들
        const criteriaKey = String(criteria.value) // 'DEVICE' 등
        const criteriaValues = [...new Set(sortedData.map(r => r[criteriaKey]))].filter(v => v !== null && v !== undefined)

        const traces = []
        const palette = getColorPalette()

        // criteria별 박스플롯 트레이스 - 행 단위로 유효성 검사
        criteriaValues.forEach((cVal, idx) => {
          const color = palette[idx % palette.length]
          const rows = sortedData.filter(r => r[criteriaKey] === cVal)
          const x = []
          const y = []

          rows.forEach(row => {
            // 해당 행에서 유효한 NO_VAL 값들만 수집
            const validValues = []
            noValColumns.value.forEach(noCol => {
              const v = row[noCol]
              if (v !== null && v !== undefined && Number.isFinite(Number(v))) {
                validValues.push(Number(v))
              }
            })

            // 해당 행에 유효한 값이 하나라도 있으면 모든 유효한 값들을 포함
            if (validValues.length > 0) {
              const xValue = String(row.key)
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
              name: String(cVal),
              boxpoints: false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: 0.7,
              showlegend: true,
              legendgroup: String(cVal),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hovertemplate:
                `<b>${String(cVal)}</b><br>` +
                `Key: %{x}<br>` +
                `Q1: %{q1}<br>` +
                `Median: %{median}<br>` +
                `Q3: %{q3}<br>` +
                `Min: %{lowerfence}<br>` +
                `Max: %{upperfence}<br>` +
                `Count: ${y.length}<br>` +
                `<extra></extra>`,
              hoveron: 'boxes',
              customdata: y.map((val, i) => ({ value: val, key: x[i], criteria: cVal }))
            })
          }
        })

        // 스펙 라인들 (해당 그룹의 첫 행 기준)
        const firstRow = sortedData[0] || {}

        const pushLine = (field, name, color, dash = 'solid', width = 2) => {
          if (firstRow[field] !== undefined && firstRow[field] !== null) {
            const v = Number(firstRow[field])
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

        pushLine('USL', 'USL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
        pushLine('LSL', 'LSL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
        pushLine('TGT', 'TGT', 'rgba(0, 128, 0, 0.6)', 'dash', 2)
        pushLine('UCL', 'UCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)
        pushLine('LCL', 'LCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)

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
          boxmode: 'group',
          margin: { l: 60, r: 150, t: 20, b: 100 },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest',
          boxgap: 0.1,
          boxgroupgap: 0.3
        }

        await Plotly.newPlot(containerEl, traces, layout, PlotlyConfig)
      } catch (err) {
        console.error(`[${forKey}] 차트 생성 오류:`, err)
        if (containerEl) {
          containerEl.innerHTML = `
            <div style="padding:12px;text-align:center;color:#666;">
              <h4>차트 생성 실패 (FOR_KEY: ${forKey})</h4>
              <p>${err?.message ?? err}</p>
            </div>
          `
        }
      }
    }

    const createCharts = async () => {
      // DOM이 준비된 이후 렌더
      await nextTick()
      const list = forKeyList.value

      // FOR_KEY가 전혀 없을 때 안내
      if (list.length === 0) {
        // 단일 차트 모드로의 폴백이 필요하면 여기서 구현 가능
        return
      }

      // 각 FOR_KEY 그룹별로 개별 차트 생성
      for (const fk of list) {
        const el = chartRefs.value[fk]
        await buildAndPlotForGroup(fk, el)
      }
    }

    onMounted(createCharts)

    // 데이터/옵션 변경 시 재렌더
    watch(() => props.backendData, createCharts, { deep: true })
    watch(() => props.height, createCharts)
    watch(() => props.title, createCharts)
    watch(parsedData, createCharts)
    watch(forKeyList, createCharts)

    return {
      successMessage,
      title: props.title,
      criteria: criteria,
      forKeyList,
      setChartRef
    }
  }
})
</script>

<style scoped>
.dynamic-box-chart {
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

/* 멀티 차트 레이아웃 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
  gap: 16px;
}

.single-chart {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  padding: 8px 12px 12px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 6px 4px 10px;
}

.chart-box {
  width: 100%;
  min-height: 360px;
  border: 1px solid #f1f1f1;
  border-radius: 4px;
  background: white;
}

/* 차트 로딩 상태 */
.chart-box:empty::before {
  content: "차트 로딩 중...";
  display: flex;
  align-items: center;
  justify-content: center;
  height: 360px;
  color: #666;
  font-size: 15px;
}
</style>