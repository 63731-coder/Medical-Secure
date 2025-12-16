<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';
import { decryptData } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';

const records = ref([]);
const loading = ref(true);
const error = ref("");
const userProfile = ref(null);
const userType = ref(null);
const selectedFile = ref(null);
const showDeleteConfirm = ref(false);

// Fetch user profile
const fetchProfile = async () => {
    try {
        const response = await api.getProfile();
        userProfile.value = response.data;
        userType.value = response.data.user_type;
    } catch (e) {
        console.error('Error fetching profile:', e);
    }
};

// Fetch medical records
const fetchRecords = async () => {
    loading.value = true;
    error.value = "";
    
    try {
        const response = await api.getMedicalRecord();
        records.value = response.data;
    } catch (e) {
        error.value = "Error loading medical records.";
        console.error('Error fetching records:', e);
    } finally {
        loading.value = false;
    }
};

// Download file
const handleDownload = async (record) => {
    if (!record.file) {
        alert("File not available or awaiting approval");
        return;
    }
    
    try {
        const response = await api.downloadFileSecure(record.id);
        
        // Create blob link for download
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = record.name || `file_${record.id}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Log audit action
        console.log(`File downloaded: ${record.name}`);
    } catch (e) {
        alert("Error downloading file");
        console.error('Download error:', e);
    }
};

// Delete file (patient only)
const confirmDelete = (record) => {
    selectedFile.value = record;
    showDeleteConfirm.value = true;
};

const handleDelete = async () => {
    if (!selectedFile.value) return;
    
    try {
        await api.deleteFile(selectedFile.value.id);
        alert('File deleted successfully');
        await fetchRecords();
    } catch (e) {
        alert("Error deleting file");
        console.error('Delete error:', e);
    } finally {
        showDeleteConfirm.value = false;
        selectedFile.value = null;
    }
};

const cancelDelete = () => {
    showDeleteConfirm.value = false;
    selectedFile.value = null;
};

// Check if user can delete file
const canDeleteFile = (file) => {
    return userType.value === 'patient';
};

// Check if user can view file
const canViewFile = (file) => {
    // Patient can always view their files
    if (userType.value === 'patient') return true;
    // Doctor can only view approved files
    if (userType.value === 'doctor') return file.approved;
    return false;
};

// Format date
const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
};

// Get status badge class
const getStatusClass = (file) => {
    if (!file.approved) return 'pending';
    return 'approved';
};

// Get status label
const getStatusLabel = (file) => {
    if (!file.approved) return 'Pending';
    return 'Approved';
};

onMounted(() => {
    fetchProfile();
    fetchRecords();
});
</script>

<template>
    <div class="max-w-6xl mx-auto mt-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Medical Records</h1>
            <div class="flex gap-3">
                <router-link v-if="userType === 'patient'" to="/pending-requests"
                    class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                    Pending Requests
                </router-link>
                <router-link to="/upload"
                    class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                    + Add File
                </router-link>
            </div>
        </div>

        <StatusAlert v-if="error" type="error" :message="error" />

        <div v-if="loading" class="text-center py-10 text-gray-500">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <p class="mt-2">Loading secure records...</p>
        </div>

        <div v-else class="bg-white rounded-xl shadow overflow-hidden border border-gray-100">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Document Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Date</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Uploaded By</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status</th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="file in records" :key="file.id" 
                        :class="['hover:bg-gray-50 transition', { 'opacity-60': !file.approved }]">
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <svg class="h-5 w-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                <span class="font-medium text-gray-900">{{ file.name || 'Unnamed' }}</span>
                            </div>
                            <div v-if="file.description" class="text-xs text-gray-500 mt-1 ml-7">
                                {{ file.description }}
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">
                            {{ formatDate(file.created_at) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">
                            <div v-if="file.uploaded_by">
                                <span>{{ file.uploaded_by.first_name }} {{ file.uploaded_by.last_name }}</span>
                                <div class="text-xs text-gray-400">{{ file.uploaded_by.username }}</div>
                            </div>
                            <span v-else>-</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span :class="['inline-flex px-2 py-1 text-xs font-semibold rounded-full',
                                          getStatusClass(file) === 'approved' 
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-yellow-100 text-yellow-800']">
                                {{ getStatusLabel(file) }}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div class="flex justify-end gap-2">
                                <button v-if="canViewFile(file)" 
                                        @click="handleDownload(file)" 
                                        class="text-blue-600 hover:text-blue-900 font-bold"
                                        :disabled="!file.file">
                                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
                                    </svg>
                                </button>
                                <button v-if="canDeleteFile(file)" 
                                        @click="confirmDelete(file)" 
                                        class="text-red-600 hover:text-red-900">
                                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                    </svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div v-if="records.length === 0" class="p-6 text-center text-gray-500">
                <svg class="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <p>No medical records found</p>
                <p class="text-sm mt-1">Start by adding your first file</p>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteConfirm" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Deletion</h3>
                <p class="text-sm text-gray-500 mb-6">
                    Are you sure you want to delete the file "{{ selectedFile?.name }}"?
                    This action cannot be undone.
                </p>
                <div class="flex gap-3 justify-end">
                    <button @click="cancelDelete" 
                            class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                        Cancel
                    </button>
                    <button @click="handleDelete" 
                            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>