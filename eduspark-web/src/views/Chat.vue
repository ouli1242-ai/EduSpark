<template>
  <div class="chat-view">
    <!-- 对话历史侧栏 -->
    <aside class="session-sidebar">
      <div class="session-header">
        <h3 class="session-title">对话历史</h3>
        <button class="btn-new-session" @click="newSession">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>新建</span>
        </button>
      </div>

      <div class="session-list" v-if="sessions.length > 0">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          :class="['session-item', { active: s.session_id === currentSessionId }]"
        >
          <div class="session-info" @click="loadSession(s)">
            <div class="session-item-title">{{ s.title || '对话' }}</div>
            <div class="session-meta">
              <span>{{ s.messages.length }} 条消息</span>
            </div>
          </div>
          <button
            class="session-delete"
            @click.stop="deleteSession(s.session_id)"
            title="删除"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>

      <div v-else class="session-empty">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" class="empty-icon">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <p>暂无对话记录</p>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <!-- Empty State -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon-wrapper">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 10L26 22L38 24L26 26L24 38L22 26L10 24L22 22L24 10Z" fill="url(#empty-grad)" />
              <defs>
                <linearGradient id="empty-grad" x1="10" y1="10" x2="38" y2="38">
                  <stop stop-color="#4f8cff" />
                  <stop offset="1" stop-color="#7c5cf0" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h2 class="empty-title">你好，我是 EduSpark 学习助手</h2>
          <p class="empty-desc">
            告诉我你的专业、学习目标或遇到的问题，我来帮你规划学习路径。
          </p>
          <div class="empty-suggestions">
            <button
              v-for="q in quickQuestions"
              :key="q"
              class="suggestion-chip"
              @click="sendQuickMessage(q)"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <!-- Messages -->
        <TransitionGroup name="message-slide">
          <MessageBubble
            v-for="(msg, i) in messages"
            :key="i"
            :role="msg.role"
            :content="msg.content"
            :initial="userInitial"
            :is-streaming="msg.role === 'assistant' && i === messages.length - 1 && sending"
          />
        </TransitionGroup>

        <!-- Agent Status -->
        <AgentStatusPanel :agents="agentStatusList" />
      </div>

      <!-- 输入区 -->
      <ChatInput
        v-model="inputText"
        :disabled="sending"
        placeholder="输入你的问题..."
        @send="sendMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import AgentStatusPanel from '@/components/chat/AgentStatusPanel.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { usePathRefresh } from '@/composables/usePathRefresh'

const userStore = useUserStore()
const { notifyPathGenerated } = usePathRefresh()
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const agentStatus = ref({})
const currentSessionId = ref(null)
const sessions = ref([])
const messageListRef = ref(null)
let abortController = null

const AGENT_NAMES = {
  profile: '画像分析',
  resource: '资源生成',
  document: '文档生成',
  quiz: '题目生成',
  mindmap: '思维导图',
  code: '代码案例',
  video: '视频脚本',
  path: '路径规划',
  orchestrator: '编排器',
  tutor: '智能辅导',
  evaluation: '学习评估',
}

const quickQuestions = [
  '介绍一下机器学习',
  '帮我规划学习路线',
  '生成决策树的讲解文档',
  '分析一下我的学习情况'
]

const userInitial = computed(() => {
  return userStore.username ? userStore.username.charAt(0).toUpperCase() : 'U'
})

const agentStatusList = computed(() => {
  return Object.entries(agentStatus.value).map(([key, val]) => ({
    name: AGENT_NAMES[key] || key,
    status: val.status,
    progress: val.progress || (val.status === 'done' ? 100 : val.status === 'running' ? 50 : 0),
  }))
})

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function sendQuickMessage(text) {
  inputText.value = text
  sendMessage()
}

// ── Session Management ──

async function fetchSessions() {
  try {
    const res = await api.get('/api/chat/history')
    sessions.value = res.data
  } catch (e) {
    console.error('加载历史失败:', e)
  }
}

async function deleteSession(sessionId) {
  try {
    await ElMessageBox.confirm('删除后无法恢复，确定删除此对话？', '确认删除')
    await api.delete(`/api/chat/history/${sessionId}`)
    ElMessage.success('已删除')
    if (currentSessionId.value === sessionId) {
      newSession()
    }
    fetchSessions()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function abortActiveChat() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  sending.value = false
}

function newSession() {
  abortActiveChat()
  currentSessionId.value = null
  messages.value = []
  agentStatus.value = {}
}

function loadSession(session) {
  abortActiveChat()
  currentSessionId.value = session.session_id
  messages.value = session.messages.map(m => ({
    role: m.role,
    content: m.content,
  }))
  agentStatus.value = {}
  scrollToBottom()
}

onMounted(() => {
  fetchSessions()
})

// ── SSE Chat ──

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  // Abort any previous in-flight request
  abortActiveChat()

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  agentStatus.value = {}

  messages.value.push({ role: 'assistant', content: '' })
  const assistantMsg = messages.value[messages.value.length - 1]

  abortController = new AbortController()

  try {
    const base = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
    const url = `${base}/api/chat`

    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({
        message: text,
        session_id: currentSessionId.value,
      }),
      signal: abortController.signal,
    })

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          handleSSEEvent(data, assistantMsg)
        } catch (e) {}
      }
    }

    if (buffer.startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.slice(6))
        handleSSEEvent(data, assistantMsg)
      } catch (e) {}
    }

    fetchSessions()

  } catch (e) {
    if (e.name === 'AbortError') {
      // User switched conversation — clean exit, no error message
      console.log('[Chat] SSE aborted by user')
      return
    }
    console.error('Chat error:', e)
    assistantMsg.content += '\n\n请求失败，请稍后重试'
  } finally {
    sending.value = false
    abortController = null
    scrollToBottom()
  }
}

