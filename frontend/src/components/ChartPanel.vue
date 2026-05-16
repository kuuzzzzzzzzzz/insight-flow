<template>
  <el-card shadow="never" class="chart-card">
    <div ref="chartRef" style="height: 360px; width: 100%"></div>
  </el-card>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  chartType: { type: String, default: 'bar' },
  chartData: { type: [Array, Object], default: () => [] },
  chartTitle: { type: String, default: '' },
})

const chartRef = ref(null)
let chart = null
let resizeTimer = null
const metricNameMap = {
  play_rate: '播放率',
  valid_view_rate: '有效观看率',
  completion_rate: '完播率',
  engagement_user_rate: '互动用户率',
  profile_visit_rate: '主页访问率',
  follow_conversion_rate: '关注转化率',
  next_day_retention_rate: '次日留存率',
  new_user_ratio: '新用户占比',
  impression_count: '曝光量',
  view_count: '播放量',
  follow_count: '关注数',
  profile_visit_count: '主页访问数',
}

function displayName(name) {
  return metricNameMap[name] || name
}

function isRateLikeMetric(name) {
  const n = String(name || '').toLowerCase()
  return (
    n.includes('rate') ||
    n.includes('ratio') ||
    n.includes('retention') ||
    n.includes('conversion') ||
    n.includes('率') ||
    n.includes('占比') ||
    n.includes('留存') ||
    n.includes('转化')
  )
}

function isGrowthScoreMetric(name) {
  const n = String(name || '').toLowerCase()
  return n.includes('growth_score') || n.includes('综合增长得分')
}

function isCountLikeMetric(name) {
  const n = String(name || '').toLowerCase()
  return (
    n.includes('count') ||
    n.includes('views') ||
    n.includes('播放量') ||
    n.includes('点赞数') ||
    n.includes('收藏数') ||
    n.includes('评论数') ||
    n.includes('分享数') ||
    n.includes('弹幕数') ||
    n.includes('用户数') ||
    n.includes('访问数')
  )
}

function formatValueByMetric(metricName, value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return String(value ?? '')

  if (isGrowthScoreMetric(metricName)) {
    return num.toFixed(4)
  }

  if (isRateLikeMetric(metricName) && num >= 0 && num <= 1) {
    return `${(num * 100).toFixed(2)}%`
  }

  if (isCountLikeMetric(metricName)) {
    return Math.round(num).toLocaleString()
  }

  if (Math.abs(num) >= 1000) return Math.round(num).toLocaleString()
  if (Number.isInteger(num)) return num.toLocaleString()
  return num.toFixed(4).replace(/\.?0+$/, '')
}

function truncateLabel(label) {
  const text = String(label ?? '')
  const hasCjk = /[\u3400-\u9fff]/.test(text)
  const limit = hasCjk ? 10 : 16
  if (text.length <= limit) return text
  return `${text.slice(0, limit)}...`
}

function optionFromPayload(type, data) {
  // New format: { xAxis: [...], series: [{name, data: [...]}, ...] }
  if (data && !Array.isArray(data) && data.xAxis && data.series) {
    const originalXAxis = (data.xAxis || []).map((x) => String(x ?? ''))
    const displayXAxis = originalXAxis.map(truncateLabel)
    const forceBar = (props.chartTitle || '').includes('效率指标')
    const renderType = forceBar && type === 'line' ? 'bar' : type
    const multiSeries = data.series.map((s) => ({
      name: displayName(s.name),
      rawName: s.name,
      type: renderType === 'line' ? 'line' : 'bar',
      data: s.data || [],
      smooth: renderType === 'line',
    }))
    return {
      tooltip: {
        trigger: 'axis',
        formatter(params) {
          const arr = Array.isArray(params) ? params : [params]
          const idx = arr[0]?.dataIndex ?? 0
          const fullTitle = originalXAxis[idx] || arr[0]?.axisValue || ''
          const lines = [fullTitle]
          arr.forEach((item) => {
            const rawMetricName = multiSeries[item.seriesIndex]?.rawName || ''
            lines.push(`${item.marker}${item.seriesName}: ${formatValueByMetric(rawMetricName, item.value)}`)
          })
          return lines.join('<br/>')
        },
      },
      legend: { top: 6, textStyle: { color: '#334155', fontSize: 12 } },
      grid: { left: 48, right: 20, top: 48, bottom: 78 },
      xAxis: {
        type: 'category',
        data: displayXAxis,
        axisLabel: { interval: 0, rotate: 20, color: '#475569', fontSize: 11, margin: 14 },
      },
      yAxis: { type: 'value', axisLabel: { color: '#475569' } },
      series: multiSeries,
    }
  }

  if (type === 'pie') {
    const pieData = (data || []).map((d) => ({ ...d, name: displayName(d.name) }))
    return {
      tooltip: { trigger: 'item' },
      legend: { top: 6, textStyle: { color: '#334155', fontSize: 12 } },
      series: [{ type: 'pie', radius: '60%', data: pieData }],
    }
  }
  if (type === 'funnel') {
    const funnelData = (data || []).map((d) => ({ ...d, name: displayName(d.name) }))
    return {
      tooltip: { trigger: 'item' },
      legend: { top: 6, textStyle: { color: '#334155', fontSize: 12 } },
      series: [{ type: 'funnel', left: '10%', width: '80%', data: funnelData }],
    }
  }
  const xData = data.map((d) => d.x)
  const xDataFull = xData.map((x) => String(x ?? ''))
  const xDataDisplay = xDataFull.map(truncateLabel)
  const yData = data.map((d) => d.y)
  return {
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        const arr = Array.isArray(params) ? params : [params]
        const idx = arr[0]?.dataIndex ?? 0
        const fullTitle = xDataFull[idx] || arr[0]?.axisValue || ''
        const val = arr[0]?.value
        return `${fullTitle}<br/>${arr[0]?.marker || ''}${formatValueByMetric('', val)}`
      },
    },
    grid: { left: 48, right: 20, top: 34, bottom: 78 },
    xAxis: { type: 'category', data: xDataDisplay, axisLabel: { interval: 0, rotate: 20, color: '#475569', fontSize: 11, margin: 14 } },
    yAxis: { type: 'value', axisLabel: { color: '#475569' } },
    series: [{ type: type === 'line' ? 'line' : 'bar', data: yData, smooth: type === 'line' }],
  }
}

function renderChart() {
  nextTick(() => {
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value)
    chart.setOption(optionFromPayload(props.chartType, props.chartData || []), true)
    chart.resize()

    // Handle collapsed panel/layout transition cases.
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (chart) chart.resize()
    }, 100)
  })
}

function handleWindowResize() {
  if (chart) chart.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleWindowResize)
})
watch(() => [props.chartType, props.chartData], renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (resizeTimer) {
    clearTimeout(resizeTimer)
    resizeTimer = null
  }
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.chart-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 5px rgba(15, 23, 42, 0.03);
}
</style>
