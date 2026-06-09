<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="layout-main">
      <AppHeader />
      <main class="layout-content">
        <router-view v-slot="{ Component, route }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.layout-main {
  flex: 1;
  margin-left: 64px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* Sidebar overlays on hover-expand, content margin stays at 64px */

.layout-content {
  flex: 1;
  padding: var(--space-6);
  background: var(--color-bg-primary);
  position: relative;
}

/* Subtle dot grid pattern overlay */
.layout-content::before {
  content: '';
  position: fixed;
  inset: 0;
  left: 64px;
  background-image: radial-gradient(
    circle,
    rgba(79, 140, 255, 0.03) 1px,
    transparent 1px
  );
  background-size: 24px 24px;
  pointer-events: none;
  z-index: 0;
}
</style>
