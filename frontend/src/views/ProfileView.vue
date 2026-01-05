<script setup>
import { ref, onMounted, computed } from 'vue';
import { decryptMetadata } from '../utils/crypto';
import api from '../services/api';

const user = ref(null);
const profile = ref(null);
const userType = ref(null);
const loading = ref(true);

// Computed properties for decrypted data
const decryptedFirstName = computed(() => {
    // Both patients and doctors: decrypt user.first_name (Django User model)
    if (user.value?.first_name) {
        try {
            return decryptMetadata(user.value.first_name) || 'N/A';
        } catch (e) {
            return 'N/A';
        }
    }
    return 'N/A';
});

const decryptedLastName = computed(() => {
    // Both patients and doctors: decrypt user.last_name (Django User model)
    if (user.value?.last_name) {
        try {
            return decryptMetadata(user.value.last_name) || 'N/A';
        } catch (e) {
            return 'N/A';
        }
    }
    return 'N/A';
});

const decryptedDateOfBirth = computed(() => {
    if (userType.value !== 'patient' || !profile.value?.date_of_birth) return null;
    
    try {
        return decryptMetadata(profile.value.date_of_birth);
    } catch (e) {
        return null;
    }
});

const decryptedOrganisation = computed(() => {
    if (userType.value !== 'doctor' || !profile.value) return null;
    if (!profile.value.organisation) return profile.value.organisation;
    try {
        return decryptMetadata(profile.value.organisation) || profile.value.organisation || 'N/A';
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
                        {{ decryptedFirstName ? decryptedFirstName.charAt(0).toUpperCase() : 'U' }}
                    </div>
                    <div>
                        <h2 class="text-2xl font-extrabold text-gray-900">
                            {{ decryptedFirstName }} {{ decryptedLastName }}
                        </h2>
                        <p class="text-sm text-gray-500 mt-1">@{{ user.username }}</p>
                        <p class="text-xs text-gray-400 mt-1 capitalize">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {{ userType }}
                            </span>
                        </p>
                    </div>
                </div>
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
