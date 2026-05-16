<template>
  <el-row :gutter="12" class="metric-row">
    <el-col v-for="metric in metrics" :key="metric.name" :xs="24" :sm="12" :md="8">
      <el-card shadow="never" class="metric-card">
        <div class="name">{{ metric.label || metric.name }}</div>
        <div class="formula">{{ metric.formula || '原始字段' }}</div>
        <div class="meaning">{{ metric.meaning }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
defineProps({ metrics: { type: Array, default: () => [] } })
</script>

<style scoped>
.metric-row {
  margin-top: 4px;
}
.metric-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fbfdff;
  box-shadow: 0 1px 5px rgba(15, 23, 42, 0.03);
}
.name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}
.formula {
  font-size: 13px;
  color: #2563eb;
  margin-bottom: 8px;
  word-break: break-all;
}
.meaning {
  font-size: 13px;
  color: #475569;
  line-height: 1.65;
}
</style>
