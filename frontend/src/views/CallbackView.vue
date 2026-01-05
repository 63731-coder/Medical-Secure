<template>
  <div class="oauth-callback">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Authenticating with Keycloak...</p>
    </div>
    
    <div v-if="error" class="error">
      <h2>Authentication Failed</h2>
      <p>{{ error }}</p>
      <button @click="goToLogin">Try Again</button>
    </div>
  </div>
</template>

<script>
import keycloakAuth from '@/services/keycloakAuth'
import api from '@/services/api'
import { deriveKeyFromUser } from '@/utils/crypto'
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'

export default {
  name: 'CallbackView',
  
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const error = ref(null)
    
    onMounted(async () => {
      try {
        // Get authorization code and state from URL
        const urlParams = new URLSearchParams(window.location.search)
        const code = urlParams.get('code')
        const state = urlParams.get('state')
        
        if (!code) {
          throw new Error('No authorization code received')
        }
        
        // Exchange code for tokens
        await keycloakAuth.handleCallback(code, state)
        
        // Fetch user profile to get username
        const response = await api.get('/auth/me/')
        const userData = response.data
        
        // Generate deterministic encryption key based on username
        // Use username (not keycloak_id) to match the key used during registration
        deriveKeyFromUser(userData.username)
        
        // Redirect to home page
        router.push('/')
      } catch (err) {
        error.value = err.message || 'Authentication failed'
        loading.value = false
      }
    })
    
    const goToLogin = () => {
      router.push('/login')
    }
    
    return {
      loading,
      error,
      goToLogin
    }
  }
}
</script>

<style scoped>
.oauth-callback {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.loading, .error {
  background: white;
  padding: 3rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  text-align: center;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error h2 {
  color: #e74c3c;
  margin-bottom: 1rem;
}

button {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  background: #5568d3;
}
</style>
