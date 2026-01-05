<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';
import StatusAlert from '../components/StatusAlert.vue';
import { useNotifications } from '../composables/useNotifications';
import { getCurrentKey } from '../utils/crypto';

const { success: notifySuccess, error: notifyError } = useNotifications();
const requests = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');

onMounted(async () => {
    await fetchRequests();
});

const fetchRequests = async () => {
    try {
        loading.value = true;
        
        // Get profile to confirm user is a patient
        const profileRes = await api.getProfile();
        if (profileRes.data.user_type !== 'patient') {
            error.value = "This page is for patients only.";
            loading.value = false;
            return;
        }
        
        // Get all requests for this patient
        const requestsRes = await api.getRequests();
        requests.value = requestsRes.data.filter(r => r.status === 'pending');
        
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch requests:", e);
        error.value = "Failed to load requests.";
        loading.value = false;
    }
};

const approveRequest = async (request) => {
    try {
        // First approve the request
        await api.approveRequest(request.id);
        
        // Then automatically share the encryption key with the doctor
        try {
            const myEncryptionKey = getCurrentKey();
            const doctorPublicKey = request.doctor.public_key;
            
            if (doctorPublicKey && myEncryptionKey) {
                const encryptedKey = await encryptWithPublicKey(myEncryptionKey, doctorPublicKey);
                
                await api.post('/share-key/', {
                    doctor_id: request.doctor.id,
                    encrypted_key: encryptedKey
                });
                
                console.log('Encryption key shared successfully with doctor');
            }
        } catch (keyError) {
            console.warn('Failed to share encryption key:', keyError);
            // Don't fail the whole approval if key sharing fails
        }
        
        const message = `Dr. ${request.doctor.user.last_name} has been added to your doctors list.`;
        success.value = message;
        notifySuccess(message);
        error.value = '';
        await fetchRequests();
    } catch (e) {
        console.error("Failed to approve request:", e);
        const errorMsg = e.response?.data?.error || "Failed to approve request.";
        error.value = errorMsg;
        notifyError(errorMsg);
    }
};

const rejectRequest = async (request) => {
    try {
        await api.rejectRequest(request.id);
        success.value = `Request from Dr. ${request.doctor.user.last_name} has been rejected.`;
        error.value = '';
        await fetchRequests();
    } catch (e) {
        console.error("Failed to reject request:", e);
        error.value = e.response?.data?.error || "Failed to reject request.";
    }
};
</script>

<template>
    <div class="max-w-4xl mx-auto py-8">
        <StatusAlert v-if="error" type="error" :message="error" @close="error = ''" />
        <StatusAlert v-if="success" type="success" :message="success" @close="success = ''" />

        <div class="mb-6">
            <h1 class="text-2xl font-extrabold text-gray-900">Doctor Access Requests</h1>
            <p class="text-sm text-gray-500">Review and approve doctors who want to access your medical records.</p>
        </div>

        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading requests...</p>
        </div>

        <div v-else-if="requests.length === 0" class="text-center py-12 bg-white rounded-lg shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-600 font-medium">No pending requests</p>
            <p class="text-gray-400 text-sm mt-1">You don't have any doctor access requests at the moment</p>
        </div>

        <div v-else class="space-y-4">
            <div v-for="request in requests" :key="request.id" 
                :class="[
                    'rounded-lg shadow-md border p-6',
                    request.action_type === 'remove' ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'
                ]">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <h3 class="font-bold text-lg text-gray-900">
                                Dr. {{ request.doctor.user.first_name }} {{ request.doctor.user.last_name }}
                            </h3>
                            <span v-if="request.action_type === 'remove'" 
                                class="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                                REMOVAL REQUEST
                            </span>
                        </div>
                        <p class="text-sm text-gray-600">{{ request.doctor.organisation }}</p>
                        <p class="text-xs text-gray-500 mt-2">
                            Request sent {{ new Date(request.created_at).toLocaleDateString() }}
                        </p>
                    </div>
                    <span class="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-1 rounded">
                        Pending
                    </span>
                </div>

                <div :class="[
                    'border rounded-lg p-4 mb-4',
                    request.action_type === 'remove' ? 'bg-red-100 border-red-300' : 'bg-blue-50 border-blue-200'
                ]">
                    <p :class="[
                        'text-sm',
                        request.action_type === 'remove' ? 'text-red-900' : 'text-blue-900'
                    ]">
                        <strong>Dr. {{ request.doctor.user.last_name }}</strong> 
                        <span v-if="request.action_type === 'add'">
                            is requesting access to your medical records.
                            If you approve, they will be able to view and upload medical files to your account.
                        </span>
                        <span v-else>
                            is requesting to be removed from your doctors list.
                            If you approve, they will no longer have access to your medical records.
                        </span>
                    </p>
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
