<template>
  <div class="resource-card" @click="$emit('click')">
    <!-- Type accent bar -->
    <div class="card-accent" :class="type" />

    <div class="card-body">
      <!-- Type icon + label -->
      <div class="card-type">
        <span class="type-icon">{{ typeIcon }}</span>
        <span class="type-label">{{ typeLabel }}</span>
      </div>

      <!-- Title -->
      <h4 class="card-title">{{ title }}</h4>

      <!-- Description -->
      <p class="card-desc">{{ description || '暂无描述' }}</p>

      <!-- Footer -->
      <div class="card-footer">
        <span class="card-date">{{ date }}</span>
        <span class="status-badge" :class="status">
          <span class="status-dot" />
          {{ statusText }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  type: { type: String, default: 'document' },
  status: { type: String, default: 'completed' },
  date: { type: String, default: '' }
})

defineEmits(['click'])

const typeConfig = {
  document: { icon: '📄', label: '文档' },
  quiz: { icon: '📝', label: '题目' },
  mindmap: { icon: '🧠', label: '思维导图' },
  code: { icon: '💻', label: '代码案例' },
  video: { icon: '🎬', label: '视频' }
}

const typeIcon = computed(() => typeConfig[props.type]?.icon || '📦')
const typeLabel = computed(() => typeConfig[props.type]?.label || props.type)

const statusText = computed(() => {
  const map = { completed: '已完成', generating: '生成中', failed: '失败' }
  return map[props.status] || props.status
})
</script>

<style scoped>
.resource-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--transition-base),
              border-color var(--transition-base),
              box-shadow var(--transition-base);
}

.resource-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-border-default);
  box-shadow: var(--shadow-lg), var(--glow-accent);
}

/* Type accent bar */
.card-accent {
  height: 3px;
  transition: height var(--transition-fast);
}

.resource-card:hover .card-accent {
  height: 4px;
}

.card-accent.document { background: var(--color-type-document); }
.card-accent.quiz { background: var(--color-type-quiz); }
.card-accent.mindmap { background: var(--color-type-mindmap); }
.card-accent.code { background: var(--color-type-code); }
.card-accent.video { background: var(--color-type-video); }

/* Body */
.card-body {
  padding: var(--space-5);
}

.card-type {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.type-icon {
  font-size: var(--font-size-lg);
}

.type-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

.card-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--line-height-tight);
}

.card-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-base);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 0 var(--space-4) 0;
  min-height: 2.4em;
}

/* Footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-date {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
}

.status-badge.completed {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.status-badge.generating {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.status-badge.failed {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--radius-full);
  background: currentColor;
}

.status-badge.generating .status-dot {
  animation: pulse-glow 1.5s ease-in-out infinite;
}
</style>
