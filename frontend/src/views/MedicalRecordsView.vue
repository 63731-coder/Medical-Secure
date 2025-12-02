<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { decryptData } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';

const records = ref([]);
const loading = ref(true);
const error = ref("");

// Mock Data (Replace with API call)
const fetchRecords = async () => {
    try {
        // const token = localStorage.getItem('accessToken');
        // const res = await axios.get('http://127.0.0.1:8000/api/medical-files/', ...);
        // records.value = res.data;

        // MOCK
        setTimeout(() => {
            records.value = [
                { id: 1, title: "Blood Test", date: "2025-01-10", size: "12kb" },
                { id: 2, title: "MRI Scan Report", date: "2024-12-22", size: "45kb" },
            ];
            loading.value = false;
        }, 1000);
    } catch (e) {
        error.value = "Failed to load records.";
        loading.value = false;
    }
};

const handleDownload = async (record) => {
    alert(`Downloading and Decrypting ${record.title}... (Check Console)`);
    // Logic:
    // 1. Axios GET (blob)
    // 2. Read Blob
    // 3. decryptData(blobContent)
    // 4. Create download link for user
    console.log("Decryption logic initiated for ID:", record.id);
};

onMounted(fetchRecords);
</script>

<template>
    <div class="max-w-4xl mx-auto mt-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-gray-900">My Medical Records</h1>
            <router-link to="/upload"
                class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                + Upload New
            </router-link>
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
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Action</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="file in records" :key="file.id" class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{{ file.title }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ file.date }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ file.size }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button @click="handleDownload(file)" class="text-blue-600 hover:text-blue-900 font-bold">
                                Decrypt & Download
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