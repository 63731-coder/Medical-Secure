<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

const router = useRouter();
const user = ref({ name: 'Patient', email: '—', role: 'Patient' });

onMounted(() => {
    const storedName = localStorage.getItem('username');
    const storedEmail = localStorage.getItem('email');
    if (storedName) user.value.name = storedName;
    if (storedEmail) user.value.email = storedEmail;
});

function logout() {
    // Limpiar estado local y redirigir (ajustar según autenticación real)
    localStorage.removeItem('token');
    router.push('/login');
}

function editProfile() {
    // Ruta de edición; puede necesitar ser creada en el router
    router.push('/profile/edit');
}
</script>

<template>
    <div class="max-w-4xl mx-auto py-8">
        <div class="bg-white shadow-lg rounded-xl p-6 border border-gray-100">
            <div class="flex items-center space-x-6">
                <div
                    class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold">
                    {{ user.name.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1">
                    <h2 class="text-2xl font-extrabold text-gray-900">{{ user.name }}</h2>
                    <p class="text-sm text-gray-500">{{ user.email }}</p>
                    <p class="mt-2 text-xs text-gray-400">Role: {{ user.role }}</p>
                </div>
                <div class="flex flex-col gap-2">
                    <button @click="editProfile"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg">Edit
                        Profile</button>
                    <button @click="logout"
                        class="bg-red-50 hover:bg-red-100 text-red-700 border border-red-100 font-medium px-4 py-2 rounded-lg">Log
                        out</button>
                </div>
            </div>

            <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <h3 class="font-semibold text-gray-900 mb-2">Security</h3>
                    <p class="text-sm text-gray-600 mb-3">Your data is encrypted locally. The server never sees your
                        decrypted medical records.</p>
                    <div class="flex items-center text-sm text-gray-700">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-green-600" fill="none"
                            viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 11c0-1.657-1.343-3-3-3S6 9.343 6 11s1.343 3 3 3 3-1.343 3-3z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 11V7m0 4v5m0 0H9m3 0h3" />
                        </svg>
                        <span>AES-256 local encryption active</span>
                    </div>
                </div>

                <div class="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <h3 class="font-semibold text-gray-900 mb-2">Manage Access</h3>
                    <p class="text-sm text-gray-600 mb-3">See which doctors have access to your records and revoke
                        permissions.</p>
                    <RouterLink to="/doctors"
                        class="inline-block bg-purple-600 hover:bg-purple-700 text-white font-semibold px-3 py-2 rounded-lg">
                        Manage Doctors</RouterLink>
                </div>

                <div class="md:col-span-2 p-4 bg-white rounded-lg border border-gray-100">
                    <h3 class="font-semibold text-gray-900 mb-2">Account Actions</h3>
                    <div class="flex gap-3 flex-wrap">
                        <RouterLink to="/change-password"
                            class="text-sm bg-yellow-50 hover:bg-yellow-100 text-yellow-800 border border-yellow-100 px-3 py-2 rounded-md">
                            Change Password</RouterLink>
                        <RouterLink to="/records"
                            class="text-sm bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-100 px-3 py-2 rounded-md">
                            View Medical Records</RouterLink>
                        <RouterLink to="/upload"
                            class="text-sm bg-green-50 hover:bg-green-100 text-green-800 border border-green-100 px-3 py-2 rounded-md">
                            Upload Files</RouterLink>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
