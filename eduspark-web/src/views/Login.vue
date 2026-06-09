<template>
  <div class="login-page">
    <!-- Background Effects -->
    <ParticleField />
    <AnimatedGradient />

    <!-- Split Layout -->
    <div class="login-layout">
      <!-- Left: Brand Section -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M24 10L26 22L38 24L26 26L24 38L22 26L10 24L22 22L24 10Z"
                fill="url(#logo-grad)"
                class="logo-spark"
              />
              <circle cx="24" cy="24" r="19" stroke="url(#logo-grad)" stroke-width="1.5" fill="none" opacity="0.3" />
              <defs>
                <linearGradient id="logo-grad" x1="10" y1="10" x2="38" y2="38">
                  <stop stop-color="#4f8cff" />
                  <stop offset="1" stop-color="#7c5cf0" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <h1 class="brand-name">EduSpark</h1>
          <p class="brand-tagline">
            <TypewriterText
              :phrases="[
                '个性化学习',
                '多智能体协作',
                'AI 驱动的教育',
                '你的专属学习助手'
              ]"
              :type-speed="80"
              :delete-speed="40"
              :pause-duration="2500"
            />
          </p>
          <p class="brand-desc">
            基于多智能体的个性化教育平台，通过 AI 对话了解你的学习特点，自动生成定制化学习内容和路径。
          </p>

          <!-- Feature Pills -->
          <div class="feature-pills">
            <span class="pill">
              <span class="pill-dot" />
              智能画像分析
            </span>
            <span class="pill">
              <span class="pill-dot" />
              个性化辅导
            </span>
            <span class="pill">
              <span class="pill-dot" />
              多资源生成
            </span>
          </div>
        </div>
      </div>

      <!-- Right: Auth Card -->
      <div class="form-section">
        <div class="glass-card">
          <!-- Custom Tabs -->
          <div class="tab-switcher">
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'login' }"
              @click="activeTab = 'login'"
            >
              登录
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'register' }"
              @click="activeTab = 'register'"
            >
              注册
            </button>
            <div class="tab-indicator" :class="activeTab" />
          </div>

          <!-- Login Form -->
          <Transition name="fade" mode="out-in">
            <div v-if="activeTab === 'login'" key="login" class="form-body">
              <div class="input-group">
                <label class="input-label">用户名</label>
                <div class="input-wrapper">
                  <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <input
                    v-model="loginForm.username"
                    type="text"
                    placeholder="请输入用户名"
                    class="form-input"
                    @keyup.enter="handleLogin"
                  />
                </div>
              </div>
              <div class="input-group">
                <label class="input-label">密码</label>
                <div class="input-wrapper">
                  <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  <input
                    v-model="loginForm.password"
                    :type="showLoginPwd ? 'text' : 'password'"
                    placeholder="请输入密码"
                    class="form-input"
                    @keyup.enter="handleLogin"
                  />
                  <button class="toggle-pwd" @click="showLoginPwd = !showLoginPwd">
                    <svg v-if="!showLoginPwd" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
              </div>
              <button
                class="submit-btn"
                :disabled="loading"
                @click="handleLogin"
              >
                <span v-if="!loading">登 录</span>
                <span v-else class="loading-dots">
                  <span class="dot" />
                  <span class="dot" />
                  <span class="dot" />
                </span>
              </button>
            </div>

            <!-- Register Form -->
            <div v-else key="register" class="form-body">
              <div class="input-group">
                <label class="input-label">用户名</label>
                <div class="input-wrapper">
                  <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <input
                    v-model="registerForm.username"
                    type="text"
                    placeholder="请输入用户名"
                    class="form-input"
                    @keyup.enter="handleRegister"
                  />
                </div>
              </div>
              <div class="input-group">
                <label class="input-label">密码</label>
                <div class="input-wrapper">
                  <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  <input
                    v-model="registerForm.password"
                    :type="showRegPwd ? 'text' : 'password'"
                    placeholder="请输入密码"
                    class="form-input"
                    @keyup.enter="handleRegister"
                  />
                  <button class="toggle-pwd" @click="showRegPwd = !showRegPwd">
                    <svg v-if="!showRegPwd" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
              </div>
              <button
                class="submit-btn"
                :disabled="loading"
                @click="handleRegister"
              >
                <span v-if="!loading">注 册</span>
                <span v-else class="loading-dots">
                  <span class="dot" />
                  <span class="dot" />
                  <span class="dot" />
                </span>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import ParticleField from '@/components/background/ParticleField.vue'
