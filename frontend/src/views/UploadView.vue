<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { encryptData } from '../utils/crypto'; // Using your existing crypto utility
import StatusAlert from '../components/StatusAlert.vue';

const file = ref(null);
const title = ref("");
const loading = ref(false);
const status = ref({ type: 'info', message: '' });

const handleFileChange = (event) => {
    file.value = event.target.files[0];
};

const handleUpload = async () => {
    if (!file.value || !title.value) {
        status.value = { type: 'error', message: "Please select a file and a title." };
        return;
    }

    loading.value = true;
    status.value = { type: 'info', message: "Reading and encrypting file..." };

    // 1. Read file locally
    const reader = new FileReader();
    reader.readAsText(file.value); // For PoC (Use readAsArrayBuffer for PDFs/Images in production)

    reader.onload = async (e) => {
        try {
            const rawContent = e.target.result;

            // 2. Encrypt Content (Client-Side)
            // The server NEVER sees the rawContent
            const encryptedContent = encryptData(rawContent);

            if (!encryptedContent) {
                throw new Error("Encryption failed. Are you logged in?");
            }

            // 3. Prepare Form Data (Django expects a file)
            // We create a new Blob from the encrypted string
            const encryptedBlob = new Blob([encryptedContent], { type: 'text/plain' });
            const formData = new FormData();
            formData.append('name', title.value);
            formData.append('file', encryptedBlob, file.value.name + ".enc"); // Add .enc extension

            // 4. Send to Server
            status.value = { type: 'info', message: "Uploading encrypted data..." };
            const token = localStorage.getItem('accessToken');

            await axios.post('http://127.0.0.1:8000/api/medical-files/', formData, {
                headers: {
                    'Authorization': `Token ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });

            status.value = { type: 'success', message: "File encrypted and uploaded successfully!" };
            title.value = "";
            file.value = null;

        } catch (error) {
            console.error(error);
            status.value = { type: 'error', message: "Upload failed: " + error.message };
        } finally {
            loading.value = false;
        }
    };
};
</script>

<template>
    <div class="max-w-xl mx-auto bg-white p-8 rounded-xl shadow border border-gray-100 mt-10">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Secure Document Upload</h2>

        <StatusAlert :type="status.type" :message="status.message" />

        <form @submit.prevent="handleUpload" class="space-y-6">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Document Title</label>
                <input v-model="title" type="text" required
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="e.g., Blood Test Results">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Select File</label>
                <div
                    class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition">
                    <input type="file" @change="handleFileChange"
                        class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                </div>
                <p class="text-xs text-gray-500 mt-2">File will be encrypted locally using AES-256 before upload.</p>
            </div>

            <button type="submit" :disabled="loading"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition disabled:bg-blue-300">
                {{ loading ? 'Processing...' : 'Encrypt & Upload' }}
            </button>
        </form>
    </div>
</template>