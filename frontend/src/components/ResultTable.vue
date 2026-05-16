<template>
  <div>
    <el-table :data="pagedRows" stripe border style="width: 100%" class="result-table">
      <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" min-width="140" />
    </el-table>
    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :page-size="pageSize"
        :total="rows.length"
        v-model:current-page="currentPage"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
})

const pageSize = 10
const currentPage = ref(1)

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return props.rows.slice(start, start + pageSize)
})
</script>

<style scoped>
.result-table :deep(.el-table__header th) {
  background: #f4f6fa;
  color: #334155;
  font-weight: 600;
}
.result-table :deep(.el-table__row td) {
  color: #1f2937;
  font-size: 13px;
}
.result-table :deep(.el-table td.el-table__cell),
.result-table :deep(.el-table th.el-table__cell) {
  padding: 11px 0;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
