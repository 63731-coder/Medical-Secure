<script setup>
/**
 * HomeView - Main dashboard after authentication
 * Shows different navigation options based on user type (patient/doctor)
 */
import { ref, onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();

// User state
const isAuthenticated = ref(false);
const userName = ref(null); 
const userType = ref(null);
const pendingRequestsCount = ref(0);
const pendingFileActionsCount = ref(0);

onMounted(async () => {
  // Check if user is authenticated
  const token = localStorage.getItem('access_token');
  if (!token) {
    isAuthenticated.value = false;
    router.push('/login');
    return;
  }
  
  try {
    const profileRes = await api.getProfile();
    isAuthenticated.value = true;
    userType.value = profileRes.data.user_type;
    
    // Use first name if available, otherwise username (but not keycloak ID)
    if (profileRes.data.first_name && profileRes.data.first_name !== 'N/A') {
      userName.value = profileRes.data.first_name;
    } else if (profileRes.data.username && !profileRes.data.username.includes('-')) {
      userName.value = profileRes.data.username;
    } else {
      userName.value = 'User'; // Fallback
    }
    
    // If patient, check for pending requests
    if (userType.value === 'patient') {
      const requestsRes = await api.getRequests();
      pendingRequestsCount.value = requestsRes.data.filter(r => r.status === 'pending').length;
      
      // Check for pending file action requests
      const fileActionsRes = await api.getFileActionRequests();
      pendingFileActionsCount.value = fileActionsRes.data.filter(r => r.status === 'pending').length;
    }
  } catch (e) {
    console.error('Failed to load profile:', e);
    isAuthenticated.value = false;
    router.push('/login');
  }
});
</script>

<template>
  <div v-if="isAuthenticated">
    <div class="flex flex-col md:flex-row justify-between items-center mb-10">
      <div>
        <h1 class="text-3xl font-extrabold text-gray-900">
          Welcome
        </h1>
        <p class="mt-2 text-sm text-gray-600">
          Secure Medical Portal Dashboard
        </p>
      </div>
      
      <div class="mt-4 md:mt-0 flex items-center bg-green-100 text-green-800 px-4 py-2 rounded-full shadow-sm border border-green-200">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span class="font-medium text-sm">End-to-End Encryption Active</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      
      <div v-if="userType === 'patient'" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition duration-300 border border-gray-100 flex flex-col">
        <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Medical Records</h3>
        <p class="text-gray-500 text-sm mb-6 flex-grow">
          Access your history, prescriptions, and lab results. Data is decrypted locally in your browser.
        </p>
        <RouterLink to="/records" class="w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
          View Records
        </RouterLink>
      </div>

      <div v-if="userType === 'patient'" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition duration-300 border border-gray-100 flex flex-col">
        <div class="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Upload Files</h3>
        <p class="text-gray-500 text-sm mb-6 flex-grow">
          Securely upload new analyses or reports. Files are encrypted before leaving your device.
        </p>
        <RouterLink to="/upload" class="w-full text-center bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
          Upload New File
        </RouterLink>
      </div>

      <div v-if="userType === 'patient'" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition duration-300 border border-gray-100 flex flex-col relative">
        <div v-if="pendingRequestsCount > 0" class="absolute top-4 right-4 bg-red-500 text-white text-xs font-bold rounded-full h-6 w-6 flex items-center justify-center">
          {{ pendingRequestsCount }}
        </div>
        <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">My Doctors</h3>
        <p class="text-gray-500 text-sm mb-6 flex-grow">
          Manage access rights and view the list of doctors authorized to see your data.
        </p>
        <div class="space-y-2">
          <RouterLink to="/doctors" class="w-full block text-center bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
            Manage Doctors
          </RouterLink>
          <RouterLink v-if="pendingRequestsCount > 0" to="/doctor-requests" class="w-full block text-center bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
            Review Requests ({{ pendingRequestsCount }})
          </RouterLink>
        </div>
      </div>

      <div v-if="userType === 'doctor'" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition duration-300 border border-gray-100 flex flex-col">
        <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">My Patients</h3>
        <p class="text-gray-500 text-sm mb-6 flex-grow">
          Manage your patients and send access requests to view their medical records.
        </p>
        <RouterLink to="/my-patients" class="w-full text-center bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
          Manage Patients
        </RouterLink>
      </div>

      <div v-if="userType === 'patient' && pendingFileActionsCount > 0" class="bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition duration-300 border border-yellow-200 flex flex-col relative">
        <div class="absolute top-4 right-4 bg-orange-500 text-white text-xs font-bold rounded-full h-6 w-6 flex items-center justify-center">
          {{ pendingFileActionsCount }}
        </div>
        <div class="w-12 h-12 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">File Actions</h3>
        <p class="text-gray-500 text-sm mb-6 flex-grow">
          Your doctors have requested file operations that require your approval.
        </p>
        <RouterLink to="/file-action-requests" class="w-full text-center bg-orange-500 hover:bg-orange-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
          Review File Actions ({{ pendingFileActionsCount }})
        </RouterLink>
      </div>

    </div>
  </div>
</template>