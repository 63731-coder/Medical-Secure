<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import NotificationCenter from './components/NotificationCenter.vue';
import ToastNotifications from './components/ToastNotifications.vue';

const router = useRouter();
const isLoggedIn = ref(false);

const checkAuth = () => {
  isLoggedIn.value = !!localStorage.getItem('accessToken');
};

const handleLogout = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('username');
  isLoggedIn.value = false;
  router.push('/login');
};

onMounted(() => {
  checkAuth();
  // Listen for login/logout events
  window.addEventListener('storage', checkAuth);
  
  // Update auth state when navigating
  router.afterEach(() => {
    checkAuth();
  });
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
          <RouterLink to="/" class="hover:text-blue-200 transition">SecureMed</RouterLink>
        </div>
        <div class="flex items-center gap-6">
          <div v-if="!isLoggedIn" class="space-x-6 text-sm font-medium">
            <RouterLink to="/" class="hover:text-blue-200 transition">Home</RouterLink>
            <RouterLink to="/login" class="hover:text-blue-200 transition">Login</RouterLink>
            <RouterLink to="/about" class="hover:text-blue-200 transition">About</RouterLink>
          </div>
          <div v-else class="flex items-center gap-4">
            <RouterLink to="/" class="text-sm font-medium hover:text-blue-200 transition">Home</RouterLink>
            <RouterLink to="/profile" class="text-sm font-medium hover:text-blue-200 transition">Profile</RouterLink>
            <NotificationCenter />
            <button @click="handleLogout" 
              class="text-sm font-medium hover:text-blue-200 transition flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </div>
        </div>
      </nav>
    </header>

    <main class="flex-grow container mx-auto px-4 py-8">
      <RouterView />
    </main>
    
    <!-- Toast Notifications -->
    <ToastNotifications />
    
    <footer class="bg-white border-t border-gray-200 text-gray-500 text-center py-6 text-sm mt-auto">
      &copy; 2026 Secure Medical Project. End-to-End Encrypted System.
    </footer>
  </div>
</template>