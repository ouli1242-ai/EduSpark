<template>
  <div class="app-root dark-theme">
    <router-view v-slot="{ Component, route }">
      <Transition :name="route.meta.transition || 'fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
  </div>
</template>

<script setup>
// Root app component — applies dark theme and global transitions
</script>

<style scoped>
.app-root {
  width: 100%;
  min-height: 100vh;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}
</style>
