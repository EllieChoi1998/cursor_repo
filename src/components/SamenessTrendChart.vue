<template>
  <div class="sameness-trend-chart">
    <div v-if="routeOperGroups.length > 1" class="multi-group-charts">
      <div 
        v-for="(group, index) in routeOperGroups"
        :key="group.key"
        class="group-chart-container"
      >
        <div class="group-chart-header">
          <h3>{{ title }} - {{ group.route }} ({{ group.oper }})</h3>
          <div class="group-chart-info">
            <span class="data-count">{{ getGroupData(group).length }} records</span>
          </div>
        </div>
        <div :ref="el => setChartRef(el, index)" class="chart-container"></div>
      </div>
    </div>

    <div v-else class="single-chart">
      <div v-if="routeOperGroups.length === 1" class="group-chart-header">
        <h3>{{ title }} - {{ routeOperGroups[0].route }} ({{ routeOperGroups[0].oper }})</h3>
        <div class="group-chart-info">
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
  name: 'SamenessTrendChart',
  props: {
    data: {
      type: Array,
      default: () => []
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'EQ-CH Trend (Sameness)'
    },
    maxLabels: {
      type: Number,
      default: 50
    }
  },
  setup(props) {
    const chartContainer = ref(null)
    const chartRefs = ref([])

    // Group by MAIN_ROUTE_DESC + MAIN_OPER_DESC
    const routeOperGroups = computed(() => {
      if (!Array.isArray(props.data) || props.data.length === 0) return []
      const groupsMap = new Map()
      for (const row of props.data) {
        const route = row.MAIN_ROUTE_DESC ?? 'ROUTE'
        const oper = row.MAIN_OPER_DESC ?? 'OPER'
        const key = `${route}|||${oper}`
        if (!groupsMap.has(key)) {
          groupsMap.set(key, { key, route, oper })
        }
      }
      return Array.from(groupsMap.values())
    })

    const setChartRef = (el, index) => {
      if (el) chartRefs.value[index] = el
    }

    const getGroupData = (group) => {
      if (!group) return []
      return props.data.filter(
        (row) => (row.MAIN_ROUTE_DESC ?? 'ROUTE') === group.route && (row.MAIN_OPER_DESC ?? 'OPER') === group.oper
      )
    }

    // Generate pseudo points from quartiles to render Plotly box
    const generateBoxPoints = (min, q1, q2, q3, max, count = 30) => {
      const points = []
      const q1Count = Math.floor(count * 0.25)
      const q2Count = Math.floor(count * 0.25)
      const q3Count = Math.floor(count * 0.25)
      const q4Count = count - q1Count - q2Count - q3Count

      for (let i = 0; i < q1Count; i++) points.push(min + Math.random() * Math.max(0, q1 - min))
      for (let i = 0; i < q2Count; i++) points.push(q1 + Math.random() * Math.max(0, q2 - q1))
      for (let i = 0; i < q3Count; i++) points.push(q2 + Math.random() * Math.max(0, q3 - q2))
      for (let i = 0; i < q4Count; i++) points.push(q3 + Math.random() * Math.max(0, max - q3))

      return points
    }

    const getColorForEqCham = (eqCham, alpha = 1) => {
      const palette = [
        [102, 126, 234],
        [118, 75, 162],
        [255, 128, 10],
        [46, 204, 113],
        [231, 76, 60],
        [52, 152, 219],
        [155, 89, 182],
        [241, 196, 15],
        [26, 188, 156],
        [192, 57, 43],
        [41, 128, 185],
        [243, 156, 18]
      ]
      let hash = 0
      const str = String(eqCham ?? '')
      for (let i = 0; i < str.length; i++) {
        hash = (hash << 5) - hash + str.charCodeAt(i)
        hash |= 0
      }
      const [r, g, b] = palette[Math.abs(hash) % palette.length]
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }

    const createSingleChart = (container, data, chartTitle) => {
      if (!container || !Array.isArray(data) || data.length === 0) return

      // X order = sorted unique keys
      const keys = [...new Set(data.map(r => r.key))]
      const xOrder = keys.sort((a, b) => {
        // natural-ish sort: try numeric when possible
        const na = Number(a)
        const nb = Number(b)
        if (!Number.isNaN(na) && !Number.isNaN(nb)) return na - nb
        return String(a).localeCompare(String(b))
      })

      // control lines (use first row per key)
      const keyToRow = new Map()
      for (const row of data) {
        if (!keyToRow.has(row.key)) keyToRow.set(row.key, row)
      }
      const usls = xOrder.map(k => keyToRow.get(k)?.USL ?? null)
      const lsls = xOrder.map(k => keyToRow.get(k)?.LSL ?? null)
      const tgts = xOrder.map(k => keyToRow.get(k)?.TGT ?? null)
      const ucls = xOrder.map(k => keyToRow.get(k)?.UCL ?? null)
      const lcls = xOrder.map(k => keyToRow.get(k)?.LCL ?? null)

      // traces per EQ_CHAM
      const eqChams = [...new Set(data.map(r => r.EQ_CHAM))]
      const boxTraces = []

      eqChams.forEach(eq => {
        const groupRows = data.filter(r => r.EQ_CHAM === eq)
        const xLabels = []
        const yPoints = []
        groupRows.forEach(r => {
          const pts = generateBoxPoints(r.MIN, r.Q1, r.Q2, r.Q3, r.MAX)
          yPoints.push(...pts)
          xLabels.push(...Array(pts.length).fill(r.key))
        })
        const color = getColorForEqCham(eq)
        boxTraces.push({
          type: 'box',
          x: xLabels,
          y: yPoints,
          name: String(eq),
          boxpoints: 'outliers',
          jitter: 0.3,
          pointpos: -1.8,
          marker: { color, size: 4 },
          line: { color, width: 2 },
          fillcolor: getColorForEqCham(eq, 0.4),
          showlegend: true
        })
      })

      const scatterTraces = [
        { type: 'scatter', x: xOrder, y: usls, mode: 'lines', name: 'USL', line: { color: 'rgba(0,0,0,0.8)', width: 2 } },
        { type: 'scatter', x: xOrder, y: lsls, mode: 'lines', name: 'LSL', line: { color: 'rgba(0,0,0,0.8)', width: 2 } },
        { type: 'scatter', x: xOrder, y: tgts, mode: 'lines', name: 'TGT', line: { color: 'rgba(0,0,0,0.5)', width: 2 } },
        { type: 'scatter', x: xOrder, y: ucls, mode: 'lines', name: 'UCL', line: { color: 'rgba(255,128,10,0.5)', width: 2, dash: 'dash' } },
        { type: 'scatter', x: xOrder, y: lcls, mode: 'lines', name: 'LCL', line: { color: 'rgba(255,128,10,0.5)', width: 2, dash: 'dash' } }
      ]

      const maxLabels = props.maxLabels
      const step = Math.max(1, Math.floor(xOrder.length / maxLabels))
      const sampled = xOrder.filter((_, i) => i % step === 0)

      const layout = {
        title: { text: chartTitle || props.title, font: { size: 16, color: '#333' } },
        xaxis: {
          title: 'key', type: 'category', showgrid: true, gridcolor: '#f0f0f0',
          tickangle: 90, tickmode: 'array', tickvals: sampled, ticktext: sampled.map(v => String(v)),
          tickfont: { size: 9, color: '#333' }, automargin: true, side: 'bottom', tickposition: 'outside',
          categoryorder: 'array', categoryarray: xOrder
        },
        yaxis: { title: 'Values', showgrid: true, gridcolor: '#f0f0f0' },
        height: props.height,
        showlegend: true,
        legend: { orientation: 'v', x: 1, xanchor: 'left', y: 1, yanchor: 'top', bgcolor: 'rgba(255,255,255,0.8)', bordercolor: '#ccc', borderwidth: 1 },
        margin: { l: 60, r: 40, t: 80, b: 150 },
        plot_bgcolor: 'white', paper_bgcolor: 'white', hovermode: 'closest'
      }

      Plotly.newPlot(container, [...boxTraces, ...scatterTraces], layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        scrollZoom: true
      })
    }

    const createCharts = async () => {
      if (!Array.isArray(props.data) || props.data.length === 0) return

      if (chartContainer.value) Plotly.purge(chartContainer.value)
      chartRefs.value.forEach(ref => { if (ref) Plotly.purge(ref) })

      await nextTick()

      if (routeOperGroups.value.length > 1) {
        routeOperGroups.value.forEach((g, idx) => {
          const container = chartRefs.value[idx]
          const groupData = getGroupData(g)
          if (container && groupData.length > 0) {
            createSingleChart(container, groupData, `${props.title} - ${g.route} (${g.oper})`)
          }
        })
      } else {
        if (chartContainer.value) {
          createSingleChart(chartContainer.value, props.data, props.title)
        }
      }
    }

    onMounted(createCharts)
    watch(() => props.data, createCharts, { deep: true })
    watch(() => props.height, createCharts)
    watch(() => props.title, createCharts)

    return {
      chartContainer,
      chartRefs,
      routeOperGroups,
      getGroupData,
      setChartRef
    }
  }
})
</script>

<style scoped>
.sameness-trend-chart {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.multi-group-charts {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.group-chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.group-chart-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.group-chart-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.group-chart-info {
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

.single-chart .group-chart-header + .chart-container {
  border-top: none;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

@media (max-width: 768px) {
  .group-chart-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  .group-chart-header h3 { font-size: 16px; }
  .multi-group-charts { gap: 20px; }
}
</style>