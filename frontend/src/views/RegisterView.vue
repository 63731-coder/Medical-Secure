<script>
import axios from 'axios'

export default {
  name: "RegisterPage",
  data() {
    return {
      username: '',
      email: '',
      firstName: '',
      lastName: '',
      dateOfBirth: '',
      errorMessage: '',
      loading: false
    }
  },
  methods: {
    async handleRegister() {
      this.errorMessage = ''
      this.loading = true

      try {
        if (!this.username || !this.email || !this.firstName || !this.lastName) {
          this.errorMessage = 'Please fill all required fields'
          this.loading = false
          return
        }

        if (!this.dateOfBirth) {
          this.errorMessage = 'Date of birth is required'
          this.loading = false
          return
        }

        // Générer un mot de passe temporaire simple
        const tempPassword = this.generateTempPassword()

        const response = await axios.post('http://localhost:8000/api/auth/register/', {
          username: this.username,
          email: this.email,
          password: tempPassword,
          first_name: this.firstName,
          last_name: this.lastName,
          user_type: 'patient',  // Always patient
          date_of_birth: this.dateOfBirth,
          organisation: null
        })

        if (response.data) {
          // Afficher le message de succès
          alert(`✅ Account created successfully!\n\n🔐 Next steps:\n1. Enter your username: ${this.username}\n2. Setup your Passkey (fingerprint, Face ID, or security key)\n3. Future logins: Just use your Passkey!\n\n🔒 Passwordless = Maximum Security`)
          
          // Stocker pour référence
          sessionStorage.setItem('new_user', this.username)
          
          // Générer state pour sécurité CSRF
          const state = this.generateRandomString(32)
          sessionStorage.setItem('oauth_state', state)
          
          const keycloakAuthUrl = `http://localhost:8080/realms/medical-realm/protocol/openid-connect/auth`
          const params = new URLSearchParams({
            client_id: 'medical-app',
            redirect_uri: 'http://localhost:5173/callback',
            response_type: 'code',
            scope: 'openid profile email',
            state: state,
            login_hint: this.username,
            // Force immediate authentication (no SSO)
            prompt: 'login'
          })
          
          window.location.href = `${keycloakAuthUrl}?${params.toString()}`
        }
      } catch (error) {
        console.error('Registration error:', error)
        if (error.response?.data?.error) {
          this.errorMessage = error.response.data.error
        } else {
          this.errorMessage = 'Registration failed. Please try again.'
        }
        this.loading = false
      }
    },

    generateTempPassword() {
      // Génère un code simple de 6 caractères alphanumériques
      const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // Sans caractères ambigus
      let code = ''
      for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length))
      }
      // Retourne un password qui contient le code + suffixe pour respecter la policy
      return code + '!Aa1'
    },

    generateRandomString(length) {
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
      let result = ''
      for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length))
      }
      return result
    }
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-10 bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
    <div class="bg-blue-500 p-6 text-center">
      <h2 class="text-2xl font-bold text-white">Register</h2>
      <p class="text-blue-100 text-sm mt-1">* Required fields</p>
    </div>
    
    <form @submit.prevent="handleRegister" class="p-8 space-y-4">
      <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {{ errorMessage }}
      </div>



      <div>
        <label class="block text-white text-sm font-bold mb-2">Username *</label>
        <input type="text" v-model="username" required placeholder="Enter username" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div>
        <label class="block text-white text-sm font-bold mb-2">Email *</label>
        <input type="email" v-model="email" required placeholder="your.email@example.com" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div>
        <label class="block text-white text-sm font-bold mb-2">First name *</label>
        <input type="text" v-model="firstName" required placeholder="John" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div>
        <label class="block text-white text-sm font-bold mb-2">Last name *</label>
        <input type="text" v-model="lastName" required placeholder="Doe" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div>
        <label class="block text-white text-sm font-bold mb-2">Date of Birth *</label>
        <input type="date" v-model="dateOfBirth" required class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div v-if="userType === 'doctor'">
        <label class="block text-white text-sm font-bold mb-2">Organisation *</label>
        <input type="text" v-model="organisation" required placeholder="Hospital name" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div class="bg-white p-4 rounded flex items-center justify-center">
        <div class="flex items-center">
          <input type="checkbox" id="captcha" required class="mr-2" />
          <label for="captcha" class="text-gray-700">I'm not a robot</label>
        </div>
      </div>

      <button type="submit" :disabled="loading" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-lg transition duration-200 disabled:bg-gray-500">
        <span v-if="loading">Creating account...</span>
        <span v-else">Register</span>
      </button>

      <div class="text-center mt-4">
        <p class="text-sm text-gray-400">
          Already have an account? 
          <RouterLink to="/login" class="text-blue-400 hover:underline font-bold">Sign In</RouterLink>
        </p>
      </div>
    </form>
  </div>
</template>

<style scoped>
input[type="date"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
}
</style>
