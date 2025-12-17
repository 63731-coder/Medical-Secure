<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { decryptData } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';

const records = ref([]);
const loading = ref(true);
const error = ref("");

// Fetch medical records from API
const fetchRecords = async () => {
    try {
        const token = localStorage.getItem('accessToken');
        const response = await axios.get('http://127.0.0.1:8000/api/files/', {
            headers: { 'Authorization': `Token ${token}` }
        });
        
        records.value = response.data;
        loading.value = false;
    } catch (e) {
        console.error("Failed to load records:", e);
        error.value = "Failed to load records.";
        loading.value = false;
    }
};

const handleDownload = async (record) => {
    try {
        const token = localStorage.getItem('accessToken');
        
        // 1. Download encrypted blob from server
        const response = await axios.get(`http://127.0.0.1:8000/api/files/${record.id}/download/`, {
            headers: { 'Authorization': `Token ${token}` },
            responseType: 'blob'
        });
        
        // 2. Read blob as text
        const encryptedText = await response.data.text();
        
        // 3. Decrypt using client-side key
        const decryptedBase64 = decryptData(encryptedText);
        
        if (!decryptedBase64) {
            throw new Error("Decryption failed. Wrong key?");
        }
        
        // 4. Convert Base64 back to binary
        const binaryString = atob(decryptedBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // 5. Create download link for decrypted file
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = record.name.replace('.enc', ''); // Remove .enc extension
        link.click();
        URL.revokeObjectURL(url);
        
        console.log(`✅ File ${record.name} decrypted and downloaded`);
    } catch (err) {
        console.error("Download/decryption error:", err);
        error.value = `Failed to decrypt ${record.name}`;
    }
};

onMounted(fetchRecords);
</script>

<template>
    <div class="max-w-4xl mx-auto mt-8">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">My Medical Records</h1>
        </div>

        <StatusAlert v-if="error" type="error" :message="error" />

        <div v-if="loading" class="text-center py-10 text-gray-500">Loading secure records...</div>

        <div v-else class="bg-white rounded-xl shadow overflow-hidden border border-gray-100">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Document Title</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Action</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="file in records" :key="file.id" class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{{ file.name }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ new Date(file.created_at).toLocaleDateString() }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ file.description || 'N/A' }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button @click="handleDownload(file)" class="text-blue-600 hover:text-blue-900 font-bold">
                                🔓 Decrypt & Download
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div v-if="records.length === 0" class="p-6 text-center text-gray-500">
                No records found.
            </div>
        </div>
    </div>
</template>