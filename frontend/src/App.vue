<script setup>
import { RouterLink, RouterView } from 'vue-router';
import { ref, onMounted, computed } from 'vue';
import api from './services/api';

const isAuthenticated = ref(false);
const userType = ref(null);
const unreadNotificationCount = ref(0);

// Check authentication status
const checkAuth = () => {
  const token = localStorage.getItem('accessToken');
  isAuthenticated.value = !!token;
  if (token) {
    loadProfile();
    loadNotificationCount();
  }
};

// Load user profile
const loadProfile = async () => {
  try {
    const response = await api.getProfile();
    userType.value = response.data.user_type;
  } catch (error) {
    console.error('Error loading profile:', error);
  }
};

// Load notification count
const loadNotificationCount = async () => {
  try {
    const response = await api.getUnreadNotificationCount();
    unreadNotificationCount.value = response.data.unread_count;
  } catch (error) {
    console.error('Error loading notification count:', error);
  }
};

// Logout function
const logout = async () => {
  try {
    await api.logout();
  } catch (error) {
    // Even if API call fails, clear local data
  } finally {
    localStorage.removeItem('accessToken');
    isAuthenticated.value = false;
    userType.value = null;
    unreadNotificationCount.value = 0;
    window.location.href = '/login';
  }
};

onMounted(() => {
  checkAuth();
  // Refresh notification count every 30 seconds
  setInterval(() => {
    if (isAuthenticated.value) {
      loadNotificationCount();
    }
  }, 30000);
});

// Listen for auth changes
window.addEventListener('storage', (e) => {
  if (e.key === 'accessToken') {
    checkAuth();
  }
});
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans text-gray-900 bg-gray-50">
    
    <header class="bg-blue-800 text-white shadow-md">
      <nav class="container mx-auto px-6 py-4 flex justify-between items-center">
        <div class="text-xl font-bold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          SecureMed
        </div>
        <div class="flex items-center space-x-6 text-sm font-medium">
          <RouterLink to="/" class="hover:text-blue-200 transition">Home</RouterLink>
          
          <!-- Authenticated Navigation -->
          <template v-if="isAuthenticated">
            <RouterLink to="/records" class="hover:text-blue-200 transition">Medical Records</RouterLink>
            <RouterLink to="/doctors" class="hover:text-blue-200 transition">Doctors</RouterLink>
            
            <!-- Patient-specific links -->
            <template v-if="userType === 'patient'">
              <RouterLink to="/pending-requests" class="hover:text-blue-200 transition">Requests</RouterLink>
            </template>
            
            <!-- Notifications with badge -->
            <RouterLink to="/notifications" class="relative hover:text-blue-200 transition flex items-center">
              <svg class="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
              </svg>
              Notifications
              <span v-if="unreadNotificationCount > 0" 
                    class="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                {{ unreadNotificationCount > 9 ? '9+' : unreadNotificationCount }}
              </span>
            </RouterLink>
            
            <RouterLink to="/profile" class="hover:text-blue-200 transition">Profile</RouterLink>
            <RouterLink to="/audit-logs" class="hover:text-blue-200 transition">Audit</RouterLink>
            <button @click="logout" class="hover:text-blue-200 transition">Logout</button>
          </template>
          
          <!-- Non-authenticated Navigation -->
          <template v-else>
            <RouterLink to="/login" class="hover:text-blue-200 transition">Login</RouterLink>
            <RouterLink to="/register" class="hover:text-blue-200 transition">Register</RouterLink>
            <RouterLink to="/about" class="hover:text-blue-200 transition">About</RouterLink>
          </template>
        </div>
      </nav>
    </header>

    <main class="flex-grow container mx-auto px-4 py-8">
      <RouterView />
    </main>
    
    <footer class="bg-white border-t border-gray-200 text-gray-500 text-center py-6 text-sm mt-auto">
      &copy; 2026 Secure Medical Project. End-to-End Encrypted System.
    </footer>
  </div>
</template>