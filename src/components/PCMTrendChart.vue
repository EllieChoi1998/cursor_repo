<template>
  <div class="pcm-trend-chart">
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist'

export default defineComponent({
  name: 'PCMTrendChart',
  props: {
    data: {
      type: Array,
      default: () => [
        [1, 10, 20, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
        [2, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
        [3, 11, 19, 15, 16, 17, 'B', 30, 15, 1, 25, 6],
        [4, 12, 21, 15, 16, 17, 'B', 30, 15, 1, 25, 6],
        [5, 9, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6],
        [6, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
        [7, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
        [8, 11, 21, 15, 16, 17, 'A', 30, 15, 1, 25, 6],
        [9, 12, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6],
        [10, 8, 21, 15, 16, 17, 'C', 30, 15, 1, 25, 6]
      ]
    },
    height: {
      type: Number,
      default: 600
    },
    title: {
      type: String,
      default: 'PCM Trend Analysis'
    }
  },
  setup(props) {
    const chartContainer = ref(null)
    const columns = ['DATE_WAFER_ID', 'MIN', 'MAX', 'Q1', 'Q2', 'Q3', 'DEVICE', 'USL', 'TGT', 'LSL', 'UCL', 'LCL']

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

    const createChart = () => {
      if (!chartContainer.value) return

      // Convert data to the format expected by Plotly.js
      const data = props.data.map(row => {
        const obj = {}
        columns.forEach((col, index) => {
          obj[col] = row[index]
        })
        return obj
      })

      // Extract data for control lines
      const dateWaferIds = data.map(row => row.DATE_WAFER_ID)
      const usls = data.map(row => row.USL)
      const tgts = data.map(row => row.TGT)
      const lsls = data.map(row => row.LSL)
      const ucls = data.map(row => row.UCL)
      const lcls = data.map(row => row.LCL)

      // Create box plot traces for each device
      const deviceTypes = [...new Set(data.map(row => row.DEVICE))]
      const boxTraces = []
      
      deviceTypes.forEach(device => {
        const deviceData = data.filter(row => row.DEVICE === device)
        
        // Generate box plot data for each date point
        const allBoxData = []
        const allLabels = []
        
        deviceData.forEach(row => {
          const boxData = generateBoxPlotData(
            row.MIN, 
            row.Q1, 
            row.Q2, 
            row.Q3, 
            row.MAX
          )
          allBoxData.push(...boxData)
          allLabels.push(...Array(boxData.length).fill(row.DATE_WAFER_ID))
        })

        boxTraces.push({
          type: 'box',
          x: allLabels,
          y: allBoxData,
          name: `Device ${device}`,
          boxpoints: 'outliers',
          jitter: 0.3,
          pointpos: -1.8,
          marker: {
            color: getDeviceColor(device),
            size: 4
          },
          line: {
            color: getDeviceColor(device),
            width: 2
          },
          fillcolor: getDeviceColor(device, 0.3),
          showlegend: true
        })
      })

      // Create scatter traces for control lines (matching Python go.Scatter approach)
      const scatterTraces = [
        {
          type: 'scatter',
          x: dateWaferIds,
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
          x: dateWaferIds,
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
          x: dateWaferIds,
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
          x: dateWaferIds,
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
          x: dateWaferIds,
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

      // Combine all traces
      const allTraces = [...boxTraces, ...scatterTraces]

      // Layout configuration
      const layout = {
        title: {
          text: props.title,
          font: {
            size: 18,
            color: '#333'
          }
        },
        xaxis: {
          title: 'Date Wafer ID',
          type: 'category',
          categoryorder: 'array',
          categoryarray: dateWaferIds,
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        yaxis: {
          title: 'Values',
          showgrid: true,
          gridcolor: '#f0f0f0'
        },
        height: props.height,
        showlegend: true,
        legend: {
          x: 0,
          y: 1,
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          bordercolor: '#ccc',
          borderwidth: 1
        },
        margin: {
          l: 60,
          r: 40,
          t: 80,
          b: 60
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        hovermode: 'closest'
      }

      // Plot the chart
      Plotly.newPlot(chartContainer.value, allTraces, layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false
      })
    }

    // Helper function to get colors for different devices
    const getDeviceColor = (device, alpha = 1) => {
      const colors = {
        'A': `rgba(102, 126, 234, ${alpha})`,
        'B': `rgba(118, 75, 162, ${alpha})`,
        'C': `rgba(255, 128, 10, ${alpha})`
      }
      return colors[device] || `rgba(128, 128, 128, ${alpha})`
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

    return {
      chartContainer
    }
  }
})
</script>

<style scoped>
.pcm-trend-chart {
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