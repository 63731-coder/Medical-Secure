<template>
    <div class="container mx-auto px-4 py-8 max-w-6xl">
        <!-- Header -->
        <div class="mb-8">
            <div class="flex items-center mb-4">
                <button @click="$router.back()" 
                    class="mr-4 text-gray-600 hover:text-gray-900 transition">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                </button>
                <h1 class="text-3xl font-bold text-gray-900">Add Patient</h1>
            </div>
            <p class="text-gray-600">Request access to a patient's medical records</p>
        </div>

        <!-- Alert Messages -->
        <StatusAlert v-if="alert.show" :type="alert.type" :message="alert.message" @close="alert.show = false" />

        <!-- Search Bar -->
        <div class="mb-6 bg-white rounded-lg shadow-sm p-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Search Patients
            </label>
            <div class="relative">
                <input v-model="searchQuery" type="text" 
                    placeholder="Filter by name or username..."
                    class="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
            </div>
            <p class="mt-2 text-sm text-gray-500">
                Found {{ filteredPatients().length }} patient(s)
            </p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p class="mt-4 text-gray-600">Loading patients...</p>
        </div>

        <!-- Patient List -->
        <div v-else-if="filteredPatients().length > 0" class="bg-white rounded-lg shadow-sm overflow-hidden">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                <div v-for="patient in filteredPatients()" :key="patient.id"
                    class="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md cursor-pointer transition-all"
                    @click="requestAddPatient(patient)">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center mb-3">
                                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-3 shadow-sm">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="font-bold text-lg text-gray-900">
                                        @{{ patient.user.username }}
                                    </h3>
                                    <p class="text-xs text-gray-500 flex items-center mt-0.5">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                        </svg>
                                        Private information
                                    </p>
                                </div>
                            </div>
                            <div class="mt-3 space-y-1.5 text-sm">
                                <div class="flex items-center text-gray-700">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                    <span class="text-xs font-medium">{{ patient.user.email }}</span>
                                </div>
                                <div v-if="patient.phone_number" class="flex items-center text-gray-700">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                    </svg>
                                    <span class="text-xs font-medium">{{ patient.phone_number }}</span>
                                </div>
                                <div class="mt-2 pt-2 border-t border-gray-100">
                                    <p class="text-xs text-gray-500 italic">Click to request access to this patient's medical records</p>
                                </div>
                            </div>
                        </div>
                        <div class="ml-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div v-else class="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 class="text-lg font-medium text-gray-900 mb-2">
                {{ searchQuery ? 'No matching patients found' : 'No available patients' }}
            </h3>
            <p class="text-gray-500">
                {{ searchQuery ? 'Try a different search term' : 'All patients are already in your list or have pending requests' }}
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import StatusAlert from '@/components/StatusAlert.vue';
import { useNotifications } from '@/composables/useNotifications';

const router = useRouter();
const { success, error: notifyError } = useNotifications();

const loading = ref(true);
const allPatients = ref([]);
const myPatients = ref([]);
const pendingRequests = ref([]);
const searchQuery = ref('');

const alert = ref({
    show: false,
    type: 'success',
    message: ''
});

const showAlert = (type, message) => {
    alert.value = { show: true, type, message };
    setTimeout(() => {
        alert.value.show = false;
    }, 3000);
};

const filteredPatients = () => {
    const myPatientIds = myPatients.value.map(p => p.id);
    
    return allPatients.value.filter(p => {
        // Don't show patients already in my list
        if (myPatientIds.includes(p.id)) return false;
        
        // Check if there's already a pending request for this patient
        const hasPendingRequest = pendingRequests.value.some(r => r.patient.id === p.id);
        if (hasPendingRequest) return false;
        
        // Search filter (if search query exists)
        if (searchQuery.value) {
            const query = searchQuery.value.toLowerCase();
            const username = p.user.username.toLowerCase();
            const email = p.user.email.toLowerCase();
            return username.includes(query) || email.includes(query);
        }
        
        // Show all if no search query
        return true;
    });
};

const requestAddPatient = async (patient) => {
    try {
        await api.createRequest({ 
            patient_id: patient.id,
            action_type: 'add'  // Required for doctor-initiated requests
        });
        success(`Access request sent to @${patient.user.username}`);
        showAlert('success', `Access request sent to @${patient.user.username}`);
        
        // Add to pending requests to remove from available list
        pendingRequests.value.push({ patient });
        
        // Navigate back after a short delay
        setTimeout(() => {
            router.push('/my-patients');
        }, 1500);
    } catch (err) {
        console.error('Error creating request:', err);
        const errorMsg = err.response?.data?.error || 'Failed to send access request';
        notifyError(errorMsg);
        showAlert('error', errorMsg);
    }
};

const fetchData = async () => {
    loading.value = true;
    try {
        const [allPatientsRes, myPatientsRes, requestsRes] = await Promise.all([
            api.getAllPatients(),
            api.getPatients(),
            api.getRequests()
        ]);
        
        allPatients.value = allPatientsRes.data;
        myPatients.value = myPatientsRes.data;
        pendingRequests.value = requestsRes.data.filter(r => r.status === 'pending');
    } catch (error) {
        console.error('Error fetching data:', error);
        showAlert('error', 'Failed to load patients');
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchData();
});
</script>
