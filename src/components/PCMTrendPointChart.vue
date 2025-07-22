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
    },
    maxLabels: {
      type: Number,
      default: 50  // 사용자가 설정 가능하도록 props로 받음
    },
    dataSampling: {
      type: Boolean,
      default: true  // 데이터 샘플링 여부
    }
  },
  setup(props) {
    const chartContainer = ref(null)

    const createChart = () => {
      if (!chartContainer.value) return
      
      // 데이터 샘플링 제거 - 전체 데이터 사용
      const data = props.data
      console.log(`PCMTrendPointChart 전체 데이터 사용: ${data.length}개`)
      
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
        marker: { size: 6 }, // 마커 크기 줄임
        line: { width: 1.5 } // 선 두께 줄임
      }))
      
      // x축 라벨 생성 (적절한 간격으로 표시)
      const xOrder = [...new Set(data.map(row => row.DATE_WAFER_ID))].sort((a, b) => a - b)
      const maxLabels = 50  // 적절한 라벨 수
      const step = Math.max(1, Math.floor(xOrder.length / maxLabels))
      const sampledLabels = xOrder.filter((_, index) => index % step === 0)
      
      console.log(`PCMTrendPointChart x축 라벨: ${xOrder.length}개 → ${sampledLabels.length}개 샘플링 (최대 ${maxLabels}개)`)
      
      const layout = {
        title: { text: props.title, font: { size: 18, color: '#333' } },
        xaxis: {
          title: 'Date Wafer ID',
          type: 'category',
          showgrid: true,
          gridcolor: '#f0f0f0',
          // 적절한 라벨 표시
          showticklabels: true,
          tickangle: 90,  // 45도 회전으로 겹침 방지
          tickmode: 'array',  // 명시적 라벨 설정
          tickvals: sampledLabels,  // 샘플링된 라벨 사용
          ticktext: sampledLabels.map(val => val.toString()),  // 샘플링된 텍스트
          tickfont: { 
            size: 9,  // 적절한 폰트 크기
            color: '#333'
          },
          automargin: true,
          // 하단에 라벨 표시
          side: 'bottom',  // 하단에 라벨 표시
          tickposition: 'outside',
          // category 순서 설정 (전체 데이터, 순서 유지)
          categoryorder: 'array',
          categoryarray: xOrder  // 전체 데이터 순서 유지
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
        margin: { l: 60, r: 40, t: 80, b: 150 },  // 상단 80px, 하단 150px (하단 라벨 공간)
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        hovermode: 'closest'
      }
      
      console.log('차트 생성 중...', { 
        dataLength: data.length, 
        xLabels: sampledLabels.length,
        sampleData: data.slice(0, 3),  // 처음 3개 데이터 샘플
        siteGroups: Object.keys(siteGroups),
        traces: traces.length
      })
      
      Plotly.newPlot(chartContainer.value, traces, layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        scrollZoom: true
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