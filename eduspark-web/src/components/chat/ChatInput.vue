<template>
  <div class="chat-input-wrapper glass">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="chat-textarea"
      rows="1"
      @input="onInput"
      @keydown.enter.exact="$emit('send')"
    />
    <button
      class="send-btn"
      :disabled="!modelValue.trim() || disabled"
      @click="$emit('send')"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '输入你的问题...' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'send'])
const textareaRef = ref(null)

function onInput(e) {
  emit('update:modelValue', e.target.value)
  autoResize()
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

defineExpose({ focus: () => textareaRef.value?.focus() })
</script>

<style scoped>
.chat-input-wrapper {
  display: flex; align-items: flex-end; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
}
.chat-textarea {
  flex: 1; background: transparent; border: none;
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  resize: none; outline: none;
  line-height: 1.6;
  min-height: 24px; max-height: 150px;
}
.chat-textarea::placeholder { color: var(--color-text-muted); }
.chat-textarea:disabled { opacity: 0.5; }
.send-btn {
  width: 38px; height: 38px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-accent-primary);
  border: none; border-radius: var(--radius-md);
  color: white; cursor: pointer;
  transition: all var(--transition-fast);
}
.send-btn:hover:not(:disabled) {
  background: #6ba3ff;
  box-shadow: var(--glow-accent);
  transform: scale(1.05);
}
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; }
</style>
