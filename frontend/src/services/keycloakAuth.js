// Keycloak OAuth2 / OIDC Authentication Service
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

class KeycloakAuth {
  constructor() {
    this.config = null
    this.accessToken = localStorage.getItem('access_token')
    this.refreshToken = localStorage.getItem('refresh_token')
  }

  /**
   * Get Keycloak configuration from backend
   */
  async getConfig() {
    if (!this.config) {
      const response = await axios.get(`${API_URL}/auth/config/`)
      this.config = response.data
    }
    return this.config
  }

  /**
   * Initiate OAuth2 login flow
   * Redirects user to Keycloak login page
   */
  async login() {
    const config = await this.getConfig()
    
    // Generate state for CSRF protection
    const state = this.generateRandomString(32)
    sessionStorage.setItem('oauth_state', state)
    
    const params = new URLSearchParams({
      client_id: config.client_id,
      redirect_uri: config.redirect_uri,
      response_type: 'code',
      scope: 'openid profile email',
      state: state,
    })
    
    window.location.href = `${config.auth_url}?${params.toString()}`
  }

  /**
   * Handle OAuth2 callback
   * Exchange authorization code for tokens
   */
  async handleCallback(code, state) {
    // Verify state to prevent CSRF
    const savedState = sessionStorage.getItem('oauth_state')
    if (state !== savedState) {
      throw new Error('Invalid state parameter')
    }
    sessionStorage.removeItem('oauth_state')
    
    const config = await this.getConfig()
    
    const response = await axios.post(`${API_URL}/auth/callback/`, {
      code: code,
      redirect_uri: config.redirect_uri,
    })

    // Save tokens in memory and localStorage
    this.accessToken = response.data.access_token
    this.refreshToken = response.data.refresh_token
    
    localStorage.setItem('access_token', this.accessToken)
    localStorage.setItem('refresh_token', this.refreshToken)
    
    return response.data
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available')
    }
    
    try {
      const response = await axios.post(`${API_URL}/auth/refresh/`, {
        refresh_token: this.refreshToken,
      })
      
      this.accessToken = response.data.access_token
      this.refreshToken = response.data.refresh_token

      localStorage.setItem('access_token', this.accessToken)
      localStorage.setItem('refresh_token', this.refreshToken)
      
      return this.accessToken
    } catch (error) {
      console.warn('Refresh token failed, logging out...')
      await this.logout()
      throw error
    }
  }

  /**
   * Logout user and revoke tokens
   */
  async logout() {
    if (this.refreshToken) {
      try {
        await axios.post(`${API_URL}/auth/logout/`, {
          refresh_token: this.refreshToken
        }, {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    this.accessToken = null
    this.refreshToken = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.accessToken
  }

  /**
   * Get current access token
   */
  getAccessToken() {
    return this.accessToken
  }

  /**
   * Decode JWT to get user info (without verification)
   */
  getUserInfo() {
    if (!this.accessToken) return null
    
    try {
      const payload = this.accessToken.split('.')[1]
      const decoded = JSON.parse(atob(payload))
      return {
        username: decoded.preferred_username,
        email: decoded.email,
        firstName: decoded.given_name,
        lastName: decoded.family_name,
        roles: decoded.realm_access?.roles || [],
      }
    } catch (error) {
      console.error('Failed to decode JWT', error)
      return null
    }
  }

  /**
   * Generate random string for state parameter
   */
  generateRandomString(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }
}

// Export singleton instance
export default new KeycloakAuth()
