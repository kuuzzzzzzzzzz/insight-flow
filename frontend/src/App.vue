<template>
  <div class="page">
    <aside class="left-panel">
      <div class="left-header">
        <h1>InsightFlow</h1>
        <p>智能数据洞察分析系统</p>
        <p class="intro-text">
          输入自然语言问题，系统自动完成 SQL 查询、指标分析、图表生成和中文洞察输出。
        </p>
      </div>

      <div class="left-body">
        <div class="field-block">
          <div class="field-title">分析问题</div>
          <el-input
            v-model="question"
            type="textarea"
            :rows="7"
            :placeholder="placeholder"
          />
        </div>

        <div class="field-block">
          <div class="field-title">数据源选择</div>
          <el-select v-model="source" style="width: 100%">
            <el-option label="CSV" value="csv" />
            <el-option label="抖音链接beta(暂未实现）" value="douyin" />
            <el-option label="B站链接 Beta" value="bilibili" />
          </el-select>
        </div>

        <div v-if="source === 'bilibili'" class="field-block">
          <div class="field-title">B站 UP 主输入</div>
          <el-input
            v-model="bilibiliInput"
            type="textarea"
            :rows="3"
            placeholder="请输入 B站 UP 主 UID 或主页链接，例如：https://space.bilibili.com/xxxxxx"
          />
        </div>

        <el-card v-if="source === 'bilibili'" shadow="never" class="up-card">
          <template #header><strong>B站 UP 主信息</strong></template>
          <p><strong>UID：</strong>{{ bilibiliUid || 'UID 待识别' }}</p>
          <p><strong>数据源：</strong>B站公开视频</p>
          <p><strong>抓取范围：</strong>最近 30 个视频</p>
          <p><strong>状态：</strong>{{ bilibiliStatusText }}</p>
        </el-card>

        <el-button type="primary" :loading="loading" class="run-btn" @click="onAnalyze">
          生成分析报告
        </el-button>

        <div class="status-group">
          <el-tag effect="plain">当前模式：{{ mode }}</el-tag>
          <el-tag effect="plain">数据库：SQLite</el-tag>
          <el-tag effect="plain">分析链路：SQL + 图表 + 中文结论</el-tag>
        </div>
      </div>
    </aside>

    <main class="right-content">
      <el-card v-if="result && !analyzeError && !showFlow" shadow="never" class="block">
        <template #header>
          <strong>分析结果</strong>
        </template>
        <el-tag effect="plain">数据源：{{ sourceLabel }}</el-tag>
      </el-card>

      <div v-if="showFlow" class="flow-wrap">
        <AgentFlow :steps="flowSteps" />
      </div>

      <el-alert
        v-if="analyzeError"
        :title="`分析失败：${analyzeError}`"
        type="error"
        show-icon
        :closable="false"
        class="block"
      />

      <el-card v-if="analyzeError && rawSql" shadow="never" class="block">
        <el-collapse>
          <el-collapse-item title="模型原始输出 raw_sql" name="raw_sql">
            <pre class="raw-sql"><code>{{ rawSql }}</code></pre>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <el-card v-if="analyzeError && errorDetail" shadow="never" class="block error-detail-card">
        <template #header><strong>错误详情</strong></template>
        <p><strong>来源：</strong>{{ errorSource || '-' }}</p>
        <p><strong>输入：</strong>{{ errorInput || '-' }}</p>
        <p><strong>详情：</strong>{{ errorDetail }}</p>
      </el-card>

      <template v-if="result && !analyzeError && !showFlow">
        <el-card shadow="never" class="block">
          <el-collapse v-model="activeSections">
            <el-collapse-item title="本次分析问题" name="question" class="main-item">
              {{ result.question }}
            </el-collapse-item>

            <el-collapse-item title="本次使用的核心指标" name="metrics_used" class="main-item">
              <MetricCards :metrics="result.metrics_used" />
            </el-collapse-item>

            <el-collapse-item title="查询结果表格" name="result_table" class="aux-item">
              <ResultTable :columns="result.table_columns" :rows="result.table_rows" />
            </el-collapse-item>

            <el-collapse-item title="图表分析" name="charts" class="main-item">
              <template v-if="result.charts && result.charts.length">
                <el-card
                  v-for="(chart, idx) in result.charts"
                  :key="`${chart.title}-${idx}`"
                  shadow="never"
                  class="inner-chart-card"
                >
                  <template #header>{{ chart.title }}</template>
                  <ChartPanel :chart-title="chart.title" :chart-type="chart.chart_type" :chart-data="chart.chart_data" />
                </el-card>
              </template>
              <template v-else>
                <ChartPanel :chart-title="'默认图表'" :chart-type="result.chart_type" :chart-data="result.chart_data" />
              </template>
            </el-collapse-item>

            <el-collapse-item title="中文分析结论" name="insight" class="main-item">
              <InsightCards :insight="result.insight" />
            </el-collapse-item>

            <el-collapse-item title="生成 SQL" name="sql_block" class="aux-item">
              <SqlBlock :sql="result.sql" />
            </el-collapse-item>

            <el-collapse-item title="用户增长指标体系" name="metric_system" class="aux-item">
              <p>{{ result.metric_system.chain }}</p>
              <el-table :data="result.metric_system.metrics" border stripe>
                <el-table-column prop="name" label="指标" min-width="180" />
                <el-table-column prop="label" label="中文名" min-width="120" />
                <el-table-column prop="formula" label="公式" min-width="260" />
                <el-table-column prop="meaning" label="业务含义" min-width="260" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { analyze, getMode } from './api/analyze'
