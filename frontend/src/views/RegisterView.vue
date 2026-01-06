<script>
import api from '@/services/api'
import { useReCaptcha } from 'vue-recaptcha-v3'
import { encryptMetadata, deriveKeyFromUser } from '@/utils/crypto'

export default {
  name: "RegisterPage",
  setup() {
    const { executeRecaptcha, recaptchaLoaded } = useReCaptcha()
    return { executeRecaptcha, recaptchaLoaded }
  },
  data() {
    return {
      username: '',
      email: '',
      firstName: '',
      lastName: '',
      userType: 'patient',  // Default to patient
      dateOfBirth: '',
      organisation: '',
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

        // Validation conditionnelle selon le type d'utilisateur
        if (this.userType === 'patient' && !this.dateOfBirth) {
          this.errorMessage = 'Date of birth is required'
          this.loading = false
          return
        }

        if (this.userType === 'doctor' && !this.organisation) {
          this.errorMessage = 'Organisation is required'
          this.loading = false
          return
        }

        // Wait for reCAPTCHA to be ready
        await this.recaptchaLoaded()
        
        // Get reCAPTCHA token
        const recaptchaToken = await this.executeRecaptcha('register')

        // Generate temporary simple password
        const tempPassword = this.generateTempPassword()
        
        // IMPORTANT: Generate encryption key BEFORE encrypting data
        // Uses username as base (will be replaced by keycloak_id after login)
        deriveKeyFromUser(this.username)
        
        // Encrypt sensitive data on client-side BEFORE sending
        // NOTE: username and email remain in plaintext (required for auth)
        // NOTE: Doctor names are NOT encrypted (public professional info)
        const encryptedDateOfBirth = this.userType === 'patient' ? encryptMetadata(this.dateOfBirth) : null
        const encryptedFirstName = this.userType === 'patient' ? encryptMetadata(this.firstName) : this.firstName
        const encryptedLastName = this.userType === 'patient' ? encryptMetadata(this.lastName) : this.lastName
        
        const payload = {
          username: this.username,  // Plaintext
          email: this.email,        // Plaintext
          password: tempPassword,
          user_type: this.userType,
          recaptcha_token: recaptchaToken,
          // Plaintext versions for Keycloak UI
          plaintext_first_name: this.firstName,
          plaintext_last_name: this.lastName,
          // For patients: encrypted, for doctors: plaintext
          first_name: encryptedFirstName,
          last_name: encryptedLastName
        }

        // Ajouter les champs conditionnels
        if (this.userType === 'patient') {
          payload.date_of_birth = encryptedDateOfBirth  // Encrypted for DB
        } else if (this.userType === 'doctor') {
          payload.organisation = this.organisation  // Plaintext for display
        }

        const response = await api.post('/auth/register/', payload)

        if (response.data) {
          // Success message adapted to user type
          const userTypeLabel = this.userType === 'patient' ? 'Patient' : 'Doctor'
          alert(`✅ ${userTypeLabel} account created successfully!\n\n🔐 Next steps:\n1. Enter your username: ${this.username}\n2. Setup your Passkey (fingerprint, Face ID, or security key)\n3. Future logins: Just use your Passkey!\n\n🔒 Passwordless = Maximum Security`)
          
          // Store for reference
          sessionStorage.setItem('new_user', this.username)
          
          // Generate state for CSRF security
          const state = this.generateRandomString(32)
          sessionStorage.setItem('oauth_state', state)
          
          const keycloakAuthUrl = `https://localhost/auth/realms/medical-realm/protocol/openid-connect/auth`
          const params = new URLSearchParams({
            client_id: 'medical-app',
            redirect_uri: 'https://localhost/callback',
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
      // Generate simple 6-character alphanumeric code
      const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // Without ambiguous characters
      let code = ''
      for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length))
      }
      // Return password with code + suffix to meet policy requirements
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
        <label class="block text-white text-sm font-bold mb-2">I am a *</label>
        <select v-model="userType" required class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="patient">Patient</option>
          <option value="doctor">Doctor</option>
        </select>
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

      <div v-if="userType === 'patient'">
        <label class="block text-white text-sm font-bold mb-2">Date of Birth *</label>
        <input type="date" v-model="dateOfBirth" :required="userType === 'patient'" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div v-if="userType === 'doctor'">
        <label class="block text-white text-sm font-bold mb-2">Organisation *</label>
        <input type="text" v-model="organisation" :required="userType === 'doctor'" placeholder="Hospital name" class="w-full px-3 py-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      <div class="bg-blue-50 border border-blue-200 p-3 rounded text-center">
        <p class="text-sm text-gray-700">
          🔒 Protected by Google reCAPTCHA
        </p>
      </div>

      <button type="submit" :disabled="loading" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-lg transition duration-200 disabled:bg-gray-500">
        <span v-if="loading">Creating account...</span>
        <span v-else>Register</span>
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

/* Style pour le select en mode sombre */
select {
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 1.5em 1.5em;
  appearance: none;
  padding-right: 2.5rem;
}

select option {
  background-color: #374151;
  color: white;
}
</style>
