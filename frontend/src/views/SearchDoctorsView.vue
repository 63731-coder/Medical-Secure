<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '@/services/api';
import StatusAlert from '../components/StatusAlert.vue';

const query = ref('');
const allDoctors = ref([]);
const appointedDoctorIds = ref([]);
const loading = ref(true);
const error = ref('');
const currentPatientId = ref(null);
const successMessage = ref('');

onMounted(async () => {
    await fetchDoctors();
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
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch doctors:", e);
        error.value = "Failed to load doctors.";
        loading.value = false;
    }
};

const addDoctor = async (doctorId) => {
    try {
        successMessage.value = '';
        error.value = '';
        
        await api.post(`/patients/${currentPatientId.value}/add_doctor/`, { doctor_id: doctorId });
        
        // Add to appointed list
        appointedDoctorIds.value.push(doctorId);
        successMessage.value = 'Doctor added successfully!';
        
        // Auto-clear message after 3 seconds
        setTimeout(() => {
            successMessage.value = '';
        }, 3000);
    } catch (e) {
        console.error("Failed to add doctor:", e);
        error.value = 'Failed to add doctor. Please try again.';
    }
};

const isAppointed = (doctorId) => {
    return appointedDoctorIds.value.includes(doctorId);
};

const filtered = computed(() => {
    const q = query.value.trim().toLowerCase();
    if (!q) return allDoctors.value;
    return allDoctors.value.filter(d => {
        const name = `${d.user.first_name} ${d.user.last_name}`.toLowerCase();
        const org = d.organisation.toLowerCase();
        return name.includes(q) || org.includes(q);
    });
});
</script>

<template>
    <div class="max-w-5xl mx-auto py-8">
        <div class="mb-6">
            <div class="flex items-center gap-3 mb-2">
                <RouterLink to="/doctors" class="text-blue-600 hover:text-blue-800">
                    ← Back to My Doctors
                </RouterLink>
            </div>
            <h1 class="text-2xl font-extrabold text-gray-900">Search Doctors</h1>
            <p class="text-sm text-gray-500">Find and appoint doctors to access your medical records.</p>
        </div>

        <div class="mb-6">
            <input v-model="query" type="search" placeholder="Search by name or hospital"
                class="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>

        <StatusAlert v-if="successMessage" type="success" :message="successMessage" />
        <StatusAlert v-if="error" type="error" :message="error" />

        <div v-if="loading" class="text-center py-10 text-gray-500">Loading doctors...</div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="doctor in filtered" :key="doctor.id"
                class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div
                        class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center text-white text-lg font-semibold">
                        {{ doctor.user.last_name.charAt(0) }}
                    </div>
                    <div>
                        <div class="font-semibold text-gray-900">Dr. {{ doctor.user.first_name }} {{ doctor.user.last_name }}</div>
                        <div class="text-sm text-gray-500">{{ doctor.organisation }}</div>
                    </div>
                </div>

                <div class="flex items-center gap-2">
                    <RouterLink :to="{ name: 'doctor-detail', params: { id: doctor.id } }"
                        class="text-sm bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-100 px-3 py-2 rounded-md">
                        View
                    </RouterLink>
                    <button 
                        v-if="!isAppointed(doctor.id)"
                        @click="addDoctor(doctor.id)"
                        class="text-sm bg-green-50 hover:bg-green-100 text-green-700 border border-green-100 px-3 py-2 rounded-md">
                        + Add
                    </button>
                    <span 
                        v-else
                        class="text-sm text-gray-500 px-3 py-2">
                        ✓ Appointed
                    </span>
                </div>
            </div>
        </div>

        <div v-if="!loading && !filtered.length" class="mt-6 text-center text-gray-500">
            No doctors found.
        </div>
    </div>
</template>
