<template>
  <div class="radar-wrapper">
    <div ref="chartRef" class="radar-chart" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => [0, 0, 0, 0, 0, 0]
  },
  labels: {
    type: Array,
    default: () => ['知识基础', '认知风格', '学习能力', '易错点', '学习目标', '学习偏好']
  },
  max: {
    type: Number,
    default: 1
  }
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value) return

  if (!chart) {
    chart = echarts.init(chartRef.value, null, { devicePixelRatio: 2 })
  }

  const indicator = props.labels.map(name => ({ name, max: props.max }))

  chart.setOption({
    backgroundColor: 'transparent',
    radar: {
      center: ['50%', '52%'],
      radius: '65%',
      indicator,
      axisName: {
        color: '#8896a9',
        fontSize: 13,
        fontWeight: 500,
        padding: [4, 8]
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.08)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.06)'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(79, 140, 255, 0.02)', 'rgba(79, 140, 255, 0.01)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: props.data,
        name: '学习画像',
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#4f8cff',
          borderColor: '#4f8cff',
          borderWidth: 2
        },
        lineStyle: {
          color: '#4f8cff',
          width: 2,
          shadowBlur: 12,
          shadowColor: 'rgba(79, 140, 255, 0.4)'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79, 140, 255, 0.25)' },
            { offset: 1, color: 'rgba(124, 92, 240, 0.05)' }
          ])
        }
      }]
    }]
  })
}

watch(() => props.data, () => {
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.radar-wrapper {
  width: 100%;
  height: 100%;
  min-height: 420px;
}

.radar-chart {
  width: 100%;
  height: 100%;
  min-height: 420px;
}
</style>
