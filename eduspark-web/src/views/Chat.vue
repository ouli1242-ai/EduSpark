<template>
  <div class="chat-container">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div v-if="messages.length === 0" class="empty-state">
        <h3>👋 你好，我是 EduSpark 学习助手</h3>
        <p>告诉我你的专业、学习目标或遇到的问题，我来帮你规划学习路径。</p>
      </div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role === 'user' ? 'user-message' : 'assistant-message']"
      >
        <div class="message-content" v-html="renderMarkdown(msg.content)" />
      </div>
      <!-- Agent 状态指示 -->
      <div v-if="agentStatusList.length > 0" class="agent-status">
        <div v-for="(agent, i) in agentStatusList" :key="i" class="agent-item">
          <span class="agent-name">
            <span v-if="agent.status === 'done'">✅</span>
            <span v-else-if="agent.status === 'running'">🔄</span>
            <span v-else>⏳</span>
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
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { useUserStore } from '@/stores/user'

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
const agentStatus = ref({})  // { agentName: { status, progress } }
const sessionId = ref(null)
const messageListRef = ref(null)

// Agent 名称映射
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

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  agentStatus.value = {}

  // 添加空的 assistant 消息用于流式填充
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
        session_id: sessionId.value,
      }),
    })

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    // 读取 SSE 流
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留不完整的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          handleSSEEvent(data, assistantMsg)
        } catch (e) {
          // 忽略解析错误
        }
      }
    }

    // 处理剩余 buffer
    if (buffer.startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.slice(6))
        handleSSEEvent(data, assistantMsg)
      } catch (e) {}
    }

  } catch (e) {
    console.error('Chat error:', e)
    assistantMsg.content += '\n\n❌ 请求失败，请稍后重试'
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
      // 画像已更新，可以通知 Profile 页面刷新
      console.log('Profile updated:', data.data)
      break

    case 'resource_generated':
      // 资源生成完成
      assistantMsg.content += `\n\n✅ 已生成：${AGENT_NAMES[data.resource_type] || data.resource_type}`
      scrollToBottom()
      break

    case 'path_generated':
      // 路径生成完成
      assistantMsg.content += `\n\n✅ 已生成学习路径：${data.data?.name || ''}`
      scrollToBottom()
      break

    case 'done':
      sessionId.value = data.session_id
      break
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.empty-state {
  text-align: center;
  color: #909399;
  margin-top: 120px;
}
.message {
  margin-bottom: 16px;
  max-width: 80%;
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
}
.assistant-message .message-content {
  background: #fff;
  border-radius: 12px 12px 12px 0;
  padding: 10px 16px;
  display: inline-block;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
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
