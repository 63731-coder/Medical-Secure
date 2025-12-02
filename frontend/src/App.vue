<script setup>
import { RouterLink, RouterView } from 'vue-router';
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
        <div class="space-x-6 text-sm font-medium">
          <RouterLink to="/" class="hover:text-blue-200 transition">Home</RouterLink>
          <RouterLink to="/login" class="hover:text-blue-200 transition">Login</RouterLink>
          <RouterLink to="/about" class="hover:text-blue-200 transition">About</RouterLink>
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