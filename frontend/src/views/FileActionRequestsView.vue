<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';
import StatusAlert from '../components/StatusAlert.vue';
import { useNotifications } from '../composables/useNotifications';
import { decryptMetadata } from '../utils/crypto';

const { success: notifySuccess, error: notifyError, warning: notifyWarning } = useNotifications();
const fileActionRequests = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');

onMounted(async () => {
    await fetchFileActionRequests();
});

const fetchFileActionRequests = async () => {
    try {
        loading.value = true;
        
        // Get profile to confirm user is a patient
        const profileRes = await api.getProfile();
        if (profileRes.data.user_type !== 'patient') {
            error.value = "This page is for patients only.";
            loading.value = false;
            return;
        }
        
        // Get all file action requests for this patient
        const requestsRes = await api.getFileActionRequests();
        fileActionRequests.value = requestsRes.data.filter(r => r.status === 'pending');
        
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch file action requests:", e);
        error.value = "Failed to load file action requests.";
        loading.value = false;
    }
};

const approveRequest = async (request) => {
    try {
        await api.approveFileAction(request.id);
        const message = `${getActionText(request.action_type)} request from Dr. ${getDoctorName(request.doctor)} has been approved.`;
        success.value = message;
        notifySuccess(message);
        error.value = '';
        await fetchFileActionRequests();
    } catch (e) {
        console.error("Failed to approve request:", e);
        const errorMsg = e.response?.data?.error || "Failed to approve request.";
        error.value = errorMsg;
        notifyError(errorMsg);
    }
};

const rejectRequest = async (request) => {
    try {
        await api.rejectFileAction(request.id);
        success.value = `${getActionText(request.action_type)} request from Dr. ${getDoctorName(request.doctor)} has been rejected.`;
        error.value = '';
        await fetchFileActionRequests();
    } catch (e) {
        console.error("Failed to reject request:", e);
        error.value = e.response?.data?.error || "Failed to reject request.";
    }
};

const getActionText = (actionType) => {
    const texts = {
        'upload': 'Upload',
        'edit': 'Edit',
        'delete': 'Delete'
    };
    return texts[actionType] || actionType;
};

const getActionColor = (actionType) => {
    const colors = {
        'upload': 'green',
        'edit': 'blue',
        'delete': 'red'
    };
    return colors[actionType] || 'gray';
};

// Check if a string looks like encrypted data (Base64 CryptoJS format)
const isEncryptedString = (str) => {
    if (!str) return false;
    return str.startsWith('U2FsdGVkX1');
};

// Get doctor name - doctors' names should NOT be encrypted (public professional info)
const getDoctorName = (doctor) => {
    if (!doctor) return '@unknown';
    
    let firstName = doctor.user.first_name || '';
    let lastName = doctor.user.last_name || '';
    
    // Check if names are encrypted (legacy issue) - use username instead
    if (isEncryptedString(firstName) || isEncryptedString(lastName)) {
        return doctor.user.username;
    }
    
    if (firstName || lastName) {
        return `${firstName} ${lastName}`.trim();
    }
    return doctor.user.username;
};

// Get doctor organisation (already in plaintext from backend)
const getDoctorOrganisation = (doctor) => {
    if (!doctor) return '';
    // Use organisation field (backend sends plaintext)
    return doctor.organisation || 'Medical Professional';
};

const getActionIcon = (actionType) => {
    return {
        'upload': 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
        'edit': 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
        'delete': 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'
    }[actionType] || 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
};

// Decrypt request fields
const getDecryptedFileName = (request) => {
    if (!request.file_name) return 'Untitled';
    try {
        return decryptMetadata(request.file_name) || 'Untitled';
    } catch (e) {
        console.error('Failed to decrypt file name:', e);
        return 'Encrypted';
    }
};

const getDecryptedFileDescription = (request) => {
    if (!request.file_description) return '';
    try {
        return decryptMetadata(request.file_description) || '';
    } catch (e) {
        console.error('Failed to decrypt file description:', e);
        return '';
    }
};

const getDecryptedTargetName = (request) => {
    if (!request.target_file_info?.name) return 'Unknown';
    try {
        return decryptMetadata(request.target_file_info.name) || 'Unknown';
    } catch (e) {
        console.error('Failed to decrypt target file name:', e);
        return 'Encrypted';
    }
};