import AgentFlow from './components/AgentFlow.vue'
import ChartPanel from './components/ChartPanel.vue'
import InsightCards from './components/InsightCards.vue'
import MetricCards from './components/MetricCards.vue'
import ResultTable from './components/ResultTable.vue'
import SqlBlock from './components/SqlBlock.vue'

const FLOW_DEFS = [
  { key: 'user', name: '用户问题', desc: '接收分析需求' },
  { key: 'planner', name: 'Planner', desc: '解析任务' },
  { key: 'sql_agent', name: 'SQLAgent', desc: '生成 SQL' },
  { key: 'sql_guard', name: 'SQLGuard', desc: '安全校验' },
  { key: 'sqlite', name: 'SQLite', desc: '执行查询' },
  { key: 'chart', name: 'ChartAgent', desc: '生成图表' },
  { key: 'insight', name: 'InsightAgent', desc: '生成结论' },
  { key: 'report', name: '分析报告', desc: '输出结果' },
]

const questionPool = [
  '哪些视频高播放低关注？',
  '最近 7 天关注转化率趋势如何？',
  '哪个内容分类带来的新增用户最多？',
  '哪个环节流失最大？',
]

const question = ref('')
const source = ref('demo')
const loading = ref(false)
const mode = ref('')
const result = ref(null)
const analyzeError = ref('')
const rawSql = ref('')
const errorDetail = ref('')
const errorSource = ref('')
const errorInput = ref('')
const bilibiliInput = ref('')
const activeSections = ref(['question', 'metrics_used', 'charts', 'insight'])
const placeholder = `例如：${questionPool[Math.floor(Math.random() * questionPool.length)]}`
const flowSteps = ref(FLOW_DEFS.map((s) => ({ ...s, status: 'pending' })))
const flowRunId = ref(0)

const hasResult = computed(() => !!result.value)
const hasError = computed(() => !!analyzeError.value)
const showFlow = computed(() => loading.value || hasError.value || !hasResult.value)

const sourceLabel = computed(() => {
  if (source.value === 'demo') return 'Demo'
  if (source.value === 'csv') return 'CSV'
  if (source.value === 'douyin') return '抖音链接 Beta'
  return 'B站链接 Beta'
})

const bilibiliUid = computed(() => {
  const text = (bilibiliInput.value || '').trim()
  if (!text) return ''
  if (/^\d+$/.test(text)) return text
  const m = text.match(/space\.bilibili\.com\/(\d+)/)
  return m ? m[1] : ''
})

