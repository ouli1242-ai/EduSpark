<template>
  <span class="typewriter">
    <span class="text">{{ displayedText }}</span>
    <span class="cursor" :class="{ blink: isComplete }">|</span>
  </span>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  phrases: {
    type: Array,
    required: true
  },
  typeSpeed: {
    type: Number,
    default: 60
  },
  deleteSpeed: {
    type: Number,
    default: 30
  },
  pauseDuration: {
    type: Number,
    default: 2000
  }
})

const displayedText = ref('')
const isComplete = ref(false)
let timeoutId = null
let currentPhraseIndex = 0
let currentCharIndex = 0
let isDeleting = false

async function typeLoop() {
  const phrase = props.phrases[currentPhraseIndex]

  if (isDeleting) {
    if (currentCharIndex > 0) {
      currentCharIndex--
      displayedText.value = phrase.substring(0, currentCharIndex)
      isComplete.value = false
      timeoutId = setTimeout(typeLoop, props.deleteSpeed)
    } else {
      isDeleting = false
      currentPhraseIndex = (currentPhraseIndex + 1) % props.phrases.length
      isComplete.value = false
      timeoutId = setTimeout(typeLoop, props.typeSpeed)
    }
  } else {
    if (currentCharIndex < phrase.length) {
      currentCharIndex++
      displayedText.value = phrase.substring(0, currentCharIndex)
      isComplete.value = false
      timeoutId = setTimeout(typeLoop, props.typeSpeed)
    } else {
      isComplete.value = true
      timeoutId = setTimeout(() => {
        isDeleting = true
        isComplete.value = false
        typeLoop()
      }, props.pauseDuration)
    }
  }
}

onMounted(() => {
  timeoutId = setTimeout(typeLoop, 500)
})

onUnmounted(() => {
  clearTimeout(timeoutId)
})
</script>

<style scoped>
.typewriter {
  display: inline-block;
}

.text {
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.cursor {
  color: var(--color-accent-primary);
  font-weight: var(--font-weight-light, 300);
  margin-left: 2px;
  opacity: 0;
  transition: opacity 200ms;
}

.cursor.blink {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
