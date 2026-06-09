import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'

// Design system tokens — must be first
import './styles/tokens.css'
import 'element-plus/dist/index.css'
import './styles/element-overrides.css'
import './styles/transitions.css'
import './styles/animations.css'

// Code highlighting
import 'highlight.js/styles/github.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