const bilibiliStatusText = computed(() => {
  if (source.value !== 'bilibili') return '待输入'
  if (!bilibiliInput.value.trim()) return '待输入'
  if (loading.value) return '正在拉取/分析'
  if (hasError.value) return '分析失败'
  if (hasResult.value) return '已完成'
  return '待分析'
})

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function resetFlow() {
  flowSteps.value = FLOW_DEFS.map((s) => ({ ...s, status: 'pending' }))
}

function setStepStatus(index, status) {
  const next = flowSteps.value.map((s, i) => (i === index ? { ...s, status } : s))
  flowSteps.value = next
}

async function runFlowAnimation(runId) {
  for (let i = 0; i < FLOW_DEFS.length - 1; i += 1) {
    if (runId !== flowRunId.value) return
    setStepStatus(i, 'running')
    await delay(300)
    if (runId !== flowRunId.value) return
    setStepStatus(i, 'success')
  }
  if (runId !== flowRunId.value) return
  setStepStatus(FLOW_DEFS.length - 1, 'running')
}

function markFlowSuccess() {
  setStepStatus(FLOW_DEFS.length - 1, 'success')
}

function markFlowError() {
  const idx = flowSteps.value.findIndex((s) => s.status === 'running')
  const target = idx >= 0 ? idx : FLOW_DEFS.length - 1
  setStepStatus(target, 'error')
}

async function loadMode() {
  const res = await getMode()
  mode.value = res.data.mode
}

