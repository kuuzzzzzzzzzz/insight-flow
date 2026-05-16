<template>
  <el-row :gutter="12">
    <el-col v-for="key in keys" :key="key" :xs="24" :sm="12">
      <el-card shadow="never" class="insight-card">
        <template #header>
          <strong>{{ key }}</strong>
        </template>
        <div class="content markdown-body" v-html="renderMarkdown(insight?.[key] || '暂无内容')"></div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const keys = ['核心发现', '数据解释', '可能原因', '增长建议']
defineProps({ insight: { type: Object, default: () => ({}) } })

const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
})

function renderMarkdown(text) {
  const raw = md.render(String(text || '暂无内容'))
  return DOMPurify.sanitize(raw, {
    FORBID_TAGS: ['script', 'iframe'],
  })
}
</script>

<style scoped>
.insight-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 5px rgba(15, 23, 42, 0.03);
}
.insight-card :deep(.el-card__header) {
  background: #f8fafc;
  border-bottom: 1px solid #eef2f7;
  color: #0f172a;
  font-size: 15px;
}
.content {
  color: #334155;
  line-height: 1.85;
  font-size: 14px;
  padding-top: 2px;
}
.markdown-body :deep(p) {
  margin: 0 0 10px;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0 12px;
  padding-left: 22px;
}
.markdown-body :deep(li) {
  margin: 4px 0;
}
.markdown-body :deep(strong) {
  color: #0f172a;
  font-weight: 700;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 8px 0 10px;
  font-size: 15px;
  color: #0f172a;
}
</style>
