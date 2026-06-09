<template>
  <span class="streaming-cursor" :class="{ active: isStreaming }">|</span>
</template>

<script setup>
defineProps({
  isStreaming: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.streaming-cursor {
  display: inline;
  color: var(--color-accent-primary);
  font-weight: 300;
  margin-left: 1px;
  opacity: 0;
}

.streaming-cursor.active {
  animation: blink 0.8s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