const getDecryptedTargetDescription = (request) => {
    if (!request.target_file_info?.description) return '';
    try {
        return decryptMetadata(request.target_file_info.description) || '';
    } catch (e) {
        console.error('Failed to decrypt target file description:', e);
        return '';
    }
};

const getDecryptedActionType = (request) => {
    // action_type is NOT encrypted on backend - it's stored as plain 'upload', 'edit', 'delete'
    // This is not sensitive data, just an action type
    if (!request.action_type) {
        console.log('[FileActionRequest] No action_type field');
        return 'upload'; // Default to upload if missing
    }
    // Return directly without decryption
    return request.action_type;
};

</script>

<template>
    <div class="max-w-4xl mx-auto py-8">
        <StatusAlert v-if="error" type="error" :message="error" @close="error = ''" />
        <StatusAlert v-if="success" type="success" :message="success" @close="success = ''" />

        <div class="mb-6">
            <h1 class="text-2xl font-extrabold text-gray-900">File Action Requests</h1>
            <p class="text-sm text-gray-500">Review and approve file operations requested by your doctors.</p>
        </div>

        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading requests...</p>
        </div>

        <div v-else-if="fileActionRequests.length === 0" class="text-center py-12 bg-white rounded-lg shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-600 font-medium">No pending file action requests</p>
            <p class="text-gray-400 text-sm mt-1">You don't have any pending file operations at the moment</p>
        </div>

        <div v-else class="space-y-4">
            <div v-for="request in fileActionRequests" :key="request.id" 
                class="bg-white rounded-lg shadow-md border border-gray-200 p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-start gap-4 flex-1">
                        <!-- Action Icon -->
                        <div :class="`w-12 h-12 rounded-full flex items-center justify-center bg-${getActionColor(getDecryptedActionType(request))}-100`">
                            <svg xmlns="http://www.w3.org/2000/svg" 
                                :class="`h-6 w-6 text-${getActionColor(getDecryptedActionType(request))}-600`"
                                fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                    :d="getActionIcon(getDecryptedActionType(request))" />
                            </svg>
                        </div>
                        
                        <div class="flex-1">
                            <h3 class="font-bold text-lg text-gray-900">
                                {{ getActionText(getDecryptedActionType(request)) }} File
                            </h3>
                            <p class="text-sm text-gray-600">
                                Requested by <strong>Dr. {{ getDoctorName(request.doctor) }}</strong>
                            </p>
                            <p class="text-sm text-gray-600">{{ getDoctorOrganisation(request.doctor) }}</p>
                            <p class="text-xs text-gray-500 mt-2">
                                Request sent {{ new Date(request.created_at).toLocaleDateString() }}
                            </p>
                        </div>
                    </div>
                    <span :class="`bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-1 rounded`">
                        Pending
                    </span>
                </div>

                <!-- File Details -->
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                    <div v-if="getDecryptedActionType(request) === 'upload'" class="space-y-2">
                        <div class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-24">File Name:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedFileName(request) }}</span>
                        </div>
                        <div v-if="getDecryptedFileDescription(request)" class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-24">Description:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedFileDescription(request) }}</span>
                        </div>
                    </div>
                    
                    <div v-else-if="getDecryptedActionType(request) === 'edit'" class="space-y-2">
                        <div class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-32">Current File:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedTargetName(request) }}</span>
                        </div>
                        <div class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-32">New Name:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedFileName(request) }}</span>
                        </div>
                        <div v-if="getDecryptedFileDescription(request)" class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-32">New Description:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedFileDescription(request) }}</span>
                        </div>
                    </div>
                    
                    <div v-else-if="getDecryptedActionType(request) === 'delete'" class="space-y-2">
                        <div class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-24">File Name:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedTargetName(request) }}</span>
                        </div>
                        <div v-if="getDecryptedTargetDescription(request)" class="flex items-start">
                            <span class="text-sm font-medium text-gray-700 w-24">Description:</span>
                            <span class="text-sm text-gray-900">{{ getDecryptedTargetDescription(request) }}</span>
                        </div>
                        <div class="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                            <p class="text-xs text-red-800">
                                ⚠️ Warning: This file will be permanently deleted if you approve this request.
                            </p>
                        </div>
                    </div>
                </div>

                <div class="flex gap-3">
                    <button @click="approveRequest(request)"
                        class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition">
                        Approve
                    </button>
                    <button @click="rejectRequest(request)"
                        class="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition">
                        Reject
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