async function onAnalyze() {
  if (source.value === 'douyin') {
    ElMessage.info('当前版本暂未接入真实链接解析，已预留 Connector 扩展位。')
    return
  }
  if (source.value === 'bilibili' && !bilibiliInput.value.trim()) {
    ElMessage.warning('请输入 B站 UP 主 UID 或主页链接')
    return
  }

  const bilibiliDefaultQuestion =
    '请基于该 B站 UP 主最近 30 个视频做一次整体增长诊断，分析播放表现、互动表现、内容分类表现和用户增长转化表现，找出表现最好和最差的视频，并给出内容优化建议。'
  const finalQuestion =
    question.value.trim() || (source.value === 'bilibili' ? bilibiliDefaultQuestion : '')
  if (!finalQuestion) {
    ElMessage.warning('请输入分析问题')
    return
  }

  flowRunId.value += 1
  const runId = flowRunId.value
  resetFlow()

  result.value = null
  analyzeError.value = ''
  rawSql.value = ''
  errorDetail.value = ''
  errorSource.value = ''
  errorInput.value = ''

  loading.value = true
  const flowPromise = runFlowAnimation(runId)

  try {
    const payload = {
      question: finalQuestion,
      source: source.value,
      bilibili_input: source.value === 'bilibili' ? bilibiliInput.value.trim() : null,
    }
    const res = await analyze(payload)
    const data = res.data || {}

    if (data.error) {
      analyzeError.value = data.error
      rawSql.value = data.raw_sql || ''
      errorDetail.value = data.detail || ''
      errorSource.value = data.source || ''
      errorInput.value = data.input || ''
      await flowPromise
      if (runId === flowRunId.value) markFlowError()
      return
    }

    await flowPromise
    if (runId !== flowRunId.value) return
    markFlowSuccess()
    await delay(220)

    analyzeError.value = ''
    rawSql.value = ''
    errorDetail.value = ''
    errorSource.value = ''
    errorInput.value = ''
    result.value = data
    activeSections.value = ['question', 'metrics_used', 'charts', 'insight']
    mode.value = data.mode || mode.value
  } catch (err) {
    analyzeError.value = err?.response?.data?.detail || '分析失败'
    rawSql.value = ''
    errorDetail.value = err?.response?.data?.detail || ''
    errorSource.value = err?.response?.data?.source || ''
    errorInput.value = err?.response?.data?.input || ''
    result.value = null
    await flowPromise
    if (runId === flowRunId.value) markFlowError()
    ElMessage.error(err?.response?.data?.detail || '分析失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  resetFlow()
  loadMode()
})
</script>

<style scoped>
.page {
  background: #f8fafc;
  min-height: 100vh;
  font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
  color: #1f2937;
  line-height: 1.6;
  overflow-x: hidden;
}
.left-panel {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 340px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  z-index: 10;
  overflow-y: auto;
}
.left-header h1 {
  margin: 0;
  font-size: 28px;
  font-style: italic;
  color: #2563eb;
  text-align: center;
}
.left-header p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
}
.left-header .intro-text {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
}
.left-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
.up-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
}
.up-card p {
  margin: 6px 0;
  color: #334155;
  font-size: 13px;
}
.run-btn {
  width: 100%;
  margin-top: 4px;
}
.status-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}
.right-content {
  margin-left: 340px;
  padding: 20px 22px;
}
.flow-wrap {
  min-height: 560px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.block {
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
:deep(.el-card__body) {
  padding: 18px;
}
:deep(.el-card__header) {
  text-align: center;
  font-weight: 700;
}
:deep(.el-tag) {
  border-radius: 10px;
  border-color: #dbe7ff;
  color: #334155;
  background: #f8fbff;
  font-size: 13px;
  padding: 6px 10px;
}
:deep(.el-textarea__inner) {
  border-radius: 12px;
  border-color: #d1d5db;
  min-height: 180px;
  font-size: 14px;
  line-height: 1.7;
}
:deep(.el-input__wrapper) {
  border-radius: 10px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  height: 40px;
  font-size: 14px;
  font-weight: 600;
}
:deep(.el-collapse) {
  border-top: none;
  border-bottom: none;
}
:deep(.el-collapse-item__header) {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  height: 50px;
  border-bottom: 1px solid #eef2f7;
  transition: all 0.2s ease;
  justify-content: center;
  text-align: center;
  position: relative;
  padding-left: 44px;
  padding-right: 44px;
  box-sizing: border-box;
}
:deep(.el-collapse-item__arrow) {
  position: absolute;
  right: 16px;
}
:deep(.el-collapse-item__header:hover) {
  background: #f8fbff;
}
:deep(.el-collapse-item__wrap) {
  border-bottom: 1px solid #eef2f7;
  background: #ffffff;
}
:deep(.el-collapse-item__content) {
  padding: 14px 4px 16px;
  color: #334155;
}
.main-item :deep(.el-collapse-item__header) {
  background: #ffffff;
  color: #0f172a;
  box-shadow: inset 3px 0 0 #cbd5e1, inset 0 -1px 0 #eef2f7;
}
.main-item :deep(.el-collapse-item__wrap) {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-top: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.main-item :deep(.el-collapse-item__header.is-active) {
  background: #ffffff;
  color: #0f172a;
  box-shadow: inset 4px 0 0 #3b82f6, inset 0 -1px 0 #e2e8f0;
}
.aux-item :deep(.el-collapse-item__header) {
  background: #ffffff;
  color: #0f172a;
  box-shadow: inset 3px 0 0 #cbd5e1, inset 0 -1px 0 #eef2f7;
}
.aux-item :deep(.el-collapse-item__wrap) {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-top: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.aux-item :deep(.el-collapse-item__header.is-active) {
  background: #ffffff;
  color: #0f172a;
  box-shadow: inset 4px 0 0 #3b82f6, inset 0 -1px 0 #e2e8f0;
}
.raw-sql {
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  white-space: pre-wrap;
  line-height: 1.65;
}
.error-detail-card p {
  margin: 8px 0;
  color: #334155;
}
.inner-chart-card {
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.04);
}
:deep(.el-table th.el-table__cell) {
  background: #f5f7fb;
  color: #334155;
  font-weight: 600;
}
:deep(.el-table td.el-table__cell) {
  padding: 10px 0;
  color: #1f2937;
}

@media (max-width: 1024px) {
  .left-panel {
    position: static;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  .right-content {
    margin-left: 0;
    padding: 14px;
  }
  .flow-wrap {
    min-height: 360px;
  }
}
</style>
