<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 雷达图 -->
      <el-col :span="12">
        <el-card>
          <template #header>学习画像雷达图</template>
          <div ref="radarChartRef" style="height: 400px;" />
        </el-card>
      </el-col>

      <!-- 画像详情 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>画像详情</span>
              <el-button text size="small" @click="refresh">刷新</el-button>
            </div>
          </template>
          <el-empty v-if="!hasProfile" description="暂无画像数据，请先开始对话" />
          <el-descriptions v-else :column="1" border>
            <el-descriptions-item label="知识基础">
              {{ formatKnowledge(profile.knowledge_base) }}
            </el-descriptions-item>
            <el-descriptions-item label="认知风格">
              {{ formatCognitive(profile.cognitive_style) }}
            </el-descriptions-item>
            <el-descriptions-item label="学习能力">
              {{ formatAbility(profile.learning_ability) }}
            </el-descriptions-item>
            <el-descriptions-item label="易错点模式">
              {{ formatErrors(profile.error_patterns) }}
            </el-descriptions-item>
            <el-descriptions-item label="学习目标">
              {{ formatGoals(profile.learning_goals) }}
            </el-descriptions-item>
            <el-descriptions-item label="学习偏好">
              {{ formatPrefs(profile.learning_preferences) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import api from '@/api/request'

const profile = ref(null)
const radarChartRef = ref(null)
let chart = null

const hasProfile = computed(() => {
  if (!profile.value) return false
  const p = profile.value
  return Object.values(p).some(v => v && typeof v === 'object' && Object.keys(v).length > 0)
})

// 格式化各维度显示
function formatKnowledge(kb) {
  if (!kb || Object.keys(kb).length === 0) return '待分析'
  const parts = []
  if (kb.mastered?.length) parts.push(`已掌握: ${kb.mastered.join(', ')}`)
  if (kb.weak?.length) parts.push(`薄弱: ${kb.weak.join(', ')}`)
  return parts.join(' | ') || '待分析'
}
function formatCognitive(cs) {
  if (!cs || Object.keys(cs).length === 0) return '待分析'
  if (cs.summary) return cs.summary
  const parts = []
  if (cs.visual !== undefined) parts.push(`视觉型 ${Math.round(cs.visual * 100)}%`)
  if (cs.auditory !== undefined) parts.push(`听觉型 ${Math.round(cs.auditory * 100)}%`)
  if (cs.kinesthetic !== undefined) parts.push(`动觉型 ${Math.round(cs.kinesthetic * 100)}%`)
  return parts.join(' | ') || '待分析'
}
function formatAbility(la) {
  if (!la || Object.keys(la).length === 0) return '待分析'
  if (la.summary) return la.summary
  const parts = []
  if (la.absorption_speed !== undefined) parts.push(`吸收速度: ${Math.round(la.absorption_speed * 100)}%`)
  if (la.understanding_depth !== undefined) parts.push(`理解深度: ${Math.round(la.understanding_depth * 100)}%`)
  if (la.transfer_ability !== undefined) parts.push(`迁移能力: ${Math.round(la.transfer_ability * 100)}%`)
  return parts.join(' | ') || '待分析'
}
function formatErrors(ep) {
  if (!ep || Object.keys(ep).length === 0) return '待分析'
  const parts = []
  if (ep.types?.length) parts.push(`类型: ${ep.types.join(', ')}`)
  if (ep.root_causes?.length) parts.push(`原因: ${ep.root_causes.join(', ')}`)
  return parts.join(' | ') || '待分析'
}
function formatGoals(lg) {
  if (!lg || Object.keys(lg).length === 0) return '待分析'
  const parts = []
  if (lg.short_term) parts.push(`短期: ${lg.short_term}`)
  if (lg.long_term) parts.push(`长期: ${lg.long_term}`)
  return parts.join(' | ') || '待分析'
}
function formatPrefs(lp) {
  if (!lp || Object.keys(lp).length === 0) return '待分析'
  const parts = []
  if (lp.resource_types?.length) parts.push(`偏好: ${lp.resource_types.join(', ')}`)
  if (lp.time_pref) parts.push(`时段: ${lp.time_pref}`)
  if (lp.difficulty_pref) parts.push(`难度: ${lp.difficulty_pref}`)
  return parts.join(' | ') || '待分析'
}

function getRadarValues(p) {
  if (!p) return [0, 0, 0, 0, 0, 0]
  return [
    p.knowledge_base?.score ?? (p.knowledge_base?.mastered?.length ? 0.5 : 0.2),
    p.cognitive_style?.visual ?? (p.cognitive_style?.summary ? 0.5 : 0.2),
    p.learning_ability?.absorption_speed ?? (p.learning_ability?.summary ? 0.5 : 0.2),
    p.error_patterns?.severity ?? (p.error_patterns?.types?.length ? 0.5 : 0.2),
    p.learning_goals?.short_term ? 0.7 : 0.2,
    p.learning_preferences?.resource_types?.length ? 0.6 : 0.2,
  ]
}

function initRadar(data) {
  if (!radarChartRef.value) return
  if (!chart) {
    chart = echarts.init(radarChartRef.value)
  }
  chart.setOption({
    radar: {
      indicator: [
        { name: '知识基础', max: 1 },
        { name: '认知风格', max: 1 },
        { name: '学习能力', max: 1 },
        { name: '易错点', max: 1 },
        { name: '学习目标', max: 1 },
        { name: '学习偏好', max: 1 },
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        areaStyle: { opacity: 0.2 },
        lineStyle: { width: 2 },
      }]
    }]
  })
}

async function refresh() {
  try {
    const res = await api.get('/api/profile')
    profile.value = res.data
    initRadar(getRadarValues(res.data))
  } catch (e) {
    console.error('Failed to fetch profile:', e)
  }
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.profile-page {
  padding: 0;
}
</style>
