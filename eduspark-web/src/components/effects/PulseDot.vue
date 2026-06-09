<template>
  <span class="pulse-dot" :class="[status, { animated }]" :title="status" />
</template>

<script setup>
defineProps({
  status: {
    type: String,
    default: 'waiting', // waiting | running | done
    validator: v => ['waiting', 'running', 'done'].includes(v)
  },
  animated: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  transition: background var(--transition-fast),
              box-shadow var(--transition-fast);
}

.pulse-dot.waiting {
  background: var(--color-text-muted);
}

.pulse-dot.running {
  background: var(--color-accent-primary);
  box-shadow: 0 0 8px var(--color-accent-glow);
}

.pulse-dot.running.animated {
  animation: pulse-glow 1.5s ease-in-out infinite;
}

.pulse-dot.done {
  background: var(--color-success);
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.3);
}
</style>
