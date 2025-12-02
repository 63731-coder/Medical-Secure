<script setup>
import { ref } from 'vue';
import { RouterLink } from 'vue-router';

// Simulated user state
const userName = ref("Doctor"); 
</script>

<template>
  <div>
    <div class="flex flex-col md:flex-row justify-between items-center mb-10">
      <div>
        <h1 class="text-3xl font-extrabold text-gray-900">
          Welcome back, <span class="text-blue-600">{{ userName }}</span>
        </h1>
        <p class="mt-2 text-sm text-gray-600">
          Secure Medical Portal Dashboard
        </p>
      </div>
      
      <div class="mt-4 md:mt-0 flex items-center bg-green-100 text-green-800 px-4 py-2 rounded-full shadow-sm">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span class="font-medium text-sm">Secure Session Active</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      
      <div class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition border border-gray-100">
        <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Medical Records</h3>
        <p class="text-gray-500 text-sm mb-6">Access and decrypt patient history securely.</p>
        <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition">
          View Records
        </button>
      </div>

      <div class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition border border-gray-100">
        <div class="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Upload Files</h3>
        <p class="text-gray-500 text-sm mb-6">Encrypt and upload new documents to the server.</p>
        <button class="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition">
          Upload New File
        </button>
      </div>

      <div class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition border border-gray-100">
        <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Security</h3>
        <p class="text-gray-500 text-sm mb-6">Manage keys and review access logs.</p>
        <button class="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2 px-4 rounded-lg transition">
          Settings
        </button>
      </div>

    </div>
  </div>
</template> 