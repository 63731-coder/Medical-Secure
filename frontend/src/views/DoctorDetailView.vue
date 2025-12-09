<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// import axios from 'axios';

const route = useRoute(); // To get ID from URL
const router = useRouter(); // To go back
const doctorId = route.params.id;

const doctor = ref(null);
const loading = ref(true);

onMounted(() => {
    // Mock Fetch based on doctorId
    setTimeout(() => {
        doctor.value = {
            id: doctorId,
            name: "Dr. Gregory House",
            specialty: "Diagnostic Medicine",
            email: "house@securemed.com",
            hospital: "Princeton-Plainsboro",
            bio: "Specializes in solving medical puzzles. Unconventional methods."
        };
        loading.value = false;
    }, 500);
});

const goBack = () => router.back();
</script>

<template>
    <div class="max-w-2xl mx-auto mt-10">
        <button @click="goBack"
            class="mb-4 text-gray-500 hover:text-gray-900 flex items-center text-sm font-medium transition">
            &larr; Back to List
        </button>

        <div v-if="loading" class="text-center p-10">Loading details...</div>

        <div v-else class="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
            <div class="h-32 bg-blue-600"></div>
            <div class="px-8 pb-8">
                <div class="-mt-12 mb-6">
                    <div class="w-24 h-24 rounded-full bg-white p-1 shadow-md inline-block">
                        <div
                            class="w-full h-full rounded-full bg-gray-200 flex items-center justify-center text-2xl text-gray-500">
                            👨‍⚕️
                        </div>
                    </div>
                </div>

                <h1 class="text-3xl font-bold text-gray-900">{{ doctor.name }}</h1>
                <p class="text-blue-600 font-medium mb-4">{{ doctor.specialty }}</p>

                <div class="space-y-4 text-gray-600">
                    <div class="flex items-center">
                        <svg class="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4">
                            </path>
                        </svg>
                        {{ doctor.hospital }}
                    </div>
                    <div class="flex items-center">
                        <svg class="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z">
                            </path>
                        </svg>
                        {{ doctor.email }}
                    </div>

                    <hr class="border-gray-100 my-4" />

                    <h3 class="font-bold text-gray-800">Biography</h3>
                    <p class="leading-relaxed text-sm">{{ doctor.bio }}</p>
                </div>

                <div class="mt-8 flex gap-4">
                    <button
                        class="flex-1 bg-red-50 text-red-600 hover:bg-red-100 py-2 rounded-lg font-medium transition">
                        Remove Access
                    </button>
                    <button
                        class="flex-1 bg-blue-600 text-white hover:bg-blue-700 py-2 rounded-lg font-medium transition">
                        Send Message
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>