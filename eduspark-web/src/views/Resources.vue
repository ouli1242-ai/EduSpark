<template>
  <div class="resources-page">
    <el-tabs v-model="activeType" @tab-change="fetchResources">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="文档" name="document" />
      <el-tab-pane label="题目" name="quiz" />
      <el-tab-pane label="思维导图" name="mindmap" />
      <el-tab-pane label="代码案例" name="code" />
      <el-tab-pane label="视频" name="video" />
    </el-tabs>

    <el-empty v-if="resources.length === 0" description="暂无学习资源，请在对话中生成" />

    <el-row :gutter="16">
      <el-col :span="8" v-for="item in resources" :key="item.id">
        <el-card class="resource-card" shadow="hover" @click="viewResource(item)">
          <div class="resource-type">{{ typeLabel(item.type) }}</div>
          <h4>{{ item.title }}</h4>
          <p class="resource-desc">{{ item.description }}</p>
          <div class="resource-meta">
            <span>{{ formatDate(item.created_at) }}</span>
            <el-tag :type="statusType(item.status)" size="small">{{ item.status }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 资源详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="currentResource?.title" width="70%">
      <div v-if="currentResource" class="resource-detail">
        <div v-html="renderContent(currentResource.content)" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '@/api/request'

const md = new MarkdownIt()
const activeType = ref('all')
const resources = ref([])
const dialogVisible = ref(false)
const currentResource = ref(null)

const typeLabels = {
  document: '📄 文档',
  quiz: '📝 题目',
  mindmap: '🧠 思维导图',
  code: '💻 代码案例',
  video: '🎬 视频',
}

function typeLabel(type) {
  return typeLabels[type] || type
}

function statusType(status) {
  const map = { completed: 'success', generating: 'warning', failed: 'danger' }
  return map[status] || 'info'
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

function renderContent(content) {
  if (!content) return ''
  // 尝试解析 JSON 格式的资源
  try {
    const data = JSON.parse(content)
    if (data.type === 'quiz' && data.questions) {
      return renderQuiz(data.questions)
    }
    if (data.type === 'mindmap' && data.tree) {
      return renderMindmap(data.tree)
    }
    if (data.content) return md.render(data.content)
    return md.render(content)
  } catch {
    return md.render(content)
  }
}

function renderQuiz(questions) {
  return questions.map((q, i) => {
    let html = `<h4>${i + 1}. ${q.question}</h4>`
    if (q.options) {
      html += '<ul>' + q.options.map(o => `<li>${o}</li>`).join('') + '</ul>'
    }
    html += `<p><strong>答案：</strong>${q.answer}</p>`
    if (q.explanation) html += `<p><em>解析：</em>${q.explanation}</p>`
    return html
  }).join('<hr/>')
}

function renderMindmap(tree, level = 0) {
  if (!tree) return ''
  let html = `${'  '.repeat(level)}- **${tree.title}**`
  if (tree.description) html += `: ${tree.description}`
  if (tree.children) {
    html += '\n' + tree.children.map(c => renderMindmap(c, level + 1)).join('\n')
  }
  return html
}

async function fetchResources() {
  try {
    const params = activeType.value === 'all' ? {} : { type: activeType.value }
    const res = await api.get('/api/resources', { params })
    resources.value = res.data
  } catch (e) {
    console.error('Failed to fetch resources:', e)
  }
}

function viewResource(item) {
  // 获取完整资源内容
  api.get(`/api/resources/${item.id}`).then(res => {
    currentResource.value = res.data
    dialogVisible.value = true
  })
}

onMounted(() => {
  fetchResources()
})
</script>

<style scoped>
.resource-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}
.resource-card:hover {
  transform: translateY(-2px);
}
.resource-type {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}
.resource-desc {
  color: #606266;
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.resource-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 12px;
  color: #c0c4cc;
}
.resource-detail {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
