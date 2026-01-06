<script setup>
/**
 * DoctorDetailView - Detailed view of a specific doctor
 * Patients can revoke doctor access from this view
 */
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/services/api';
import ConfirmModal from '../components/ConfirmModal.vue';

const route = useRoute();
const router = useRouter();
const doctorId = route.params.id;

const doctor = ref(null);
const loading = ref(true);
const error = ref('');
const currentPatientId = ref(null);
const showConfirmModal = ref(false);
const isAppointed = ref(false);

onMounted(async () => {
    await fetchDoctor();
});

const fetchDoctor = async () => {
    try {
        // Get patient profile
        const profileRes = await api.get('/auth/me/');
        
        currentPatientId.value = profileRes.data.profile.id;
        
        // Check if doctor is appointed
        const appointedDoctorIds = profileRes.data.profile.appointed_doctors.map(d => d.id);
        isAppointed.value = appointedDoctorIds.includes(parseInt(doctorId));
        
        // Get doctor details
        const doctorRes = await api.get(`/doctors/${doctorId}/`);
        
        doctor.value = doctorRes.data;
        loading.value = false;
    } catch (e) {
        console.error("Failed to load doctor:", e);
        error.value = "Failed to load doctor details.";
        loading.value = false;
    }
};

const openRevokeConfirmation = () => {
    showConfirmModal.value = true;
};

const confirmRevoke = async () => {
    showConfirmModal.value = false;
    
    try {
        await api.delete(`/patients/${currentPatientId.value}/remove-doctor/${doctorId}/`);
        
        // Redirect back to doctors list
        router.push('/doctors');
    } catch (e) {
        console.error("Failed to revoke doctor:", e);
        error.value = 'Failed to revoke doctor access.';
    }
};

const cancelRevoke = () => {
    showConfirmModal.value = false;
};

const goBack = () => router.back();

// Check if a string looks like encrypted data (Base64 CryptoJS format)
const isEncryptedString = (str) => {
    if (!str) return false;
    return str.startsWith('U2FsdGVkX1');
};

// Get doctor name - doctors' names should NOT be encrypted (public professional info)
const getDoctorName = (doc) => {
    if (!doc) return { firstName: '', lastName: '' };
    
    let firstName = doc.user.first_name || '';
    let lastName = doc.user.last_name || '';
    
    // Check if names are encrypted (legacy issue) - use username instead
    if (isEncryptedString(firstName) || isEncryptedString(lastName)) {
        return { firstName: doc.user.username, lastName: '' };
    }
    
    if (firstName || lastName) {
        return { firstName, lastName };
    }
    return { firstName: doc.user.username, lastName: '' };
};

const getDoctorOrganisation = (doc) => {
    if (!doc) return '';
    return doc.organisation || 'Medical Professional';
};
</script>

<template>
    <div class="max-w-2xl mx-auto mt-10">
        <button @click="goBack"
            class="mb-4 text-gray-500 hover:text-gray-900 flex items-center text-sm font-medium transition">
            &larr; Back to List
        </button>

        <div v-if="loading" class="text-center p-10">Loading details...</div>
        <div v-else-if="error" class="text-center p-10 text-red-600">{{ error }}</div>

        <div v-else class="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
            <div class="h-32 bg-blue-600"></div>
            <div class="px-8 pb-8">
                <div class="-mt-12 mb-6">
                    <div class="w-24 h-24 rounded-full bg-white p-1 shadow-md inline-block">
                        <div
                            class="w-full h-full rounded-full bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center text-3xl text-white font-bold">
                            {{ getDoctorName(doctor).lastName.charAt(0) }}
                        </div>
                    </div>
                </div>

                <h1 class="text-3xl font-bold text-gray-900">Dr. {{ getDoctorName(doctor).firstName }} {{ getDoctorName(doctor).lastName }}</h1>
                <p class="text-blue-600 font-medium mb-4">{{ getDoctorOrganisation(doctor) }}</p>

                <div class="space-y-4 text-gray-600">
                    <div class="flex items-center">
                        <svg class="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4">
                            </path>
                        </svg>
                        {{ getDoctorOrganisation(doctor) }}
                    </div>
                    <div class="flex items-center">
                        <svg class="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z">
                            </path>
                        </svg>
                        {{ doctor.user.email }}
                    </div>
                </div>

                <div v-if="isAppointed" class="mt-8">
                    <button @click="openRevokeConfirmation"
                        class="w-full bg-red-50 text-red-600 hover:bg-red-100 py-3 rounded-lg font-medium transition">
                        Remove Access
                    </button>
                </div>
            </div>
        </div>

        <!-- Confirmation Modal -->
        <ConfirmModal
            :show="showConfirmModal"
            title="Revoke Doctor Access"
            :message="doctor ? `Are you sure you want to revoke access for Dr. ${getDoctorName(doctor).firstName} ${getDoctorName(doctor).lastName}? They will no longer be able to view your medical records.` : ''"
            confirmText="Revoke Access"
            cancelText="Cancel"
            :isDangerous="true"
            @confirm="confirmRevoke"
            @cancel="cancelRevoke"
        />
    </div>
</template>