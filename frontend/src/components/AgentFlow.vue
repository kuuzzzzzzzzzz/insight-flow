<template>
  <el-card shadow="never" class="flow-card">
    <template #header>
      <strong>Agent 协作流程</strong>
    </template>

    <div class="network-wrap">
      <div class="network">
        <div class="node user" :class="`status-${statusOf('user')}`">
          <div class="node-title">用户问题</div>
          <div class="node-desc">接收分析需求</div>
          <div class="node-mark" v-if="statusOf('user') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('user') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('user') === 'running'">运行中</div>
        </div>

        <div class="node sqlguard" :class="`status-${statusOf('sql_guard')}`">
          <div class="node-title">SQLGuard</div>
          <div class="node-desc">安全校验</div>
          <div class="node-mark" v-if="statusOf('sql_guard') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('sql_guard') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('sql_guard') === 'running'">运行中</div>
        </div>

        <div class="node sqlite" :class="`status-${statusOf('sqlite')}`">
          <div class="node-title">SQLite</div>
          <div class="node-desc">执行查询</div>
          <div class="node-mark" v-if="statusOf('sqlite') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('sqlite') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('sqlite') === 'running'">运行中</div>
        </div>

        <div class="node report" :class="`status-${statusOf('report')}`">
          <div class="node-title">分析报告</div>
          <div class="node-desc">输出结果</div>
          <div class="node-mark" v-if="statusOf('report') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('report') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('report') === 'running'">运行中</div>
        </div>

        <div class="node planner" :class="`status-${statusOf('planner')}`">
          <div class="node-title">Planner</div>
          <div class="node-desc">解析任务</div>
          <div class="node-mark" v-if="statusOf('planner') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('planner') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('planner') === 'running'">运行中</div>
        </div>

        <div class="node sqlagent" :class="`status-${statusOf('sql_agent')}`">
          <div class="node-title">SQLAgent</div>
          <div class="node-desc">生成 SQL</div>
          <div class="node-mark" v-if="statusOf('sql_agent') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('sql_agent') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('sql_agent') === 'running'">运行中</div>
        </div>

        <div class="node chart" :class="`status-${statusOf('chart')}`">
          <div class="node-title">ChartAgent</div>
          <div class="node-desc">生成图表</div>
          <div class="node-mark" v-if="statusOf('chart') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('chart') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('chart') === 'running'">运行中</div>
        </div>

        <div class="node insight" :class="`status-${statusOf('insight')}`">
          <div class="node-title">InsightAgent</div>
          <div class="node-desc">生成结论</div>
          <div class="node-mark" v-if="statusOf('insight') === 'success'">✓</div>
          <div class="node-mark error" v-else-if="statusOf('insight') === 'error'">✕</div>
          <div class="run-badge" v-if="statusOf('insight') === 'running'">运行中</div>
        </div>

        <!-- connectors -->
        <div class="conn down c-user-planner" :class="{ active: isConnActive('user', 'planner') }"></div>
        <div class="conn right c-planner-sqlagent" :class="{ active: isConnActive('planner', 'sql_agent') }"></div>
        <div class="conn up c-sqlagent-sqlguard" :class="{ active: isConnActive('sql_agent', 'sql_guard') }"></div>
        <div class="conn right c-sqlguard-sqlite" :class="{ active: isConnActive('sql_guard', 'sqlite') }"></div>
        <div class="conn down c-sqlite-chart" :class="{ active: isConnActive('sqlite', 'chart') }"></div>
        <div class="conn right c-chart-insight" :class="{ active: isConnActive('chart', 'insight') }"></div>
        <div class="conn right c-sqlite-report" :class="{ active: isConnActive('sqlite', 'report') }"></div>
        <div class="conn up c-insight-report" :class="{ active: isConnActive('insight', 'report') }"></div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
})

const stepMap = computed(() => {
  const m = {}
  for (const s of props.steps || []) {
    m[s.key] = s.status
  }
  return m
})

function statusOf(key) {
  return stepMap.value[key] || 'pending'
}

function isConnActive(from, to) {
  const a = statusOf(from)
  const b = statusOf(to)
  return ['running', 'success'].includes(a) || ['running', 'success', 'error'].includes(b)
}
</script>

<style scoped>
.flow-card {
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
  width: min(100%, 1480px);
}

.network-wrap {
  display: flex;
  justify-content: center;
  padding: 14px 8px 12px;
}