import AnimatedGradient from '@/components/background/AnimatedGradient.vue'
import TypewriterText from '@/components/effects/TypewriterText.vue'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('login')
const loading = ref(false)
const showLoginPwd = ref(false)
const showRegPwd = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '' })

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.register(registerForm.username, registerForm.password)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
  position: relative;
  overflow: hidden;
}

.login-layout {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
}

/* ── Left: Brand Section ── */
.brand-section {
  flex: 1.1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
}

.brand-content {
  max-width: 480px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  margin-bottom: var(--space-8);
  color: var(--color-accent-primary);
  filter: drop-shadow(0 0 20px rgba(79, 140, 255, 0.3));
}

.brand-logo svg {
  width: 100%;
  height: 100%;
}

.logo-spark {
  animation: pulse-glow 2.5s ease-in-out infinite;
}

.brand-name {
  font-family: var(--font-family-display);
  font-size: var(--font-size-hero);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: var(--letter-spacing-tight);
  line-height: 1.1;
  margin-bottom: var(--space-4);
}

.brand-tagline {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--space-6);
  min-height: 36px;
  color: var(--color-text-primary);
}

.brand-desc {
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-8);
  max-width: 420px;
}

.feature-pills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.pill {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-glass);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  backdrop-filter: blur(8px);
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-accent-primary);
  box-shadow: 0 0 6px var(--color-accent-glow);
}

/* ── Right: Form Section ── */
.form-section {
  flex: 0.9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(79, 140, 255, 0.02) 50%,
    rgba(124, 92, 240, 0.03) 100%
  );
}

.glass-card {
  width: 100%;
  max-width: 400px;
  padding: var(--space-10);
  background: var(--color-bg-glass);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl), var(--glow-accent);
}

/* ── Tab Switcher ── */
.tab-switcher {
  display: flex;
  position: relative;
  margin-bottom: var(--space-8);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  padding: 3px;
}

.tab-btn {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family);
  cursor: pointer;
  position: relative;
  z-index: 1;
  transition: color var(--transition-fast);
  border-radius: var(--radius-sm);
}

.tab-btn.active {
  color: var(--color-text-primary);
}

.tab-indicator {
  position: absolute;
  top: 3px;
  bottom: 3px;
  width: calc(50% - 3px);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  transition: transform var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.tab-indicator.login {
  transform: translateX(0);
}

.tab-indicator.register {
  transform: translateX(100%);
}

/* ── Form ── */
.form-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.input-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  letter-spacing: var(--letter-spacing-normal);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: var(--space-3);
  color: var(--color-text-muted);
  pointer-events: none;
  flex-shrink: 0;
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  padding-left: 42px;
  padding-right: 40px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  letter-spacing: var(--letter-spacing-normal);
  transition: border-color var(--transition-fast),
              box-shadow var(--transition-fast);
  outline: none;
}

.form-input::placeholder {
  color: var(--color-text-muted);
}

.form-input:focus {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px var(--color-accent-primary-soft);
}

.toggle-pwd {
  position: absolute;
  right: var(--space-3);
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  transition: color var(--transition-fast);
}

.toggle-pwd:hover {
  color: var(--color-text-secondary);
}

/* ── Submit Button ── */
.submit-btn {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  margin-top: var(--space-2);
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  font-family: var(--font-family);
  letter-spacing: var(--letter-spacing-wide);
  cursor: pointer;
  transition: transform var(--transition-fast),
              box-shadow var(--transition-fast),
              opacity var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--glow-accent), 0 4px 16px rgba(79, 140, 255, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Loading Dots */
.loading-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: white;
  animation: blink 1.4s ease-in-out infinite both;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* ── Tab Content Transition ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .brand-section {
    display: none;
  }

  .form-section {
    flex: 1;
    background: none;
  }

  .glass-card {
    max-width: 100%;
    padding: var(--space-8);
  }
}
</style>
