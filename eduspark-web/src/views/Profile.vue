<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">学习画像</h1>
      <p class="page-subtitle">AI 自动构建的六维度学习画像</p>
      <button class="btn-refresh" @click="refresh">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        刷新
      </button>
    </div>
    <div v-if="!hasProfile" class="empty-section">
      <div class="empty-graphic">
        <svg viewBox="0 0 120 120" fill="none"><circle cx="60" cy="60" r="50" stroke="#334155" stroke-width="1" stroke-dasharray="4 4"/><path d="M60 20L62 38L80 40L62 42L60 60L58 42L40 40L58 38L60 20Z" fill="#4f8cff" opacity="0.4"/></svg>
      </div>
      <h3>暂无画像数据</h3>
      <p>去对话页面与 AI 聊聊你的学习背景，系统会自动分析你的学习画像</p>
      <router-link to="/" class="cta-link">开始对话</router-link>
    </div>
    <div v-else class="profile-content">
      <div class="radar-card glass"><h3 class="card-title">六维雷达图</h3><div ref="radarChartRef" class="radar-chart"/></div>
      <div class="dimension-grid">
        <div class="dim-card glass" v-for="dim in dimensions" :key="dim.key">
          <div class="dim-icon" :style="{ background: dim.color }"><span v-html="dim.icon"/></div>
          <div class="dim-body">
            <div class="dim-header"><span class="dim-name">{{ dim.label }}</span><span class="dim-score">{{ Number.isFinite(dim.score) ? Math.round(dim.score * 100) : 0 }}%</span></div>
            <div class="dim-bar"><div class="dim-fill" :style="{ width: (Number.isFinite(dim.score) ? dim.score : 0) * 100 + '%', background: dim.color }"/></div>
            <p class="dim-desc">{{ dim.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api/request'

const profile = ref(null)
const radarChartRef = ref(null)
let chart = null

const hasProfile = computed(() => {
  if (!profile.value) return false
  return Object.values(profile.value).some(v => v && typeof v === 'object' && Object.keys(v).length > 0)
})

function fmtK(kb) {
  if (!kb || Object.keys(kb).length === 0) return '待分析'
  const p = []
  if (kb.mastered && kb.mastered.length) p.push('已掌握: ' + kb.mastered.join(', '))
  if (kb.weak && kb.weak.length) p.push('薄弱: ' + kb.weak.join(', '))
  return p.join(' | ') || '待分析'
}
function fmtC(cs) {
  if (!cs || Object.keys(cs).length === 0) return '待分析'
  if (cs.summary) return cs.summary
  const p = []
  if (cs.visual !== undefined) p.push('视觉 ' + Math.round(cs.visual * 100) + '%')
  if (cs.auditory !== undefined) p.push('听觉 ' + Math.round(cs.auditory * 100) + '%')
  if (cs.kinesthetic !== undefined) p.push('动觉 ' + Math.round(cs.kinesthetic * 100) + '%')
  return p.join(' | ') || '待分析'
}
function fmtA(la) {
  if (!la || Object.keys(la).length === 0) return '待分析'
  if (la.summary) return la.summary
  const p = []
  if (la.absorption_speed !== undefined) p.push('吸收: ' + Math.round(la.absorption_speed * 100) + '%')
  if (la.understanding_depth !== undefined) p.push('深度: ' + Math.round(la.understanding_depth * 100) + '%')
  if (la.transfer_ability !== undefined) p.push('迁移: ' + Math.round(la.transfer_ability * 100) + '%')
  return p.join(' | ') || '待分析'
}
function fmtE(ep) {
  if (!ep || Object.keys(ep).length === 0) return '待分析'
  const p = []
  if (ep.types && ep.types.length) p.push('类型: ' + ep.types.join(', '))
  if (ep.root_causes && ep.root_causes.length) p.push('原因: ' + ep.root_causes.join(', '))
  return p.join(' | ') || '待分析'
}
function fmtG(lg) {
  if (!lg || Object.keys(lg).length === 0) return '待分析'
  const p = []
  if (lg.short_term) p.push('短期: ' + lg.short_term)
  if (lg.long_term) p.push('长期: ' + lg.long_term)
  return p.join(' | ') || '待分析'
}
function fmtP(lp) {
  if (!lp || Object.keys(lp).length === 0) return '待分析'
  const p = []
  if (lp.resource_types && lp.resource_types.length) p.push('资源: ' + lp.resource_types.join(', '))
  if (lp.time_pref) p.push('时段: ' + lp.time_pref)
  if (lp.difficulty_pref) p.push('难度: ' + lp.difficulty_pref)
  return p.join(' | ') || '待分析'
}

function safeScore(v, fallback = 0.15) {
  if (typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 1) return fallback
  return v
}

function getRadarValues(p) {
  if (!p) return [0, 0, 0, 0, 0, 0]
  return [
    safeScore(p.knowledge_base?.score, p.knowledge_base?.mastered?.length ? 0.5 : 0.15),
    safeScore(p.cognitive_style?.visual, p.cognitive_style?.summary ? 0.5 : 0.15),
    safeScore(p.learning_ability?.absorption_speed, p.learning_ability?.summary ? 0.5 : 0.15),
    safeScore(p.error_patterns?.severity, p.error_patterns?.types?.length ? 0.4 : 0.2),
    p.learning_goals?.short_term ? 0.65 : 0.15,
    p.learning_preferences?.resource_types?.length ? 0.55 : 0.15,
  ]
}

const dimensions = computed(() => {
  const p = profile.value
  if (!p) return []
  const vals = getRadarValues(p)
  return [
    { key: 'kb', label: '知识基础', icon: '&#9679;', color: '#4f8cff', score: vals[0], desc: fmtK(p.knowledge_base) },
    { key: 'cs', label: '认知风格', icon: '&#9670;', color: '#7c5cf0', score: vals[1], desc: fmtC(p.cognitive_style) },
    { key: 'la', label: '学习能力', icon: '&#9650;', color: '#34d399', score: vals[2], desc: fmtA(p.learning_ability) },
    { key: 'ep', label: '易错点', icon: '&#9888;', color: '#fbbf24', score: vals[3], desc: fmtE(p.error_patterns) },
    { key: 'lg', label: '学习目标', icon: '&#9733;', color: '#f87171', score: vals[4], desc: fmtG(p.learning_goals) },
    { key: 'lp', label: '学习偏好', icon: '&#9825;', color: '#a78bfa', score: vals[5], desc: fmtP(p.learning_preferences) },
  ]
})

function initRadar(data) {
  if (!radarChartRef.value) return
  if (!chart) chart = echarts.init(radarChartRef.value)
  chart.setOption({
    radar: {
      center: ['50%', '52%'], radius: '70%',
      indicator: [
        { name: '知识基础', max: 1 }, { name: '认知风格', max: 1 },
        { name: '学习能力', max: 1 }, { name: '易错点', max: 1 },
        { name: '学习目标', max: 1 }, { name: '学习偏好', max: 1 },
      ],
      axisName: { color: '#8896a9', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(79,140,255,0.02)', 'rgba(79,140,255,0.04)'] } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: [{
      type: 'radar', data: [{ value: data, name: '画像',
        areaStyle: { color: 'rgba(79,140,255,0.15)' },
        lineStyle: { color: '#4f8cff', width: 2 },
        itemStyle: { color: '#4f8cff' }, symbol: 'circle', symbolSize: 5,
      }]
    }]
  })
}

async function refresh() {
  try {
    const res = await api.get('/api/profile')
    profile.value = res.data
    await nextTick()
    initRadar(getRadarValues(res.data))
  } catch (e) { console.error('Failed:', e) }
}

onMounted(() => { refresh() })
</script>

<style scoped>
.profile-page { position: relative; z-index: 1; }
.page-header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 32px; }
.page-title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 600; color: #e8ecf1; letter-spacing: -0.02em; }
.page-subtitle { color: #8896a9; font-size: 0.9375rem; }
.btn-refresh { margin-left: auto; display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: rgba(17,24,39,0.65); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; color: #8896a9; font-size: 0.8125rem; cursor: pointer; transition: all 0.25s ease; }
.btn-refresh:hover { border-color: #4f8cff; color: #4f8cff; }
.empty-section { display: flex; flex-direction: column; align-items: center; padding: 80px 24px; text-align: center; }
.empty-graphic { width: 120px; height: 120px; margin-bottom: 24px; opacity: 0.5; }
.empty-section h3 { color: #e8ecf1; margin-bottom: 12px; }
.empty-section p { color: #8896a9; max-width: 380px; margin-bottom: 24px; line-height: 1.75; }
.cta-link { color: #4f8cff; text-decoration: none; font-weight: 500; }
.profile-content { display: flex; flex-direction: column; gap: 24px; }
.radar-card { padding: 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); background: rgba(17,24,39,0.65); backdrop-filter: blur(16px); }
.card-title { font-size: 1rem; font-weight: 600; color: #e8ecf1; margin-bottom: 16px; }
.radar-chart { height: 380px; }
.dimension-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 1024px) { .dimension-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .dimension-grid { grid-template-columns: 1fr; } }
.dim-card { display: flex; gap: 16px; padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); background: rgba(17,24,39,0.65); backdrop-filter: blur(16px); transition: border-color 0.25s ease, transform 0.25s ease; }
.dim-card:hover { border-color: rgba(255,255,255,0.1); transform: translateY(-2px); }
.dim-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.125rem; color: white; }
.dim-body { flex: 1; min-width: 0; }
.dim-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.dim-name { font-size: 0.8125rem; font-weight: 600; color: #e8ecf1; }
.dim-score { font-size: 0.75rem; font-weight: 700; color: #4f8cff; }
.dim-bar { height: 4px; background: rgba(255,255,255,0.06); border-radius: 10px; overflow: hidden; margin-bottom: 8px; }
.dim-fill { height: 100%; border-radius: 10px; transition: width 600ms ease; }
.dim-desc { font-size: 0.75rem; color: #8896a9; line-height: 1.5; }
</style>