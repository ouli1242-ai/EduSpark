<template>
  <div class="logo-mark" :class="{ collapsed }">
    <div class="logo-icon">
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Spark core -->
        <path
          d="M20 8L22 18L32 20L22 22L20 32L18 22L8 20L18 18L20 8Z"
          fill="currentColor"
          class="spark-core"
        />
        <!-- Orbital ring -->
        <circle
          cx="20" cy="20" r="16"
          stroke="currentColor"
          stroke-width="1.5"
          fill="none"
          opacity="0.3"
          class="orbital-ring"
        />
        <!-- Outer dots -->
        <circle cx="20" cy="4" r="2" fill="currentColor" opacity="0.6" class="orbit-dot dot-1" />
        <circle cx="20" cy="36" r="2" fill="currentColor" opacity="0.6" class="orbit-dot dot-2" />
      </svg>
    </div>
    <Transition name="fade">
      <div v-if="!collapsed" class="logo-text">
        <span class="logo-name">EduSpark</span>
        <span class="logo-subtitle">Learning Intelligence</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.logo-mark {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: var(--color-accent-primary);
  transition: color var(--transition-base);
}

.logo-mark:hover .logo-icon {
  color: #6ba3ff;
}

.spark-core {
  animation: pulse-glow 2.5s ease-in-out infinite;
  transform-origin: center;
}

.orbital-ring {
  animation: spin 20s linear infinite;
  transform-origin: center;
}

.orbit-dot {
  animation: float 3s ease-in-out infinite;
}

.dot-2 {
  animation-delay: -1.5s;
}

.logo-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.logo-name {
  font-family: var(--font-family-display);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: var(--letter-spacing-tight);
  line-height: 1.2;
}

.logo-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
}

/* Collapsed state */
.logo-mark.collapsed {
  justify-content: center;
  padding: var(--space-3);
}

.logo-mark.collapsed .logo-icon {
  width: 36px;
  height: 36px;
}

/* Transition for text */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
