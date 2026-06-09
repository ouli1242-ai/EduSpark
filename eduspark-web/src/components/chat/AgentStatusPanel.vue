<template>
  <Transition name="fade">
    <div v-if="agents.length > 0" class="agent-panel">
      <div v-for="agent in agents" :key="agent.name" class="agent-card" :class="agent.status">
        <div class="agent-indicator">
          <span v-if="agent.status === 'running'" class="pulse-dot" />
          <span v-else-if="agent.status === 'done'" class="done-check">&#10003;</span>
          <span v-else-if="agent.status === 'failed'" class="failed-mark">&#10007;</span>
          <span v-else class="wait-dot" />
        </div>
        <div class="agent-body">
          <span class="agent-name">{{ agent.name }}</span>
          <div v-if="agent.message" class="agent-message">{{ agent.message }}</div>
          <div class="agent-track">
            <div class="agent-fill" :class="agent.status" :style="{ width: agent.progress + '%' }" />
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({ agents: { type: Array, default: () => [] } })
</script>

<style scoped>
.agent-panel {
  display: flex; flex-wrap: wrap; gap: var(--space-3);
  padding: var(--space-4); margin-top: var(--space-2);
  background: var(--color-bg-glass);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(12px);
}
.agent-card { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); background: var(--color-bg-elevated); border-radius: var(--radius-md); min-width: 160px; transition: opacity var(--transition-fast); }
.agent-card.done { opacity: 0.7; }
.agent-card.failed { border: 1px solid rgba(248,113,113,0.25); }
.agent-indicator { width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-accent-primary); box-shadow: 0 0 8px var(--color-accent-glow); animation: pulse-ring 1.5s ease-in-out infinite; }
.done-check { width: 20px; height: 20px; font-size: 12px; line-height: 20px; text-align: center; border-radius: 50%; background: var(--color-success); color: white; }
.failed-mark { width: 20px; height: 20px; font-size: 12px; line-height: 20px; text-align: center; border-radius: 50%; background: #f87171; color: white; }
.wait-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-text-muted); }
.agent-body { flex: 1; min-width: 0; }
.agent-name { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: 4px; display: block; }
.agent-message { font-size: 10px; color: #f87171; margin-bottom: 4px; line-height: 1.3; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-track { height: 3px; background: rgba(255,255,255,0.06); border-radius: 10px; overflow: hidden; }
.agent-fill { height: 100%; border-radius: 10px; transition: width 500ms ease; background: var(--color-accent-primary); }
.agent-fill.done { background: var(--color-success); }
.agent-fill.failed { background: #f87171; }
.fade-enter-active { transition: opacity 300ms ease; }
.fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
