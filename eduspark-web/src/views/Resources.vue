<template>
  <div class="resources-page">
    <div class="page-header">
      <h1 class="page-title">学习资源</h1>
      <p class="page-subtitle">AI 生成的个性化学习资料</p>
    </div>

    <!-- Type Filters -->
    <div class="filter-bar">
      <button v-for="t in types" :key="t.key" :class="['filter-chip', { active: activeType === t.key }]" @click="activeType = t.key; fetchResources()">
        <span class="chip-dot" :style="{ background: t.color }"/>{{ t.label }}
      </button>
    </div>

    <div v-if="resources.length === 0" class="empty-section">
      <div class="empty-graphic" style="width:100px;height:100px;margin-bottom:20px;opacity:0.4">
        <svg viewBox="0 0 120 120" fill="none"><rect x="20" y="20" width="80" height="80" rx="8" stroke="#4f8cff" stroke-width="1.5"/><line x1="30" y1="40" x2="90" y2="40" stroke="#334155" stroke-width="1.5"/><line x1="30" y1="55" x2="70" y2="55" stroke="#334155" stroke-width="1.5"/><line x1="30" y1="70" x2="60" y2="70" stroke="#334155" stroke-width="1.5"/></svg>
      </div>
      <h3>暂无学习资源</h3>
      <p>在对话页面让 AI 帮你生成学习资源</p>
    </div>

    <!-- Resource Grid -->
    <div v-else class="resource-grid">
      <div class="res-card glass" v-for="item in resources" :key="item.id" @click="viewResource(item)">
        <div class="res-accent" :style="{ background: typeColor(item.type) }"/>
        <div class="res-body">
          <div class="res-type-row">
            <span class="res-type-badge" :style="{ background: typeColor(item.type) + '20', color: typeColor(item.type) }">{{ typeLabel(item.type) }}</span>
          </div>
          <h3 class="res-title">{{ item.title }}</h3>
          <p class="res-desc" v-if="item.description">{{ item.description }}</p>
          <div class="res-footer">
            <span class="res-date">{{ formatDate(item.created_at) }}</span>
            <span class="res-status" :class="item.status">{{ item.status === 'completed' ? '已完成' : item.status === 'generating' ? '生成中' : '失败' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="dialogVisible" :title="currentResource ? currentResource.title : ''" width="70%">
      <div v-if="currentResource" class="res-detail" v-html="renderContent(currentResource.content)"/>
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

const types = [
  { key: 'all', label: '全部', color: '#8896a9' },
  { key: 'document', label: '文档', color: '#4f8cff' },
  { key: 'quiz', label: '题目', color: '#fbbf24' },
  { key: 'mindmap', label: '思维导图', color: '#7c5cf0' },
  { key: 'code', label: '代码', color: '#34d399' },
  { key: 'video', label: '视频', color: '#f87171' },
]
const typeLabels = { document: '文档', quiz: '题目', mindmap: '思维导图', code: '代码案例', video: '视频' }
const typeColors = { document: '#4f8cff', quiz: '#fbbf24', mindmap: '#7c5cf0', code: '#34d399', video: '#f87171' }

function typeLabel(t) { return typeLabels[t] || t }
function typeColor(t) { return typeColors[t] || '#8896a9' }
function formatDate(iso) { return iso ? new Date(iso).toLocaleDateString('zh-CN') : '' }

function renderContent(content) {
  if (!content) return ''
  try {
    const data = JSON.parse(content)
    if (data.type === 'quiz' && data.questions) {
      return data.questions.map((q, i) => '<h4>' + (i+1) + '. ' + q.question + '</h4>' + (q.options ? '<ul>' + q.options.map(o => '<li>' + o + '</li>').join('') + '</ul>' : '') + '<p><strong>答案：</strong>' + q.answer + '</p>' + (q.explanation ? '<p><em>' + q.explanation + '</em></p>' : '')).join('<hr/>')
    }
    if (data.type === 'mindmap' && data.tree) {
      return '<pre style="white-space:pre-wrap;font-family:var(--font-family-mono)">' + JSON.stringify(data.tree, null, 2) + '</pre>'
    }
    if (data.content) return md.render(data.content)
  } catch (e) {}
  return md.render(content)
}

async function fetchResources() {
  try {
    const params = activeType.value === 'all' ? {} : { type: activeType.value }
    const res = await api.get('/api/resources', { params })
    resources.value = res.data
  } catch (e) { console.error('Failed:', e) }
}

async function viewResource(item) {
  try {
    const res = await api.get('/api/resources/' + item.id)
    currentResource.value = res.data
    dialogVisible.value = true
  } catch (e) {}
}

onMounted(() => { fetchResources() })
</script>

<style scoped>
.resources-page { position: relative; z-index: 1; }
.page-header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 24px; }
.page-title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 600; color: #e8ecf1; letter-spacing: -0.02em; }
.page-subtitle { color: #8896a9; font-size: 0.9375rem; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 28px; flex-wrap: wrap; }
.filter-chip { display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: rgba(17,24,39,0.65); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; color: #8896a9; font-size: 0.8125rem; cursor: pointer; transition: all 0.25s ease; }
.filter-chip:hover { border-color: rgba(255,255,255,0.12); }
.filter-chip.active { border-color: #4f8cff; color: #4f8cff; background: rgba(79,140,255,0.08); }
.chip-dot { width: 6px; height: 6px; border-radius: 50%; }
.empty-section { display: flex; flex-direction: column; align-items: center; padding: 80px 24px; text-align: center; }
.empty-section h3 { color: #e8ecf1; margin-bottom: 12px; }
.empty-section p { color: #8896a9; }
.resource-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 1024px) { .resource-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .resource-grid { grid-template-columns: 1fr; } }
.res-card { border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); background: rgba(17,24,39,0.65); backdrop-filter: blur(16px); overflow: hidden; cursor: pointer; transition: all 0.25s ease; }
.res-card:hover { border-color: rgba(255,255,255,0.1); transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.res-accent { height: 3px; }
.res-body { padding: 20px; }
.res-type-row { margin-bottom: 10px; }
.res-type-badge { font-size: 0.6875rem; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.res-title { font-size: 1rem; font-weight: 600; color: #e8ecf1; margin-bottom: 8px; }
.res-desc { font-size: 0.8125rem; color: #8896a9; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 12px; }
.res-footer { display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; }
.res-date { color: #5a677b; }
.res-status { padding: 2px 8px; border-radius: 8px; font-weight: 500; }
.res-status.completed { color: #34d399; background: rgba(52,211,153,0.1); }
.res-status.generating { color: #fbbf24; background: rgba(251,191,36,0.1); }
.res-status.failed { color: #f87171; background: rgba(248,113,113,0.1); }
.res-detail { max-height: 60vh; overflow-y: auto; color: #e8ecf1; }
</style>