<template>
  <div class="learning-path-page">
    <el-empty v-if="paths.length === 0 && !loading" description="暂无学习路径，请在对话中生成" />

    <!-- 路径列表 -->
    <el-card v-for="path in paths" :key="path.id" class="path-card" @click="viewPath(path)">
      <div class="path-header">
        <h4>{{ path.name }}</h4>
        <el-tag>{{ Math.round(path.progress * 100) }}%</el-tag>
      </div>
      <p class="path-course">{{ path.course }} · {{ path.steps_count }} 个步骤</p>
      <el-progress :percentage="Math.round(path.progress * 100)" :stroke-width="8" />
    </el-card>

    <!-- 路径详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="currentPath?.name" width="60%">
      <template v-if="currentPath">
        <el-timeline>
          <el-timeline-item
            v-for="step in currentPath.steps"
            :key="step.order"
            :type="stepStatusType(step.status)"
            :hollow="step.status === 'pending'"
          >
            <div class="step-content">
              <h4>{{ step.topic }}</h4>
              <p v-if="step.description">{{ step.description }}</p>
              <p class="step-time">预计学习时间：{{ step.estimated_time }}</p>
              <div v-if="step.knowledge_points?.length" class="step-kps">
                <el-tag v-for="kp in step.knowledge_points" :key="kp" size="small" class="kp-tag">
                  {{ kp }}
                </el-tag>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/request'

const paths = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentPath = ref(null)

function stepStatusType(status) {
  const map = { completed: 'success', current: 'primary', pending: 'info' }
  return map[status] || 'info'
}

async function fetchPaths() {
  loading.value = true
  try {
    const res = await api.get('/api/path')
    paths.value = res.data
  } catch (e) {
    console.error('Failed to fetch paths:', e)
  } finally {
    loading.value = false
  }
}

async function viewPath(pathSummary) {
  try {
    const res = await api.get(`/api/path/${pathSummary.id}`)
    currentPath.value = res.data
    dialogVisible.value = true
  } catch (e) {
    console.error('Failed to fetch path detail:', e)
  }
}

onMounted(() => {
  fetchPaths()
})
</script>

<style scoped>
.path-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}
.path-card:hover {
  transform: translateY(-2px);
}
.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.path-header h4 {
  margin: 0;
}
.path-course {
  color: #909399;
  font-size: 13px;
  margin-bottom: 12px;
}
.step-content h4 {
  margin: 0 0 4px 0;
}
.step-content p {
  color: #606266;
  font-size: 13px;
  margin: 0 0 4px 0;
}
.step-time {
  color: #909399;
}
.kp-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>
