import { createApp } from 'vue'
import App from './App.vue'
import router from './router';
import './assets/main.css'
import { VueReCaptcha } from 'vue-recaptcha-v3'

const app = createApp(App)

app.use(router)

// Google reCAPTCHA v3
app.use(VueReCaptcha, {
  siteKey: '6Lfb-T8sAAAAAO3_j-UIGfplkAIL4IZ_dyOaZ8Tu',
  loaderOptions: {
    autoHideBadge: false,
    explicitRenderParameters: {
      badge: 'bottomright'
    }
  }
})

app.mount('#app')