.network {
  --node-w: 250px;
  --node-h: 148px;
  --col-gap: 90px;
  --row-gap: 120px;
  --step: calc(var(--node-w) + var(--col-gap));
  width: calc(var(--node-w) * 4 + var(--col-gap) * 3);
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, var(--node-w));
  grid-template-rows: repeat(2, var(--node-h));
  column-gap: var(--col-gap);
  row-gap: var(--row-gap);
  justify-content: center;
}

.node {
  border: 1px solid #cfd8e3;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
  padding: 16px 16px;
  position: relative;
  transition: all 0.2s ease;
}
.node-title {
  color: #1f2937;
  font-weight: 700;
  font-size: 18px;
}
.node-desc {
  color: #64748b;
  font-size: 14px;
  margin-top: 10px;
  line-height: 1.5;
}
.node-mark {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ecfdf5;
  color: #16a34a;
  font-size: 14px;
  font-weight: 700;
}
.node-mark.error {
  background: #fff1f2;
  color: #dc2626;
}
.run-badge {
  margin-top: 12px;
  display: inline-block;
  font-size: 12px;
  line-height: 1;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  border-radius: 999px;
  padding: 5px 10px;
}

.user { grid-column: 1; grid-row: 1; }
.sqlguard { grid-column: 2; grid-row: 1; }
.sqlite { grid-column: 3; grid-row: 1; }
.report { grid-column: 4; grid-row: 1; }
.planner { grid-column: 1; grid-row: 2; }
.sqlagent { grid-column: 2; grid-row: 2; }
.chart { grid-column: 3; grid-row: 2; }
.insight { grid-column: 4; grid-row: 2; }

.status-pending {
  border-color: #d1d5db;
  background: #ffffff;
}
.status-pending .node-title,
.status-pending .node-desc {
  color: #6b7280;
}
.status-running {
  border-color: #60a5fa;
  background: #f8fbff;
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.16);
  animation: pulse 1.25s ease-in-out infinite;
}
.status-success {
  border-color: #86efac;
  background: #ffffff;
}
.status-error {
  border-color: #fca5a5;
  background: #ffffff;
}

.conn {
  position: absolute;
  color: #cbd5e1;
}
.conn.active {
  color: #60a5fa;
}
.conn.right {
  height: 3px;
  background: currentColor;
}
.conn.down,
.conn.up {
  width: 3px;
  background: currentColor;
}

/* relation lines */
.c-user-planner {
  left: calc(var(--node-w) / 2);
  top: calc(var(--node-h) + 16px);
  height: calc(var(--row-gap) - 34px);
}
.c-planner-sqlagent {
  left: calc(var(--node-w) + 16px);
  top: calc(var(--node-h) + var(--row-gap) + var(--node-h) / 2);
  width: calc(var(--col-gap) - 32px);
}
.c-sqlagent-sqlguard {
  left: calc(var(--step) + var(--node-w) / 2);
  top: calc(var(--node-h) + 16px);
  height: calc(var(--row-gap) - 34px);
}
.c-sqlguard-sqlite {
  left: calc(var(--step) + var(--node-w) + 16px);
  top: calc(var(--node-h) / 2);
  width: calc(var(--col-gap) - 32px);
}
.c-sqlite-chart {
  left: calc(var(--step) * 2 + var(--node-w) / 2);
  top: calc(var(--node-h) + 16px);
  height: calc(var(--row-gap) - 34px);
}
.c-chart-insight {
  left: calc(var(--step) * 2 + var(--node-w) + 16px);
  top: calc(var(--node-h) + var(--row-gap) + var(--node-h) / 2);
  width: calc(var(--col-gap) - 32px);
}
.c-sqlite-report {
  left: calc(var(--step) * 2 + var(--node-w) + 16px);
  top: calc(var(--node-h) / 2);
  width: calc(var(--col-gap) - 32px);
}
.c-insight-report {
  left: calc(var(--step) * 3 + var(--node-w) / 2);
  top: calc(var(--node-h) + 16px);
  height: calc(var(--row-gap) - 34px);
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(96, 165, 250, 0.22); }
  70% { box-shadow: 0 0 0 8px rgba(96, 165, 250, 0); }
  100% { box-shadow: 0 0 0 0 rgba(96, 165, 250, 0); }
}

@media (max-width: 1180px) {
  .network {
    --node-w: 190px;
    --node-h: 122px;
    --col-gap: 48px;
    --row-gap: 78px;
  }
  .node-title { font-size: 16px; }
  .node-desc { font-size: 13px; }
}

@media (max-width: 920px) {
  .network {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }
  .node {
    width: calc(50% - 12px);
    min-width: 210px;
    height: auto;
  }
  .conn {
    display: none;
  }
}
</style>
