import { createApp } from 'vue'
import App from './App.vue'

// Create and mount the Vue application
const app = createApp(App)

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm)
  console.error('Error Info:', info)
}

// Global warning handler
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Vue Warning:', msg)
  console.warn('Component:', vm)
  console.warn('Trace:', trace)
}

// Mount the app
app.mount('#app') 