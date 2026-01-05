<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '@/services/api';
import StatusAlert from '../components/StatusAlert.vue';
import { encryptKeyForDoctor } from '../utils/crypto';

const query = ref('');
const allDoctors = ref([]);
const appointedDoctorIds = ref([]);
const loading = ref(true);
const error = ref('');
const currentPatientId = ref(null);
const successMessage = ref('');
const currentUser = ref(null);
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
        
        currentUser.value = profileRes.data;
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

// Check if a string looks like encrypted data (Base64 CryptoJS format)
const isEncryptedString = (str) => {
    if (!str) return false;
    // CryptoJS encrypted strings start with "U2FsdGVkX1" (Base64 for "Salted__")
    return str.startsWith('U2FsdGVkX1');
};

// Get doctor names - doctors' names should NOT be encrypted (public professional info)
// But handle legacy encrypted names gracefully by falling back to username
const decryptDoctorsData = async () => {
    for (const doctor of allDoctors.value) {
        try {
            // Doctor names should be in plain text in Django User model
            let firstName = doctor.user.first_name || '';
            let lastName = doctor.user.last_name || '';
            
            // Check if names are encrypted (legacy issue) - use username instead
            if (isEncryptedString(firstName) || isEncryptedString(lastName)) {
                firstName = doctor.user.username;
                lastName = '';
            }
            
            decryptedDoctors.value[doctor.id] = { firstName, lastName };
        } catch (e) {
            // Fallback to username if something fails
            decryptedDoctors.value[doctor.id] = {
                firstName: doctor.user.username,
                lastName: ''
            };
        }
    }
};

const addDoctor = async (doctorId) => {
    try {
        successMessage.value = '';
        error.value = '';
        
        // Step 1: Add doctor to patient's appointed list
        await api.post(`/patients/${currentPatientId.value}/add_doctor/`, { doctor_id: doctorId });
        
        // Step 2: Share encryption key with the doctor
        const patientKey = sessionStorage.getItem('encryptionKey');
        if (patientKey) {
            // Find doctor info
            const doctor = allDoctors.value.find(d => d.id === doctorId);
            if (doctor) {
                // Encrypt patient's key for secure sharing
                const encryptedKey = encryptKeyForDoctor(patientKey, doctor.id);
                
                // Share encrypted key via API
                try {
                    await api.post('/share-key/', {
                        doctor_id: doctorId,
                        key: encryptedKey
                    });
                } catch (keyError) {
                    console.error('Failed to share encryption key:', keyError);
                    // Don't fail the whole operation if key sharing fails
                }
            }
        }
        
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

const filtered = computed(() => {
    const q = query.value.trim().toLowerCase();
    if (!q) return allDoctors.value;
    return allDoctors.value.filter(d => {
        const { firstName, lastName } = getDoctorName(d);
        const name = `${firstName} ${lastName}`.toLowerCase();
        const org = getDoctorOrganisation(d).toLowerCase();
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
