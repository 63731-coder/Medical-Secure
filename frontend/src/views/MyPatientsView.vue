<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '../services/api';
import ConfirmModal from '../components/ConfirmModal.vue';
import StatusAlert from '../components/StatusAlert.vue';

const patients = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');
const showRemoveModal = ref(false);
const patientToRemove = ref(null);

onMounted(async () => {
    await fetchData();
});

const fetchData = async () => {
    try {
        loading.value = true;
        
        // Get doctor's patients
        const patientsRes = await api.getPatients();
        patients.value = patientsRes.data;
        
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch data:", e);
        error.value = "Failed to load data.";
        loading.value = false;
    }
};

const cancelRequest = async (requestId) => {
    try {
        await api.rejectRequest(requestId);
        success.value = "Request cancelled.";
        error.value = '';
        await fetchData();
    } catch (e) {
        console.error("Failed to cancel request:", e);
        error.value = "Failed to cancel request.";
    }
};

const openRemoveModal = (patient) => {
    patientToRemove.value = patient;
    showRemoveModal.value = true;
};

const confirmRemovePatient = async () => {
    showRemoveModal.value = false;
    const patient = patientToRemove.value;
    
    try {
        await api.createRequest({ 
            patient_id: patient.id,
            action_type: 'remove'
        });
        success.value = `Removal request sent to ${patient.user.first_name} ${patient.user.last_name}. Waiting for approval.`;
        error.value = '';
        await fetchData();
    } catch (e) {
        console.error("Failed to send removal request:", e);
        error.value = e.response?.data?.error || "Failed to send removal request.";
    } finally {
        patientToRemove.value = null;
    }
};

const cancelRemovePatient = () => {
    showRemoveModal.value = false;
    patientToRemove.value = null;
};
</script>

<template>
    <div class="max-w-6xl mx-auto py-8">
        <StatusAlert v-if="error" type="error" :message="error" @close="error = ''" />
        <StatusAlert v-if="success" type="success" :message="success" @close="success = ''" />

        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-extrabold text-gray-900">My Patients</h1>
                <p class="text-sm text-gray-500">Manage your patients and send access requests.</p>
            </div>
            <button @click="$router.push('/add-patient')"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                + Add Patient
            </button>
        </div>

        <!-- Current Patients List -->
        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading patients...</p>
        </div>

        <div v-else-if="patients.length === 0" class="text-center py-12 bg-white rounded-lg shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p class="text-gray-600 font-medium">No patients yet</p>
            <p class="text-gray-400 text-sm mt-1">Add patients to start managing their medical records</p>
        </div>

        <div v-else class="grid gap-4">
            <div v-for="patient in patients" :key="patient.id" 
                class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="font-bold text-lg text-gray-900">
                            {{ patient.user.first_name }} {{ patient.user.last_name }}
                        </h3>
                        <p class="text-sm text-gray-500">@{{ patient.user.username }}</p>
                        <p class="text-sm text-gray-500 mt-1">
                            Date of Birth: {{ new Date(patient.date_of_birth).toLocaleDateString() }}
                        </p>
                    </div>
                    <div class="flex gap-2">
                        <RouterLink :to="`/records?patient_id=${patient.id}`"
                            class="bg-blue-100 text-blue-700 hover:bg-blue-200 px-3 py-1.5 rounded text-sm font-medium transition flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            View Records
                        </RouterLink>
                        <button @click="openRemoveModal(patient)"
                            class="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1.5 rounded text-sm font-medium transition flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Remove Patient Modal -->
        <ConfirmModal
            :show="showRemoveModal"
            :title="'Remove Patient'"
            :message="patientToRemove ? `Request to remove ${patientToRemove.user.first_name} ${patientToRemove.user.last_name} from your patients list? The patient must approve this action.` : ''"
            :confirmText="'Send Request'"
            :cancelText="'Cancel'"
            :isDangerous="true"
            @confirm="confirmRemovePatient"
            @cancel="cancelRemovePatient"
        />
    </div>
</template>
