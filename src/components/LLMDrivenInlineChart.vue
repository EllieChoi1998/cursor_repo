<template>
  <div class="llm-plotly">
    <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

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

    <!-- 오류/디버그 -->
    <div v-if="errorMessage" class="error-box">
      <strong>차트 생성 실패:</strong> {{ errorMessage }}
      <details>
        <summary>디버그</summary>
        <pre>{{ debugInfo }}</pre>
      </details>
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
    filename: 'llm_box_chart',
    height: 600,
    width: 800,
    scale: 1
  }
}

export default defineComponent({
  name: 'LLMDrivenInlineChart',
  props: {
    backendData: {
      type: Object,
      default: () => ({
        // 예시 형태:
        // real_data: JSON.stringify([...rows]),
        // llm_spec: { ... },
        success_message: ''
      })
    },
    height: { type: Number, default: 600 },
    title: { type: String, default: 'LLM-Driven Inline Chart' }
  },
  setup(props) {
    // 여러 개 차트 DOM을 FOR_KEY 키로 보관
    const chartRefs = ref({}) // { [forKey: string]: HTMLElement }
    const errorMessage = ref('')
    const debugInfo = ref('')

    const setChartRef = (forKey, el) => {
      if (!el) {
        delete chartRefs.value[forKey]
      } else {
        chartRefs.value[forKey] = el
      }
    }

    const successMessage = computed(() => props.backendData.success_message || '')

    // ---- 파서들 ----
    const parseJSONLoose = (v) => {
      if (v == null) return null
      if (typeof v === 'object') return v
      if (typeof v !== 'string') return null
      const s = v.trim()
      if (!s) return null
      // 코드펜스 제거
      const m = s.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i)
      const body = m ? m[1].trim() : s
      try { return JSON.parse(body) } catch (_) { return null }
    }

    const rows = computed(() => {
      try {
        const arr = parseJSONLoose(props.backendData.real_data) || []
        return arr.map(r => {
          const out = { ...r }
          // key는 문자열
          out.key = String(out.key ?? '')
          // NO_VALn 숫자 정리 (9 => null)
          Object.keys(out).forEach(k => {
            if (/^NO_VAL\d+$/.test(k)) {
              const v = out[k]
              if (v === 9 || v === null || v === undefined) { out[k] = null }
              else {
                const n = typeof v === 'string' ? Number(v) : v
                out[k] = Number.isFinite(n) ? n : null
              }
            }
          })
          return out
        })
      } catch (e) {
        console.error('real_data 파싱 오류:', e)
        return []
      }
    })

    const spec = computed(() => {
      // object 또는 string(JSON) 둘 다 허용
      const s = parseJSONLoose(props.backendData.llm_spec) || props.backendData.llm_spec
      return typeof s === 'object' && s ? s : {}
    })

    // spec에서 criteria 추출 (없으면 'DEVICE' 기본값)
    const criteria = computed(() => {
      return spec.value.group_by || spec.value.criteria || 'DEVICE'
    })

    // NO_VAL1..N 컬럼 목록
    const noValColumns = computed(() => {
      if (rows.value.length === 0) return []
      const firstRow = rows.value[0]
      return Object.keys(firstRow)
        .filter((k) => /^NO_VAL\d+$/.test(k))
        .sort((a, b) => Number(a.replace('NO_VAL', '')) - Number(b.replace('NO_VAL', '')))
    })

    // ---- 필터 적용 ----
    const applyFilters = (data, filters = []) => {
        console.log('Applying filters:', filters) // 디버깅용
      if (!Array.isArray(filters) || filters.length === 0) return data
      
      console.log('Applying filters:', filters) // 디버깅용
      console.log('Original data count:', data.length)

      const result = data.filter(row => {
        for (const f of filters) {
          if (!f || typeof f !== 'object') continue
          const field = f.field
          const op = f.op
          const val = f.value
          const rowValue = row[field]

          console.log(`Checking filter: ${field} ${op} ${val}, row value: ${rowValue}`) // 디버깅용

          // 숫자 필드의 경우 숫자로 비교
          if (/^NO_VAL\d+$/.test(field)) {
            const numRowValue = Number(rowValue)
            const numFilterValue = Number(val)
            
            if (op === '==' || op === '=') {
              if (numRowValue !== numFilterValue) {
                console.log(`Filter rejected: ${numRowValue} !== ${numFilterValue}`)
                return false
              }
            } else if (op === '!=' || op === '!=') {
              if (numRowValue === numFilterValue) {
                console.log(`Filter rejected: ${numRowValue} === ${numFilterValue}`)
                return false
              }
            } else if (op === '>') {
              if (numRowValue <= numFilterValue) return false
            } else if (op === '>=') {
              if (numRowValue < numFilterValue) return false
            } else if (op === '<') {
              if (numRowValue >= numFilterValue) return false
            } else if (op === '<=') {
              if (numRowValue > numFilterValue) return false
            } else if (op === 'between') {
              // value: [min, max] 또는 {min, max}
              let min = null, max = null
              if (Array.isArray(val)) {
                min = val[0]; max = val[1]
              } else if (val && typeof val === 'object') {
                min = val.min; max = val.max
              }
              if (!Number.isFinite(numRowValue)) return false
              if (min != null && numRowValue < Number(min)) return false
              if (max != null && numRowValue > Number(max)) return false
            }
          } else {
            // 문자열 필드의 경우 문자열로 비교
            const norm = (x) => (typeof x === 'string' ? x.trim() : String(x))
            const lhs = norm(rowValue)
            const rhs = norm(val)

            if (op === '==' || op === '=') {
              if (lhs !== rhs) return false
            } else if (op === '!=' || op === '!=') {
              if (lhs === rhs) return false
            } else if (op === 'in') {
              if (!Array.isArray(val) || !val.map(norm).includes(lhs)) return false
            }
          }
        }
        return true
      })

      console.log('Filtered data count:', result.length) // 디버깅용
      return result
    }

    // FOR_KEY 목록 (중복 제거 + 정렬)
    const forKeyList = computed(() => {
      const filtered = applyFilters(rows.value, spec.value.filters)
      const all = filtered
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

    const sortByKey = (aKey, bKey) => {
      const ad = new Date(aKey), bd = new Date(bKey)
      if (!isNaN(ad) && !isNaN(bd)) return ad - bd
      const an = Number(aKey), bn = Number(bKey)
      if (Number.isFinite(an) && Number.isFinite(bn)) return an - bn
      return String(aKey).localeCompare(String(bKey))
    }

    // layout_patches 적용: "xaxis.tickangle": 90 형태를 안전히 반영
    const applyLayoutPatches = (layout, patches = {}) => {
      if (!patches || typeof patches !== 'object') return layout
      for (const [path, value] of Object.entries(patches)) {
        const parts = path.split('.')
        let ref = layout
        for (let i = 0; i < parts.length; i++) {
          const p = parts[i]
          if (i === parts.length - 1) {
            ref[p] = value
          } else {
            if (!(p in ref) || typeof ref[p] !== 'object') ref[p] = {}
            ref = ref[p]
          }
        }
      }
      return layout
    }

    const buildAndPlotForGroup = async (forKey, containerEl) => {
      try {
        const filtered = applyFilters(rows.value, spec.value.filters)
        const groupRows = filtered.filter((r) => String(r.FOR_KEY) === String(forKey))
        
        if (groupRows.length === 0 || !containerEl) return

        // 기존 차트 purge
        try { Plotly.purge(containerEl) } catch (_) {}

        const s = spec.value || {}
        const xField = s.x_field || 'key'

        // key 기준 정렬
        const sortedData = [...groupRows].sort((a, b) => sortByKey(String(a[xField] || ''), String(b[xField] || '')))

        // x축 카테고리
        const keys = [...new Set(sortedData.map(r => String(r[xField] || '')))].sort(sortByKey)

        // criteria 값들 (INLINETrendChart와 동일한 로직)
        const criteriaKey = String(criteria.value) // 'DEVICE' 등
        const criteriaValues = [...new Set(sortedData.map(r => r[criteriaKey]))].filter(v => v !== null && v !== undefined)

        const traces = []
        const palette = [
          '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
          '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
          '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
          '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF'
        ]

        // criteria별 박스플롯 트레이스 - 행 단위로 유효성 검사
        criteriaValues.forEach((cVal, idx) => {
          const color = palette[idx % palette.length]
          
          // criteriaKey 값이 cVal과 일치하는 행들 찾기 (criteria 컬럼이 없으면 모든 행 사용)
          const criteriaRows = criteriaKey && sortedData.some(r => r.hasOwnProperty(criteriaKey)) 
            ? sortedData.filter(r => r[criteriaKey] === cVal)
            : sortedData // criteria 컬럼이 없으면 모든 데이터 사용

          console.log(`📊 criteria '${cVal}': ${criteriaRows.length}개 행 발견`)
          
          const x = []
          const y = []

          criteriaRows.forEach(row => {
            const yFields = Array.isArray(s.y_fields) && s.y_fields.length ? s.y_fields : noValColumns.value
            
            // 해당 행에서 유효한 NO_VAL 값들만 수집
            const validValues = []
            yFields.forEach(noCol => {
              const v = row[noCol]
              if (v !== null && v !== undefined && Number.isFinite(Number(v))) {
                validValues.push(Number(v))
              }
            })

            // 해당 행에 유효한 값이 하나라도 있으면 모든 유효한 값들을 포함
            if (validValues.length > 0) {
              const xValue = String(row[xField] || '')
              validValues.forEach(val => {
                y.push(val)
                x.push(xValue)
              })
            }
          })

          console.log(`📊 criteria '${cVal}': ${y.length}개 데이터 포인트 생성`)

          if (y.length > 0) {
            traces.push({
              type: 'box',
              x,
              y,
              name: String(cVal),
              boxpoints: s.box?.showpoints ? 'all' : false,
              marker: { color },
              line: { color },
              fillcolor: color,
              opacity: s.box?.opacity ?? 0.7,
              showlegend: true,
              legendgroup: String(cVal),
              boxmean: false,
              notched: false,
              hoverinfo: 'all',
              hovertemplate:
                `<b>${String(cVal)}</b><br>` +
                `${xField}: %{x}<br>` +
                `Q1: %{q1}<br>` +
                `Median: %{median}<br>` +
                `Q3: %{q3}<br>` +
                `Min: %{lowerfence}<br>` +
                `Max: %{upperfence}<br>` +
                `Count: ${y.length}<br>` +
                `<extra></extra>`,
              hoveron: 'boxes',
              customdata: y.map((val, i) => ({ value: val, [xField]: x[i], criteria: cVal }))
            })
          } else {
            console.warn(`⚠️ criteria '${cVal}': 유효한 데이터 포인트가 없음`)
          }
        })

        // 스펙 라인들 (해당 그룹의 첫 행 기준)
        const firstRow = sortedData[0] || {}

        const pushLine = (field, name, color, dash = 'solid', width = 2) => {
          if (firstRow[field] !== undefined && firstRow[field] !== null) {
            const v = Number(firstRow[field])
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

        // spec_lines에 명시된 것만 반영, 없으면 모든 스펙 라인 표시 (INLINETrendChart와 동일)
        if (Array.isArray(s.spec_lines)) {
          for (const fld of s.spec_lines) {
            if (fld === 'USL') pushLine('USL', 'USL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
            else if (fld === 'LSL') pushLine('LSL', 'LSL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
            else if (fld === 'TGT') pushLine('TGT', 'TGT', 'rgba(0, 128, 0, 0.6)', 'dash', 2)
            else if (fld === 'UCL') pushLine('UCL', 'UCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)
            else if (fld === 'LCL') pushLine('LCL', 'LCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)
          }
        } else {
          // spec_lines가 명시되지 않으면 모든 스펙 라인 표시 (INLINETrendChart 기본 동작)
          pushLine('USL', 'USL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
          pushLine('LSL', 'LSL', 'rgba(255, 0, 0, 0.8)', 'solid', 2)
          pushLine('TGT', 'TGT', 'rgba(0, 128, 0, 0.6)', 'dash', 2)
          pushLine('UCL', 'UCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)
          pushLine('LCL', 'LCL', 'rgba(255, 165, 0, 0.6)', 'dot', 1)
        }

        let layout = {
          xaxis: {
            title: { text: xField, font: { size: 12 } },
            type: 'category',
            showgrid: true,
            gridcolor: '#f0f0f0',
            categoryorder: 'array',
            categoryarray: keys,
            tickangle: 90, // INLINETrendChart와 동일
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
          margin: { l: 60, r: 150, t: 20, b: 100 }, // INLINETrendChart와 동일
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          hovermode: 'closest',
          boxgap: 0.1,
          boxgroupgap: 0.3
        }

        // layout_patches 적용
        layout = applyLayoutPatches(layout, s.layout_patches)

        await Plotly.newPlot(containerEl, traces, layout, PlotlyConfig)
        console.log(`차트 생성 성공: FOR_KEY=${forKey}, 데이터수=${groupRows.length}, 필터=${JSON.stringify(spec.value)}`)
      } catch (err) {
        console.error(`[${forKey}] 차트 생성 오류:`, err)
        errorMessage.value = err?.message ?? String(err)
        debugInfo.value = JSON.stringify({
          forKey, spec: spec.value, sampleRow: rows.value?.[0], count: rows.value?.length
        }, null, 2)
        
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
      errorMessage.value = ''
      debugInfo.value = ''
      
      // DOM이 준비된 이후 렌더
      await nextTick()
      const list = forKeyList.value

      // FOR_KEY가 전혀 없을 때 안내
      if (list.length === 0) {
        return
      }

      // 각 FOR_KEY 그룹별로 개별 차트 생성
      for (const fk of list) {
        const el = chartRefs.value[fk]
        await buildAndPlotForGroup(fk, el)
      }
    }

    // 리사이즈 대응
    const handleResize = () => {
      Object.values(chartRefs.value).forEach(el => {
        if (el) {
          try { Plotly.Plots.resize(el) } catch (_) {}
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
          try { Plotly.purge(el) } catch (_) {}
        }
      })
    })

    // 반응형 업데이트
    watch(() => props.backendData, createCharts, { deep: true })
    watch(spec, createCharts, { deep: true })
    watch(rows, createCharts)
    watch(() => props.height, createCharts)
    watch(() => props.title, createCharts)
    watch(forKeyList, createCharts)

    return {
      successMessage,
      title: props.title,
      criteria,
      forKeyList,
      setChartRef,
      errorMessage,
      debugInfo
    }
  }
})
</script>

<style scoped>
.llm-plotly {
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