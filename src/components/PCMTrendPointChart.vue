<template>
  <div class="pcm-trend-point-chart">
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist'

export default defineComponent({
  name: 'PCMTrendPointChart',
  props: {
    data: {
      type: Array,
      default: () => [
        { DATE_WAFER_ID: 1, PCM_SITE: '1', VALUE: 10 },
        { DATE_WAFER_ID: 1, PCM_SITE: '2', VALUE: 11 },
        { DATE_WAFER_ID: 1, PCM_SITE: '3', VALUE: 12 },
        { DATE_WAFER_ID: 1, PCM_SITE: '4', VALUE: 13 },
        { DATE_WAFER_ID: 1, PCM_SITE: '5', VALUE: 14 },
        { DATE_WAFER_ID: 2, PCM_SITE: '1', VALUE: 11 },
        { DATE_WAFER_ID: 2, PCM_SITE: '2', VALUE: 12 },
        { DATE_WAFER_ID: 2, PCM_SITE: '3', VALUE: 13 },
        { DATE_WAFER_ID: 2, PCM_SITE: '4', VALUE: 14 },
        { DATE_WAFER_ID: 2, PCM_SITE: '5', VALUE: 15 },
        { DATE_WAFER_ID: 3, PCM_SITE: '1', VALUE: 10 },
        { DATE_WAFER_ID: 3, PCM_SITE: '2', VALUE: 11 },
        { DATE_WAFER_ID: 3, PCM_SITE: '3', VALUE: 12 },
        { DATE_WAFER_ID: 3, PCM_SITE: '4', VALUE: 13 },
        { DATE_WAFER_ID: 3, PCM_SITE: '5', VALUE: 14 },
        { DATE_WAFER_ID: 4, PCM_SITE: '1', VALUE: 12 },
        { DATE_WAFER_ID: 4, PCM_SITE: '2', VALUE: 13 },
        { DATE_WAFER_ID: 4, PCM_SITE: '3', VALUE: 14 },
        { DATE_WAFER_ID: 4, PCM_SITE: '4', VALUE: 15 },
        { DATE_WAFER_ID: 4, PCM_SITE: '5', VALUE: 16 },
        { DATE_WAFER_ID: 5, PCM_SITE: '1', VALUE: 14 },
        { DATE_WAFER_ID: 5, PCM_SITE: '2', VALUE: 13 },
        { DATE_WAFER_ID: 5, PCM_SITE: '3', VALUE: 13 },
        { DATE_WAFER_ID: 5, PCM_SITE: '4', VALUE: 12 },
        { DATE_WAFER_ID: 5, PCM_SITE: '5', VALUE: 11 }
      ]
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'PCM Trend Point Chart'
    }
  },
  setup(props) {
    const chartContainer = ref(null)

    const createChart = () => {
      if (!chartContainer.value) return
      const data = props.data
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
        marker: { size: 8 },
        line: { width: 2 }
      }))
      // x축 카테고리 정렬
      const xOrder = [...new Set(data.map(row => row.DATE_WAFER_ID))].sort((a, b) => a - b)
      const layout = {
        title: { text: props.title, font: { size: 18, color: '#333' } },
        xaxis: {
          title: 'Date Wafer ID',
          type: 'category',
          categoryorder: 'array',
          categoryarray: xOrder,
          showgrid: true,
          gridcolor: '#f0f0f0',
          tickangle: -45,
          tickfont: {
            size: 12
          },
          automargin: true
        },
        yaxis: {
          title: 'Value',
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        height: props.height,
        showlegend: true,
        legend: {
          x: 0,
          y: 1,
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: '#ccc',
          borderwidth: 1
        },
        margin: { l: 60, r: 40, t: 80, b: 120 },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        hovermode: 'closest'
      }
      Plotly.newPlot(chartContainer.value, traces, layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false
      })
    }
    const updateChart = () => {
      if (chartContainer.value) {
        Plotly.purge(chartContainer.value)
        createChart()
      }
    }
    onMounted(() => {
      createChart()
    })
    watch(() => props.data, updateChart, { deep: true })
    watch(() => props.height, updateChart)
    watch(() => props.title, updateChart)
    return { chartContainer }
  }
})
</script>

<style scoped>
.pcm-trend-point-chart {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}
.chart-container {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background: white;
}
</style> 