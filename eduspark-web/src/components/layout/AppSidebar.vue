<template>
  <aside
    class="app-sidebar"
    :class="{ expanded: isExpanded }"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <Logo :collapsed="!isExpanded" />

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon">
          <component :is="item.icon" />
        </span>
        <span v-show="isExpanded" class="nav-label">{{ item.label }}</span>
        <span v-if="isActive(item.path)" class="active-indicator" />
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <router-link
        to="/profile"
        class="user-avatar"
        :class="{ active: isActive('/profile') }"
      >
        <span class="avatar-initial">{{ userInitial }}</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ChatDotRound, User, Document, MapLocation } from '@element-plus/icons-vue'
import Logo from '@/components/branding/Logo.vue'

const route = useRoute()
const userStore = useUserStore()

const isExpanded = ref(false)

const navItems = [
  { path: '/', label: '智能对话', icon: ChatDotRound },
  { path: '/profile', label: '学习画像', icon: User },
  { path: '/resources', label: '学习资源', icon: Document },
  { path: '/path', label: '学习路径', icon: MapLocation }
]

const userInitial = computed(() => {
  return userStore.username ? userStore.username.charAt(0).toUpperCase() : 'U'
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 64px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  z-index: var(--z-sidebar);
  transition: width var(--transition-base);
  overflow: hidden;
}

.app-sidebar.expanded {
  width: 220px;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  margin-top: var(--space-4);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  position: relative;
  transition: color var(--transition-fast),
              background var(--transition-fast);
  white-space: nowrap;
}

.nav-item:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
}

.nav-item.active {
  color: var(--color-accent-primary);
  background: var(--color-accent-primary-soft);
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 25%;
  bottom: 25%;
  width: 3px;
  background: var(--color-accent-primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  box-shadow: var(--glow-accent);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: var(--font-size-lg);
}

.nav-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  letter-spacing: var(--letter-spacing-normal);
}

/* Footer */
.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  justify-content: center;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-full);
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: border-color var(--transition-fast),
              box-shadow var(--transition-fast);
}

.user-avatar:hover,
.user-avatar.active {
  border-color: var(--color-accent-primary);
  box-shadow: var(--glow-accent);
}

.avatar-initial {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-accent-primary);
}
</style>
