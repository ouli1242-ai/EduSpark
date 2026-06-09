<template>
  <div class="path-page">
    <div class="page-header">
      <h1 class="page-title">学习路径</h1>
      <p class="page-subtitle">个性化学习路线规划</p>
    </div>

    <div v-if="paths.length === 0 && !loading" class="empty-section">
      <div class="empty-graphic" style="width:100px;height:100px;margin-bottom:20px;opacity:0.4">
        <svg viewBox="0 0 120 120" fill="none"><circle cx="60" cy="20" r="6" stroke="#4f8cff" stroke-width="1.5"/><circle cx="30" cy="100" r="6" stroke="#7c5cf0" stroke-width="1.5"/><circle cx="90" cy="100" r="6" stroke="#34d399" stroke-width="1.5"/><line x1="60" y1="26" x2="30" y2="94" stroke="#334155" stroke-width="1" stroke-dasharray="4 3"/><line x1="60" y1="26" x2="90" y2="94" stroke="#334155" stroke-width="1" stroke-dasharray="4 3"/><line x1="30" y1="94" x2="90" y2="94" stroke="#334155" stroke-width="1"/></svg>
      </div>
      <h3>暂无学习路径</h3>
      <p>在对话页面让 AI 帮你规划学习路线</p>
    </div>

    <div v-else class="path-list">
      <div class="path-card glass" v-for="path in paths" :key="path.id" @click="viewPath(path)">
        <div class="path-progress-ring">
          <svg viewBox="0 0 60 60">
            <circle cx="30" cy="30" r="26" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="3"/>
            <circle cx="30" cy="30" r="26" fill="none" :stroke="progressColor(path.progress)" stroke-width="3"
              :stroke-dasharray="163.36" :stroke-dashoffset="163.36 * (1 - path.progress)"
              stroke-linecap="round" transform="rotate(-90 30 30)" style="transition: stroke-dashoffset 0.8s ease"/>
          </svg>
          <span class="progress-text">{{ Number.isFinite(path.progress) ? Math.round(path.progress * 100) : 0 }}%</span>
        </div>
        <div class="path-body">
          <h3 class="path-name">{{ path.name }}</h3>
          <p class="path-course">{{ path.course }} · {{ path.steps_count || 0 }} 个步骤</p>
          <div class="path-bar">
            <div class="path-fill" :style="{ width: path.progress * 100 + '%' }"/>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="currentPath ? currentPath.name : ''" width="60%">
      <template v-if="currentPath">
        <el-timeline>
          <el-timeline-item v-for="step in currentPath.steps" :key="step.order"
            :type="step.status === 'completed' ? 'success' : step.status === 'current' ? 'primary' : 'info'"
            :hollow="step.status === 'pending'">
            <div class="step-content">
              <h4>{{ step.topic }}</h4>
              <p v-if="step.description">{{ step.description }}</p>
              <span class="step-time">{{ step.estimated_time }}</span>
              <div v-if="step.knowledge_points && step.knowledge_points.length" class="step-kps">
                <span v-for="kp in step.knowledge_points" :key="kp" class="kp-tag">{{ kp }}</span>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '@/api/request'
import { usePathRefresh } from '@/composables/usePathRefresh'

const paths = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentPath = ref(null)
const { refreshCounter } = usePathRefresh()

function progressColor(p) {
  if (p >= 0.8) return '#34d399'
  if (p >= 0.4) return '#4f8cff'
  return '#fbbf24'
}

async function fetchPaths() {
  loading.value = true
  try { const res = await api.get('/api/path'); paths.value = res.data } catch (e) {} finally { loading.value = false }
}

async function viewPath(pathSummary) {
  try { const res = await api.get('/api/path/' + pathSummary.id); currentPath.value = res.data; dialogVisible.value = true } catch (e) {}
}

onMounted(() => { fetchPaths() })
watch(refreshCounter, () => { fetchPaths() })
</script>

<style scoped>
.path-page { position: relative; z-index: 1; }
.page-header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 28px; }
.page-title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 600; color: #e8ecf1; letter-spacing: -0.02em; }
.page-subtitle { color: #8896a9; font-size: 0.9375rem; }
.empty-section { display: flex; flex-direction: column; align-items: center; padding: 80px 24px; text-align: center; }
.empty-section h3 { color: #e8ecf1; margin-bottom: 12px; }
.empty-section p { color: #8896a9; }
.path-list { display: flex; flex-direction: column; gap: 16px; }
.path-card { display: flex; align-items: center; gap: 20px; padding: 20px 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); background: rgba(17,24,39,0.65); backdrop-filter: blur(16px); cursor: pointer; transition: all 0.25s ease; }
.path-card:hover { border-color: rgba(255,255,255,0.1); transform: translateX(4px); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.path-progress-ring { position: relative; width: 60px; height: 60px; flex-shrink: 0; }
.path-progress-ring svg { width: 100%; height: 100%; }
.progress-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: #e8ecf1; }
.path-body { flex: 1; min-width: 0; }
.path-name { font-size: 1.0625rem; font-weight: 600; color: #e8ecf1; margin-bottom: 4px; }
.path-course { font-size: 0.8125rem; color: #8896a9; margin-bottom: 10px; }
.path-bar { height: 4px; background: rgba(255,255,255,0.06); border-radius: 10px; overflow: hidden; }
.path-fill { height: 100%; background: linear-gradient(90deg, #7c5cf0, #4f8cff); border-radius: 10px; transition: width 600ms ease; }
.step-content h4 { color: #e8ecf1; margin: 0 0 4px 0; }
.step-content p { color: #8896a9; font-size: 0.8125rem; margin: 0 0 4px 0; }
.step-time { color: #5a677b; font-size: 0.75rem; }
.step-kps { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
.kp-tag { padding: 2px 10px; background: rgba(79,140,255,0.1); border-radius: 12px; color: #4f8cff; font-size: 0.6875rem; }
</style>