<template>
  <div :class="['message-bubble', role]">
    <div class="bubble-avatar" v-if="role === 'assistant'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L14 10L22 12L14 14L12 22L10 14L2 12L10 10L12 2Z" />
      </svg>
    </div>
    <div class="bubble-body">
      <div class="bubble-content" v-html="rendered" />
      <span v-if="isStreaming" class="streaming-cursor">|</span>
    </div>
    <div class="bubble-avatar user-avatar" v-if="role === 'user'">
      {{ initial }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
  initial: { type: String, default: 'U' },
  isStreaming: { type: Boolean, default: false }
})

const md = new MarkdownIt({
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return '<pre class="code-block"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
    }
    return '<pre class="code-block"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

const rendered = computed(() => md.render(props.content || ''))
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  max-width: 82%;
  animation: fade-in-up 350ms ease forwards;
}
.message-bubble.user { margin-left: auto; flex-direction: row-reverse; }
.message-bubble.assistant { margin-right: auto; }

.bubble-avatar {
  width: 34px; height: 34px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.message-bubble.assistant .bubble-avatar {
  background: var(--color-accent-primary-soft);
  color: var(--color-accent-primary);
}
.user-avatar {
  background: var(--color-accent-secondary-soft);
  color: var(--color-accent-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
}

.bubble-body { position: relative; line-height: var(--line-height-relaxed); overflow-wrap: break-word; word-break: break-word; }
.bubble-content {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  overflow: hidden;
}
.message-bubble.user .bubble-content {
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  color: white;
  border-bottom-right-radius: var(--radius-sm);
}
.message-bubble.assistant .bubble-content {
  background: var(--color-bg-glass);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
  border-bottom-left-radius: var(--radius-sm);
  backdrop-filter: blur(12px);
}
.bubble-content :deep(pre.code-block) {
  background: rgba(0,0,0,0.35);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--space-3) var(--space-4);
  margin: var(--space-2) 0;
  overflow-x: auto;
}
.bubble-content :deep(code) { font-family: var(--font-family-mono); font-size: var(--font-size-sm); }
.bubble-content :deep(p) { margin-bottom: var(--space-2); }
.bubble-content :deep(p:last-child) { margin-bottom: 0; }
.bubble-content :deep(ul),
.bubble-content :deep(ol) {
  padding-left: 1.6em;
  margin: var(--space-2) 0;
  list-style-position: outside;
}
.bubble-content :deep(li) {
  margin-bottom: var(--space-1);
  line-height: var(--line-height-relaxed);
}
.bubble-content :deep(li:last-child) { margin-bottom: 0; }
.bubble-content :deep(ul) { list-style-type: disc; }
.bubble-content :deep(ol) { list-style-type: decimal; }
.bubble-content :deep(blockquote) {
  border-left: 3px solid var(--color-accent-primary);
  padding-left: var(--space-3);
  margin: var(--space-2) 0;
  color: var(--color-text-secondary);
  opacity: 0.9;
}
.bubble-content :deep(strong) { font-weight: var(--font-weight-semibold); color: var(--color-text-primary); }
.bubble-content :deep(h1), .bubble-content :deep(h2), .bubble-content :deep(h3) {
  margin: var(--space-3) 0 var(--space-1);
  font-weight: var(--font-weight-semibold);
  line-height: 1.3;
}
.bubble-content :deep(h1) { font-size: 1.25em; }
.bubble-content :deep(h2) { font-size: 1.1em; }
.bubble-content :deep(h3) { font-size: 1em; }
.bubble-content :deep(hr) { border: none; border-top: 1px solid var(--color-border-subtle); margin: var(--space-3) 0; }
.bubble-content :deep(table) {
  border-collapse: collapse; margin: var(--space-2) 0; font-size: var(--font-size-sm);
}
.bubble-content :deep(th), .bubble-content :deep(td) {
  border: 1px solid var(--color-border-subtle); padding: var(--space-1) var(--space-2); text-align: left;
}
.bubble-content :deep(th) { background: var(--color-bg-hover); }
.streaming-cursor { color: var(--color-accent-primary); animation: blink 0.8s step-end infinite; }
</style>
