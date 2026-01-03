<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Medical Secure Login</h1>
      <p class="subtitle">Passwordless authentication with WebAuthn</p>
      
      <div class="login-methods">
        <!-- Keycloak WebAuthn Login -->
        <button @click="loginWithKeycloak" class="btn-primary">
          <span class="icon">🔐</span>
          Login with Keycloak
        </button>
      </div>

      <div class="register-link">
        <p>Don't have an account?</p>
        <router-link to="/register" class="btn-register">
          Create Account
        </router-link>
      </div>
      
      <div class="info-box">
        <p><strong>WebAuthn Benefits:</strong></p>
        <ul>
          <li>✅ No passwords to remember</li>
          <li>✅ Biometric authentication (Face ID, Touch ID)</li>
          <li>✅ Phishing-resistant</li>
          <li>✅ FIDO2 certified security</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import keycloakAuth from '@/services/keycloakAuth'
import axios from 'axios'
import { deriveKeyFromPassword } from '../utils/crypto'

export default {
  name: 'LoginView',
  
  data() {
    return {
      username: '',
      password: '',
      errorMessage: ''
    }
  },
  
  methods: {
    /**
     * Login with Keycloak (WebAuthn)
     */
    async loginWithKeycloak() {
      try {
        await keycloakAuth.login()
        // User will be redirected to Keycloak
      } catch (error) {
        this.errorMessage = 'Failed to initiate Keycloak login'
        console.error(error)
      }
    },
    
    /**
     * Legacy password login (deprecated, for backwards compatibility)
     */
    async handleLegacyLogin() {
      this.errorMessage = ''
      
      try {
        const response = await axios.post('http://127.0.0.1:8000/api/login/', {
          username: this.username,
          password: this.password
        })
        
        // Store token
        localStorage.setItem('access_token', response.data.token)
        localStorage.setItem('userId', response.data.user_id)
        localStorage.setItem('userType', response.data.user_type)
        
        // Generate encryption key from password
        const encryptionKey = await deriveKeyFromPassword(this.password, this.username)
        const keyString = Array.from(new Uint8Array(await crypto.subtle.exportKey('raw', encryptionKey)))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('')
        
        sessionStorage.setItem('encryptionKey', keyString)
        
        // Redirect to home
        this.$router.push('/')
      } catch (error) {
        this.errorMessage = error.response?.data?.error || 'Login failed'
        console.error(error)
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.login-card {
  background: white;
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 100%;
}

h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  text-align: center;
}

.subtitle {
  color: #7f8c8d;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 0.95rem;
}

.login-methods {
  margin-bottom: 2rem;
}

.btn-primary {
  width: 100%;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary .icon {
  font-size: 1.5rem;
}

.divider {
  text-align: center;
  margin: 1.5rem 0;
  position: relative;
}

.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background: #ddd;
}

.divider::before {
  left: 0;
}

.divider::after {
  right: 0;
}

.divider span {
  background: white;
  padding: 0 1rem;
  color: #95a5a6;
  font-size: 0.9rem;
}

.legacy-login {
  margin-top: 1rem;
}

.legacy-login summary {
  color: #7f8c8d;
  cursor: pointer;
  padding: 0.5rem;
  text-align: center;
  font-size: 0.9rem;
}

.legacy-login summary:hover {
  color: #667eea;
}

.legacy-form {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #2c3e50;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.btn-secondary {
  width: 100%;
  padding: 0.75rem;
  background: #95a5a6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.register-link {
  text-align: center;
  margin: 1.5rem 0;
  padding: 1.5rem 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

.register-link p {
  margin: 0 0 1rem 0;
  color: #7f8c8d;
  font-size: 0.95rem;
}

.btn-register {
  display: inline-block;
  padding: 0.75rem 2rem;
  background: #27ae60;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-register:hover {
  background: #229954;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
}

.info-box {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.info-box p {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
  font-weight: 600;
}

.info-box ul {
  margin: 0;
  padding-left: 1.5rem;
  color: #34495e;
}

.info-box li {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}
</style>
