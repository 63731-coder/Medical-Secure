<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '@/services/api';
import ConfirmModal from '../components/ConfirmModal.vue';

const doctors = ref([]);
const allDoctors = ref([]);
const appointedDoctorIds = ref([]);
const loading = ref(true);
const error = ref('');
const currentPatientId = ref(null);
const showConfirmModal = ref(false);
const doctorToRevoke = ref(null);
const decryptedDoctors = ref({}); // Store decrypted doctor names

onMounted(async () => {
    await fetchDoctors();
    await decryptDoctorsData();
});

const fetchDoctors = async () => {
    try {
        // Get patient profile to know appointed doctors
        const profileRes = await api.get('/auth/me/');
        
        if (profileRes.data.user_type !== 'patient') {
            error.value = "This page is for patients only.";
            loading.value = false;
            return;
        }
        
        currentPatientId.value = profileRes.data.profile.id;
        appointedDoctorIds.value = profileRes.data.profile.appointed_doctors.map(d => d.id);
        
        // Get all doctors
        const doctorsRes = await api.get('/doctors/');
        
        allDoctors.value = doctorsRes.data;
        
        // Show only appointed doctors
        doctors.value = doctorsRes.data.filter(d => appointedDoctorIds.value.includes(d.id));
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch doctors:", e);
        error.value = "Failed to load doctors.";
        loading.value = false;
    }
};

// Check if a string looks like encrypted data (Base64 CryptoJS format)
const isEncryptedString = (str) => {
    if (!str) return false;
    return str.startsWith('U2FsdGVkX1');
};

// Get doctor names - NOT encrypted (public professional info)
const decryptDoctorsData = async () => {
    for (const doctor of doctors.value) {
        let firstName = doctor.user.first_name || '';
        let lastName = doctor.user.last_name || '';
        
        // Check if names are encrypted (legacy data) - use username instead
        if (isEncryptedString(firstName) || isEncryptedString(lastName)) {
            firstName = doctor.user.username;
            lastName = '';
        }
        
        decryptedDoctors.value[doctor.id] = { firstName, lastName };
    }
};

const openRevokeConfirmation = (doctor) => {
    doctorToRevoke.value = doctor;
    showConfirmModal.value = true;
};

const confirmRevoke = async () => {
    showConfirmModal.value = false;
    
    if (!doctorToRevoke.value) return;
    
    try {
        await api.delete(`/patients/${currentPatientId.value}/remove-doctor/${doctorToRevoke.value.id}/`);
        
        // Refresh list
        await fetchDoctors();
        await decryptDoctorsData();
        error.value = ''; // Clear any previous errors
    } catch (e) {
        console.error("Failed to revoke doctor:", e);
        error.value = 'Failed to revoke doctor access.';
    }
    
    doctorToRevoke.value = null;
};

const cancelRevoke = () => {
    showConfirmModal.value = false;
    doctorToRevoke.value = null;
};

// Get decrypted doctor name
const getDoctorName = (doctor) => {
    if (!doctor) return { firstName: 'Unknown', lastName: '' };
    const data = decryptedDoctors.value[doctor.id];
    if (data && data.firstName) {
        return data;
    }
    return { firstName: doctor.user.username, lastName: '' };
};

// Get doctor organisation (already in plaintext from backend)
const getDoctorOrganisation = (doctor) => {
    // Use organisation field (backend sends plaintext)
    return doctor.organisation || 'Medical Professional';
};


</script>

<template>
    <div class="max-w-5xl mx-auto py-8">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-extrabold text-gray-900">My Appointed Doctors</h1>
                <p class="text-sm text-gray-500">Manage the doctors who can access your medical records.</p>
            </div>
            <RouterLink to="/search-doctors"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                + Search Doctors
            </RouterLink>
        </div>

        <div v-if="loading" class="text-center py-10 text-gray-500">Loading doctors...</div>
        <div v-else-if="error" class="text-center py-10 text-red-600">{{ error }}</div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="doctor in doctors" :key="doctor.id"
                class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div
                        class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center text-white text-lg font-semibold">
                        {{ getDoctorName(doctor).lastName.charAt(0) }}
                    </div>
                    <div>
                        <div class="font-semibold text-gray-900">Dr. {{ getDoctorName(doctor).firstName }} {{ getDoctorName(doctor).lastName }}</div>
                        <div class="text-sm text-gray-500">{{ getDoctorOrganisation(doctor) }}</div>
                    </div>
                </div>

                <div class="flex items-center gap-2">
                    <RouterLink :to="{ name: 'doctor-detail', params: { id: doctor.id } }"
                        class="text-sm bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-100 px-3 py-2 rounded-md">
                        View</RouterLink>
                    <button @click="openRevokeConfirmation(doctor)"
                        class="text-sm bg-red-50 hover:bg-red-100 text-red-700 border border-red-100 px-3 py-2 rounded-md">
                        Revoke
                    </button>
                </div>
            </div>
        </div>

        <div v-if="!loading && !error && !doctors.length" class="mt-6 text-center text-gray-500">
            No appointed doctors found.
        </div>

        <!-- Confirmation Modal -->
        <ConfirmModal
            :show="showConfirmModal"
            title="Revoke Doctor Access"
            :message="doctorToRevoke ? `Are you sure you want to revoke access for Dr. ${getDoctorName(doctorToRevoke).firstName} ${getDoctorName(doctorToRevoke).lastName}? They will no longer be able to view your medical records.` : ''"
            confirmText="Revoke Access"
            cancelText="Cancel"
            :isDangerous="true"
            @confirm="confirmRevoke"
            @cancel="cancelRevoke"
        />
    </div>
</template>
