<template>
  <div class="plotly-graph-wrapper">
    <div v-if="fileName" class="plotly-file-name">
      📄 {{ fileName }}
    </div>
    <div v-if="successMessage" class="plotly-success-message">
      {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="plotly-error-message">
      ⚠️ {{ errorMessage }}
    </div>
    <div ref="chartContainer" class="plotly-container"></div>
  </div>
</template>

<script>
import { defineComponent, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Plotly from 'plotly.js-dist'

const stripCodeFences = (value) => {
  if (typeof value !== 'string') return value
  const trimmed = value.trim()
  if (!trimmed) return trimmed
  const match = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i)
  return match ? match[1].trim() : trimmed
}

const parseJsonLoose = (value) => {
  if (value === null || value === undefined) return null
  if (typeof value === 'object') return value
  if (typeof value !== 'string') return null
  const cleaned = stripCodeFences(value)
  if (!cleaned) return null
  try {
    const parsed = JSON.parse(cleaned)
    if (typeof parsed === 'string') {
      return parseJsonLoose(parsed)
    }
    return parsed
  } catch (error) {
    console.warn('[PlotlyGraph] JSON parse failed:', error, cleaned)
    return null
  }
}

const normalizeSpec = (spec) => {
  if (!spec && spec !== 0) return null
  const parsed = parseJsonLoose(spec) ?? spec
  if (!parsed) return null

  if (Array.isArray(parsed)) {
    return {
      data: parsed,
      layout: {},
      config: {},
      frames: []
    }
  }

  let figure = parsed
  if (parsed.figure && typeof parsed.figure === 'object') {
    figure = parsed.figure
  }

  const data = Array.isArray(figure.data)
    ? figure.data
    : Array.isArray(figure.traces)
      ? figure.traces
      : []

  const layout = figure.layout && typeof figure.layout === 'object'
    ? { ...figure.layout }
    : {}

  const config = figure.config && typeof figure.config === 'object'
    ? { ...figure.config }
    : {}

  const frames = Array.isArray(figure.frames) ? [...figure.frames] : []

  return {
    data,
    layout,
    config,
    frames
  }
}

export default defineComponent({
  name: 'PlotlyGraph',
  props: {
    graphSpec: {
      type: [Object, String, Array],
      default: () => ({})
    },
    title: {
      type: String,
      default: ''
    },
    fileName: {
      type: String,
      default: ''
    },
    successMessage: {
      type: String,
      default: ''
    },
    height: {
      type: Number,
      default: 480
    }
  },
  setup(props) {
    const chartContainer = ref(null)
    const errorMessage = ref('')
    const parsedSpec = ref(null)

    const renderChart = async () => {
      errorMessage.value = ''
      parsedSpec.value = normalizeSpec(props.graphSpec)

      if (!parsedSpec.value || (!parsedSpec.value.data?.length && !parsedSpec.value.layout)) {
        errorMessage.value = '표시할 Plotly 스펙이 없습니다.'
        return
      }

      await nextTick()
      const container = chartContainer.value
      if (!container) return

      try {
        const data = Array.isArray(parsedSpec.value.data) ? parsedSpec.value.data : []
        const layout = { ...(parsedSpec.value.layout || {}) }

        if (props.title) {
          if (!layout.title) {
            layout.title = { text: props.title }
          } else if (typeof layout.title === 'string') {
            layout.title = { text: layout.title }
          }
        }

        if (props.height) {
          layout.height = props.height
        }

        // 기본 여백 설정 (화면에 꽉 차지 않도록)
        if (!layout.margin) {
          layout.margin = {}
        }
        layout.margin = {
          l: layout.margin.l || 80,
          r: layout.margin.r || 80,
          t: layout.margin.t || 100,
          b: layout.margin.b || 120,
          pad: layout.margin.pad || 10
        }

        // autosize 활성화
        if (!('autosize' in layout)) {
          layout.autosize = true
        }

        const config = {
          displaylogo: false,
          responsive: true,
          scrollZoom: true,
          ...parsedSpec.value.config
        }

        if (parsedSpec.value.frames && parsedSpec.value.frames.length) {
          await Plotly.react(container, data, layout, config)
          Plotly.addFrames(container, parsedSpec.value.frames)
        } else {
          await Plotly.react(container, data, layout, config)
        }
      } catch (error) {
        console.error('[PlotlyGraph] Render error:', error)
        errorMessage.value = error?.message || '그래프 렌더링 중 오류가 발생했습니다.'
      }
    }

    onMounted(() => {
      renderChart()
    })

    watch(
      () => [props.graphSpec, props.height, props.title],
      () => renderChart(),
      { deep: true }
    )

    onBeforeUnmount(() => {
      if (chartContainer.value) {
        try {
          Plotly.purge(chartContainer.value)
        } catch (_) {}
      }
    })

    return {
      chartContainer,
      errorMessage
    }
  }
})
</script>

<style scoped>
.plotly-graph-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.plotly-file-name {
  font-size: 0.9rem;
  color: #555;
  font-weight: 500;
}

.plotly-success-message {
  padding: 0.75rem 1rem;
  background: #f1f8ff;
  border-left: 4px solid #1e88e5;
  border-radius: 6px;
  color: #0d47a1;
  white-space: pre-line;
  font-size: 0.95rem;
}

.plotly-error-message {
  padding: 0.75rem 1rem;
  background: #fdecea;
  border-left: 4px solid #f44336;
  border-radius: 6px;
  color: #c62828;
  font-size: 0.95rem;
}

.plotly-container {
  width: 100%;
  min-height: 360px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
}
</style>
