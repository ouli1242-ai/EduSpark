<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="page-title">{{ title }}</h1>
      <span class="page-breadcrumb">
        <template v-for="(crumb, i) in breadcrumbs" :key="i">
          <span v-if="i > 0" class="crumb-sep">/</span>
          <span class="crumb-item">{{ crumb }}</span>
        </template>
      </span>
    </div>

    <div class="header-right">
      <span class="username">{{ userStore.username }}</span>
      <button class="btn-logout" @click="handleLogout">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        <span>退出</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const titleMap = {
  '/': '智能对话',
  '/profile': '学习画像',
  '/resources': '学习资源',
  '/path': '学习路径'
}

const title = computed(() => titleMap[route.path] || 'EduSpark')

const breadcrumbs = computed(() => {
  const crumbs = ['EduSpark']
  if (route.path !== '/') {
    crumbs.push(titleMap[route.path] || route.path)
  }
  return crumbs
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 var(--space-6);
  background: rgba(10, 14, 23, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border-subtle);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
}

.page-title {
  font-family: var(--font-family-display);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  letter-spacing: var(--letter-spacing-tight);
  margin: 0;
}

.page-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.crumb-sep {
  opacity: 0.4;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.username {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  cursor: pointer;
  transition: color var(--transition-fast),
              border-color var(--transition-fast),
              background var(--transition-fast);
}

.btn-logout:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
  background: var(--color-danger-soft);
}

.btn-logout svg {
  flex-shrink: 0;
}
</style>
