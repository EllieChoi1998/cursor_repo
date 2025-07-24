<template>
  <div class="pcm-trend-chart-multi-para">
    <div class="charts-container">
      <div 
        v-for="paraType in paraTypes" 
        :key="paraType"
        class="chart-wrapper"
      >
        <h3 class="chart-title">{{ paraType }} Trend Analysis</h3>
        <PCMTrendChart 
          :data="getDataForParaType(paraType)"
          :height="chartHeight"
          :title="`${paraType} PCM Trend Analysis`"
          :maxLabels="maxLabels"
          :dataSampling="dataSampling"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, computed } from 'vue'
import PCMTrendChart from './PCMTrendChart.vue'

export default defineComponent({
  name: 'PCMTrendChartMultiPara',
  components: {
    PCMTrendChart
  },
  props: {
    data: {
      type: Array,
      default: () => []
    },
    height: {
      type: Number,
      default: 400
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
    // PARA 타입들을 추출
    const paraTypes = computed(() => {
      const paraSet = new Set()
      props.data.forEach(item => {
        if (item.PARA) {
          paraSet.add(item.PARA)
        }
      })
      return Array.from(paraSet).sort()
    })

    // 특정 PARA 타입에 대한 데이터 필터링
    const getDataForParaType = (paraType) => {
      return props.data.filter(item => item.PARA === paraType)
    }

    // 차트 높이 계산 (PARA 타입 개수에 따라 조정)
    const chartHeight = computed(() => {
      const paraCount = paraTypes.value.length
      if (paraCount <= 2) return props.height
      if (paraCount <= 4) return Math.max(300, props.height * 0.8)
      return Math.max(250, props.height * 0.6)
    })

    return {
      paraTypes,
      getDataForParaType,
      chartHeight
    }
  }
})
</script>

<style scoped>
.pcm-trend-chart-multi-para {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
  gap: 25px;
  margin-top: 20px;
}

.chart-wrapper {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  text-align: center;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    padding: 10px;
  }
  
  .chart-title {
    font-size: 14px;
  }
}
</style>