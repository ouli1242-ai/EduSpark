// Composable: Profile data formatting
// Extracted from Profile.vue for reuse and testability

export function useProfileData() {
  const DIMENSION_LABELS = {
    knowledge_base: '知识基础',
    cognitive_style: '认知风格',
    learning_ability: '学习能力',
    error_patterns: '易错点模式',
    learning_goals: '学习目标',
    learning_preferences: '学习偏好'
  }

  function formatKnowledge(kb) {
    if (!kb || Object.keys(kb).length === 0) return '待分析'
    const parts = []
    if (kb.mastered?.length) parts.push(`已掌握: ${kb.mastered.join(', ')}`)
    if (kb.weak?.length) parts.push(`薄弱: ${kb.weak.join(', ')}`)
    if (kb.score !== undefined && Number.isFinite(kb.score)) parts.push(`综合评分: ${Math.round(kb.score * 100)}%`)
    return parts.join(' | ') || '待分析'
  }

  function formatCognitive(cs) {
    if (!cs || Object.keys(cs).length === 0) return '待分析'
    if (cs.summary) return cs.summary
    const parts = []
    if (cs.visual !== undefined && Number.isFinite(cs.visual)) parts.push(`视觉型 ${Math.round(cs.visual * 100)}%`)
    if (cs.auditory !== undefined && Number.isFinite(cs.auditory)) parts.push(`听觉型 ${Math.round(cs.auditory * 100)}%`)
    if (cs.kinesthetic !== undefined && Number.isFinite(cs.kinesthetic)) parts.push(`动觉型 ${Math.round(cs.kinesthetic * 100)}%`)
    return parts.join(' | ') || '待分析'
  }

  function formatAbility(la) {
    if (!la || Object.keys(la).length === 0) return '待分析'
    if (la.summary) return la.summary
    const parts = []
    if (la.absorption_speed !== undefined && Number.isFinite(la.absorption_speed)) parts.push(`吸收速度: ${Math.round(la.absorption_speed * 100)}%`)
    if (la.understanding_depth !== undefined && Number.isFinite(la.understanding_depth)) parts.push(`理解深度: ${Math.round(la.understanding_depth * 100)}%`)
    if (la.transfer_ability !== undefined && Number.isFinite(la.transfer_ability)) parts.push(`迁移能力: ${Math.round(la.transfer_ability * 100)}%`)
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
    const safe = (v, fallback) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1) ? v : fallback
    return [
      safe(p.knowledge_base?.score, p.knowledge_base?.mastered?.length ? 0.5 : 0.2),
      safe(p.cognitive_style?.visual, p.cognitive_style?.summary ? 0.5 : 0.2),
      safe(p.learning_ability?.absorption_speed, p.learning_ability?.summary ? 0.5 : 0.2),
      safe(p.error_patterns?.severity, p.error_patterns?.types?.length ? 0.5 : 0.2),
      p.learning_goals?.short_term ? 0.7 : 0.2,
      p.learning_preferences?.resource_types?.length ? 0.6 : 0.2,
    ]
  }

  function getDimensionScore(p, key) {
    if (!p) return 0
    const d = p[key]
    if (!d || Object.keys(d).length === 0) return 0
    if (d.score !== undefined && Number.isFinite(d.score)) return Math.round(d.score * 100)
    if (key === 'knowledge_base' && d.mastered?.length) return 50
    if (key === 'cognitive_style' && d.summary) return 50
    if (key === 'learning_ability' && d.summary) return 50
    if (key === 'error_patterns' && d.types?.length) return 40
    if (key === 'learning_goals' && d.short_term) return 70
    if (key === 'learning_preferences' && d.resource_types?.length) return 60
    return 10
  }

  function getFormattedDimension(p, key) {
    const formatters = {
      knowledge_base: formatKnowledge,
      cognitive_style: formatCognitive,
      learning_ability: formatAbility,
      error_patterns: formatErrors,
      learning_goals: formatGoals,
      learning_preferences: formatPrefs
    }
    const fn = formatters[key]
    return fn ? fn(p?.[key]) : '待分析'
  }

  return {
    DIMENSION_LABELS,
    formatKnowledge,
    formatCognitive,
    formatAbility,
    formatErrors,
    formatGoals,
    formatPrefs,
    getRadarValues,
    getDimensionScore,
    getFormattedDimension
  }
}