function handleSSEEvent(data, assistantMsg) {
  switch (data.type) {
    case 'chunk':
      assistantMsg.content += data.content
      scrollToBottom()
      break

    case 'agent_status':
      agentStatus.value[data.agent] = {
        status: data.status,
        progress: data.progress,
        message: data.message,
      }
      break

    case 'profile_updated':
      console.log('Profile updated:', data.data)
      break

    case 'resource_generated':
      assistantMsg.content += `\n\n已生成：${AGENT_NAMES[data.resource_type] || data.resource_type}`
      scrollToBottom()
      break

    case 'path_generated':
      assistantMsg.content += `\n\n已生成学习路径：${data.data?.name || ''}`
      notifyPathGenerated()
      scrollToBottom()
      break

    case 'tutor_analysis':
      assistantMsg.content += `\n\n> 问题类型：${data.question_type || ''} | 涉及：${(data.knowledge_points || []).join('、')} | 难度：${data.difficulty || ''}`
      scrollToBottom()
      break

    case 'evaluation_report':
      assistantMsg.content += `\n\n---\n📊 **学习评估报告已生成**`
      scrollToBottom()
      break

    case 'done':
      currentSessionId.value = data.session_id
      break

    case 'error':
      assistantMsg.content += `\n\n> ⚠️ ${data.message || '生成失败，请重试'}`
      if (data.agent) {
        agentStatus.value[data.agent] = {
          status: 'failed',
          progress: 0,
          message: data.message,
        }
      }
      break
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: calc(100vh - 60px - var(--space-12));
  gap: 0;
  position: relative;
  z-index: 1;
}

/* ── Session Sidebar ── */
.session-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.session-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: var(--letter-spacing-normal);
}

.btn-new-session {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  background: var(--color-accent-primary);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: var(--font-size-xs);
  font-family: var(--font-family);
  cursor: pointer;
  transition: background var(--transition-fast),
              box-shadow var(--transition-fast);
}

.btn-new-session:hover {
  background: #6ba3ff;
  box-shadow: var(--glow-accent);
}

/* Session List */
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.session-item {
  display: flex;
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-bottom: 2px;
}

.session-item:hover {
  background: var(--color-bg-hover);
}

.session-item.active {
  background: var(--color-accent-primary-soft);
  border-left: 3px solid var(--color-accent-primary);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-item-title {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.session-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.session-delete {
  flex-shrink: 0;
  padding: 4px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition-fast),
              color var(--transition-fast);
  border-radius: var(--radius-sm);
}

.session-item:hover .session-delete {
  opacity: 1;
}

.session-delete:hover {
  color: var(--color-danger);
}

/* Session Empty */
.session-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.empty-icon {
  opacity: 0.3;
}

/* ── Chat Main ── */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  scroll-behavior: smooth;
}

/* ── Empty State ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-6);
  text-align: center;
}

.empty-icon-wrapper {
  width: 64px;
  height: 64px;
  margin-bottom: var(--space-6);
  opacity: 0.3;
}

.empty-icon-wrapper svg {
  width: 100%;
  height: 100%;
}

.empty-title {
  font-family: var(--font-family-display);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.empty-desc {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 400px;
  line-height: var(--line-height-relaxed);
  margin-bottom: var(--space-8);
}

.empty-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
  max-width: 500px;
}

.suggestion-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  cursor: pointer;
  transition: border-color var(--transition-fast),
              color var(--transition-fast),
              background var(--transition-fast);
}

.suggestion-chip:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
  background: var(--color-accent-primary-soft);
}
</style>
