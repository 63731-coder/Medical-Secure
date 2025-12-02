<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';

const query = ref('');
const doctors = ref([]);

onMounted(() => {
    const stored = localStorage.getItem('doctors');
    if (stored) {
        try { doctors.value = JSON.parse(stored); } catch (e) { doctors.value = []; }
    }
    if (!doctors.value.length) {
        doctors.value = [
            { id: 1, name: 'Dr. Alice Martin', specialty: 'Cardiology', hospital: 'Central Hospital' },
            { id: 2, name: 'Dr. Bruno Silva', specialty: 'Dermatology', hospital: 'East Clinic' },
            { id: 3, name: 'Dr. Clara Gomez', specialty: 'Pediatrics', hospital: 'North Medical' },
            { id: 4, name: 'Dr. Daniel Kim', specialty: 'Neurology', hospital: 'West Care' },
        ];
    }
});

const filtered = computed(() => {
    const q = query.value.trim().toLowerCase();
    if (!q) return doctors.value;
    return doctors.value.filter(d => (
        d.name.toLowerCase().includes(q) ||
        d.specialty.toLowerCase().includes(q) ||
        (d.hospital && d.hospital.toLowerCase().includes(q))
    ));
});
</script>

<template>
    <div class="max-w-5xl mx-auto py-8">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-extrabold text-gray-900">Doctors</h1>
                <p class="text-sm text-gray-500">Find and manage the doctors who can access your records.</p>
            </div>
            <div class="w-72">
                <input v-model="query" type="search" placeholder="Search by name, specialty, hospital"
                    class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-200" />
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="doctor in filtered" :key="doctor.id"
                class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div
                        class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center text-white text-lg font-semibold">
                        {{ doctor.name.charAt(3) ? doctor.name.split(' ').slice(-1)[0].charAt(0) : doctor.name.charAt(0)
                        }}
                    </div>
                    <div>
                        <div class="font-semibold text-gray-900">{{ doctor.name }}</div>
                        <div class="text-sm text-gray-500">{{ doctor.specialty }} • {{ doctor.hospital }}</div>
                    </div>
                </div>

                <div class="flex items-center gap-2">
                    <RouterLink :to="{ name: 'doctor-detail', params: { id: doctor.id } }"
                        class="text-sm bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-100 px-3 py-2 rounded-md">
                        View</RouterLink>
                    <button
                        class="text-sm bg-red-50 hover:bg-red-100 text-red-700 border border-red-100 px-3 py-2 rounded-md">Revoke</button>
                </div>
            </div>
        </div>

        <div v-if="!filtered.length" class="mt-6 text-center text-gray-500">No doctors found.</div>
    </div>
</template>
