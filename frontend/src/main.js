import { createApp } from 'vue'
import App from './App.vue'
import router from './router'; // <-- Import du routeur

const app = createApp(App)

app.use(router) // <-- Utilisation du routeur

app.mount('#app')