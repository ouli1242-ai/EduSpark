<template>
  <div class="chat-view">
    <!-- 对话历史侧栏 -->
    <div class="session-sidebar">
      <div class="session-header">
        <h3>对话历史</h3>
        <el-button size="small" type="primary" @click="newSession">新建对话</el-button>
      </div>
      <div class="session-list" v-if="sessions.length > 0">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          :class="['session-item', { active: s.session_id === currentSessionId }]"
        >
          <div class="session-info" @click="loadSession(s)">
            <div class="session-title">{{ s.title || '对话' }}</div>
            <div class="session-msg-count">{{ s.messages.length }} 条消息</div>
          </div>
          <el-button
            text
            type="danger"
            size="small"
            class="session-delete"
            @click.stop="deleteSession(s.session_id)"
            title="删除此对话"
          >✕</el-button>
        </div>
      </div>
      <div v-else class="session-empty">
        <p>暂无对话记录</p>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div v-if="messages.length === 0" class="empty-state">
          <h3>你好，我是 EduSpark 学习助手</h3>
          <p>告诉我你的专业、学习目标或遇到的问题，我来帮你规划学习路径。</p>
        </div>
        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['message', msg.role === 'user' ? 'user-message' : 'assistant-message']"
        >
          <div class="message-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div class="message-content" v-html="renderMarkdown(msg.content)" />
        </div>
        <!-- Agent 状态指示 -->
        <div v-if="agentStatusList.length > 0" class="agent-status">
          <div v-for="(agent, i) in agentStatusList" :key="i" class="agent-item">
            <span class="agent-name">
              <span v-if="agent.status === 'done'">[OK]</span>
              <span v-else-if="agent.status === 'running'">[运行中]</span>
              <span v-else>[等待]</span>
              {{ agent.name }}
            </span>
            <el-progress
              :percentage="agent.progress"
              :status="agent.status === 'done' ? 'success' : undefined"
              :stroke-width="6"
            />
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题... (Ctrl+Enter 发送)"
          @keydown.enter.ctrl="sendMessage"
        />
        <el-button type="primary" :loading="sending" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { useUserStore } from '@/stores/user'
import api from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const md = new MarkdownIt({
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(str, { language: lang }).value
    }
    return ''
  }
})

const userStore = useUserStore()
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const agentStatus = ref({})
const currentSessionId = ref(null)
const sessions = ref([])
const messageListRef = ref(null)

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
}

const agentStatusList = computed(() => {
  return Object.entries(agentStatus.value).map(([key, val]) => ({
    name: AGENT_NAMES[key] || key,
    status: val.status,
    progress: val.progress || (val.status === 'done' ? 100 : val.status === 'running' ? 50 : 0),
  }))
})

function renderMarkdown(text) {
  return md.render(text || '')
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 加载对话历史列表
async function fetchSessions() {
  try {
    const res = await api.get('/api/chat/history')
    sessions.value = res.data
  } catch (e) {
    console.error('加载历史失败:', e)
  }
}

// 删除历史会话
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

// 新建对话
function newSession() {
  currentSessionId.value = null
  messages.value = []
  agentStatus.value = {}
}

// 加载某个历史会话
function loadSession(session) {
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

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  agentStatus.value = {}

  // 当前消息如果没有 session_id，新建会话自动生成 session_id
  // 如果有正在查看的历史会话，复用其 session_id

  messages.value.push({ role: 'assistant', content: '' })
  const assistantMsg = messages.value[messages.value.length - 1]

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

    // 刷新历史列表
    fetchSessions()

  } catch (e) {
    console.error('Chat error:', e)
    assistantMsg.content += '\n\n请求失败，请稍后重试'
  } finally {
    sending.value = false
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
      scrollToBottom()
      break

    case 'done':
      currentSessionId.value = data.session_id
      break
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: calc(100vh - 120px);
  gap: 16px;
}
.session-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
}
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.session-header h3 {
  margin: 0;
  font-size: 16px;
}
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.session-item:hover {
  background: #f0f2f5;
}
.session-item.active {
  background: #ecf5ff;
}
.session-info {
  flex: 1;
  min-width: 0;
}
.session-delete {
  flex-shrink: 0;
  margin-left: 4px;
  opacity: 0;
}
.session-item:hover .session-delete {
  opacity: 1;
}
.session-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-msg-count {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
.session-empty {
  text-align: center;
  color: #909399;
  margin-top: 40px;
}
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.empty-state {
  text-align: center;
  color: #909399;
  margin-top: 120px;
}
.message {
  margin-bottom: 20px;
  max-width: 75%;
}
.user-message {
  margin-left: auto;
  text-align: right;
}
.user-message .message-content {
  background: #409eff;
  color: #fff;
  border-radius: 12px 12px 0 12px;
  padding: 10px 16px;
  display: inline-block;
  text-align: left;
}
.assistant-message .message-content {
  background: #f5f7fa;
  border-radius: 12px 12px 12px 0;
  padding: 10px 16px;
  display: inline-block;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.message-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.agent-status {
  background: #f0f9ff;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}
.agent-item {
  margin-bottom: 8px;
}
.agent-name {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  display: block;
}
.input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
  align-items: flex-end;
}
</style>
