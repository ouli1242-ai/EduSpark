<template>
  <div ref="cardRef" class="path-step-card" :class="{ visible: isVisible }">
    <div class="step-header">
      <div class="step-status" :class="status">
        <span v-if="status === 'completed'" class="status-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </span>
        <span v-else-if="status === 'current'" class="status-current" />
        <span v-else class="status-pending" />
      </div>
      <div class="step-info">
        <h4 class="step-topic">{{ topic }}</h4>
        <span class="step-time">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          {{ estimatedTime }}
        </span>
      </div>
    </div>

    <p v-if="description" class="step-desc">{{ description }}</p>

    <div v-if="knowledgePoints?.length" class="step-tags">
      <span v-for="kp in knowledgePoints" :key="kp" class="kp-tag">{{ kp }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

defineProps({
  topic: { type: String, required: true },
  description: { type: String, default: '' },
  estimatedTime: { type: String, default: '' },
  status: {
    type: String,
    default: 'pending',
    validator: v => ['completed', 'current', 'pending'].includes(v)
  },
  knowledgePoints: { type: Array, default: () => [] }
})

const cardRef = ref(null)
const isVisible = ref(false)

onMounted(() => {
  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        isVisible.value = true
        observer.disconnect()
      }
    },
    { threshold: 0.2 }
  )
  if (cardRef.value) observer.observe(cardRef.value)
})
</script>

<style scoped>
.path-step-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  opacity: 0;
  transform: translateX(-16px);
  transition: opacity 500ms ease,
              transform 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.path-step-card.visible {
  opacity: 1;
  transform: translateX(0);
}

.step-header {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

/* Status indicator */
.step-status {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.step-status.completed {
  background: rgba(52, 211, 153, 0.15);
  color: var(--color-success);
}

.step-status.current {
  background: var(--color-accent-primary-soft);
  box-shadow: 0 0 12px var(--color-accent-glow);
}

.step-status.pending {
  background: var(--color-bg-hover);
}

.status-current {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-accent-primary);
  animation: pulse-glow 1.5s ease-in-out infinite;
}

.status-pending {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-text-muted);
}

/* Info */
.step-info {
  flex: 1;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.step-topic {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.step-time {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.step-desc {
  margin: var(--space-2) 0 0 40px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-base);
}

.step-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin: var(--space-3) 0 0 40px;
}

.kp-tag {
  padding: 2px var(--space-2);
  background: var(--color-accent-primary-soft);
  border: 1px solid rgba(79, 140, 255, 0.15);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  color: var(--color-accent-primary);
  letter-spacing: var(--letter-spacing-normal);
}
</style>
