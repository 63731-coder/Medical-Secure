<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { clearEncryptionKey, decryptMetadata } from '../utils/crypto';
import api from '../services/api';

const router = useRouter();
const user = ref(null);
const profile = ref(null);
const userType = ref(null);
const loading = ref(true);

// Computed properties for decrypted data
const decryptedFirstName = computed(() => {
    // For patients, use encrypted_data from response
    if (userType.value === 'patient' && user.value?.encrypted_data?.encrypted_first_name) {
        try {
            return decryptMetadata(user.value.encrypted_data.encrypted_first_name) || 'N/A';
        } catch (e) {
            console.error('Failed to decrypt first name:', e);
            return 'N/A';
        }
    }
    // For doctors, use plaintext
    return user.value?.first_name || 'N/A';
});

const decryptedLastName = computed(() => {
    // For patients, use encrypted_data from response
    if (userType.value === 'patient' && user.value?.encrypted_data?.encrypted_last_name) {
        try {
            return decryptMetadata(user.value.encrypted_data.encrypted_last_name) || 'N/A';
        } catch (e) {
            console.error('Failed to decrypt last name:', e);
            return 'N/A';
        }
    }
    // For doctors, use plaintext
    return user.value?.last_name || 'N/A';
});

const decryptedDateOfBirth = computed(() => {
    if (userType.value !== 'patient') return null;
    
    // Try encrypted data first
    if (user.value?.encrypted_data?.encrypted_date_of_birth) {
        try {
            return decryptMetadata(user.value.encrypted_data.encrypted_date_of_birth);
        } catch (e) {
            console.error('Failed to decrypt date of birth:', e);
        }
    }
    
    return profile.value?.date_of_birth || null;
});

const decryptedOrganisation = computed(() => {
    if (userType.value !== 'doctor' || !profile.value) return null;
    if (!profile.value.encrypted_organisation) return profile.value.organisation;
    try {
        return decryptMetadata(profile.value.encrypted_organisation) || profile.value.organisation || 'N/A';
    } catch (e) {
        console.error('Failed to decrypt organisation:', e);
        return profile.value.organisation || 'Encrypted';
    }
});

onMounted(async () => {
    try {
        const response = await api.getProfile();
        user.value = response.data;
        profile.value = response.data.profile;
        userType.value = response.data.user_type;
        loading.value = false;
    } catch (error) {
        console.error('Failed to load profile:', error);
        loading.value = false;
    }
});

function logout() {
    clearEncryptionKey();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.clear();
    router.push('/login');
}
</script>

<template>
    <div class="max-w-4xl mx-auto py-8">
        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading profile...</p>
        </div>
        
        <div v-else-if="user" class="bg-white shadow-lg rounded-xl p-6 border border-gray-100">
            <div class="flex items-start justify-between mb-6">
                <div class="flex items-center space-x-6">
                    <div
                        class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold">
                        {{ user.first_name ? user.first_name.charAt(0).toUpperCase() : 'U' }}
                    </div>
                    <div>
                        <h2 class="text-2xl font-extrabold text-gray-900">
                            {{ user.first_name }} {{ user.last_name }}
                        </h2>
                        <p class="text-sm text-gray-500 mt-1">@{{ user.username }}</p>
                        <p class="text-xs text-gray-400 mt-1 capitalize">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {{ userType }}
                            </span>
                        </p>
                    </div>
                </div>
                <button @click="logout"
                    class="bg-red-50 hover:bg-red-100 text-red-700 border border-red-100 font-medium px-4 py-2 rounded-lg transition">
                    Log out
                </button>
            </div>

            <!-- Profile Information -->
            <div class="border-t pt-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">First Name</label>
                        <p class="text-gray-900 font-medium mt-1">{{ decryptedFirstName }}</p>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Last Name</label>
                        <p class="text-gray-900 font-medium mt-1">{{ decryptedLastName }}</p>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Username</label>
                        <p class="text-gray-900 font-medium mt-1">@{{ user.username }}</p>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Email</label>
                        <p class="text-gray-900 font-medium mt-1">{{ user.email || 'N/A' }}</p>
                    </div>
                    
                    <div v-if="userType === 'patient' && profile" class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Date of Birth</label>
                        <p class="text-gray-900 font-medium mt-1">
                            {{ decryptedDateOfBirth ? new Date(decryptedDateOfBirth).toLocaleDateString() : 'N/A' }}
                        </p>
                    </div>
                    
                    <div v-if="userType === 'doctor' && profile" class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Organisation</label>
                        <p class="text-gray-900 font-medium mt-1">{{ decryptedOrganisation }}</p>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <label class="text-xs font-medium text-gray-500 uppercase tracking-wider">Account Type</label>
                        <p class="text-gray-900 font-medium mt-1 capitalize">{{ userType }}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div v-else class="bg-white shadow-lg rounded-xl p-6 border border-gray-100 text-center">
            <p class="text-gray-500">Failed to load profile</p>
        </div>
    </div>
</template>
