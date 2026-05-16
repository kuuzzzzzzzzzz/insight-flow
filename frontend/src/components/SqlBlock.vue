<template>
  <el-collapse>
    <el-collapse-item title="生成 SQL" name="sql">
      <pre class="sql"><code>{{ sql }}</code></pre>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup>
defineProps({ sql: { type: String, default: '' } })
</script>

<style scoped>
.sql {
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.7;
}
</style>
