<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from "axios";
import { deriveKeyFromPassword } from '../utils/crypto';
import { useNotifications } from '../composables/useNotifications';

const router = useRouter();
const { success, error } = useNotifications();

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const loading = ref(false);

const handleLogin = async () => {
    errorMessage.value = "";
    loading.value = true;
    
    try {
        const response = await axios.post("http://127.0.0.1:8000/api/login/", {
            username: username.value,
            password: password.value
        });

        console.log("Login successful:", response.data);

        // Store token securely
        localStorage.setItem("accessToken", response.data.token);
        localStorage.setItem("userId", response.data.user_id);
        localStorage.setItem("userType", response.data.user_type);
        localStorage.setItem("username", username.value);
        
        // CRITICAL: Generate encryption key from password
        deriveKeyFromPassword(password.value);

        success("Welcome back! Login successful");
        
        setTimeout(() => {
            router.push("/");
        }, 500);
    } catch (err) {
        console.error("Login error", err);
        errorMessage.value = "Invalid username or password.";
        error("Invalid username or password");
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <div class="max-w-md mx-auto mt-10 bg-white rounded-xl shadow-md overflow-hidden md:max-w-lg border border-gray-100">
        <div class="bg-blue-600 p-4 text-center">
            <h2 class="text-xl font-bold text-white">Authentication</h2>
            <p class="text-blue-100 text-xs">Please sign in to access encrypted data</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="p-8 space-y-6">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="username">
                    Username
                </label>
                <input 
                    id="username"
                    type="text" 
                    v-model="username" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    placeholder="Enter your username"
                />
            </div>

            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="password">
                    Password
                </label>
                <input 
                    id="password"
                    type="password" 
                    v-model="password" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    placeholder="Enter your password"
                />
            </div>

            <div v-if="errorMessage" class="bg-red-50 text-red-700 px-4 py-3 rounded relative text-sm" role="alert">
                <span class="block sm:inline">{{ errorMessage }}</span>
            </div>

            <button 
                type="submit"
                :disabled="loading"
                :class="[
                    'w-full font-bold py-2 px-4 rounded-lg transition duration-200 transform',
                    loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 hover:scale-[1.02]',
                    'text-white'
                ]"
            >
                <span v-if="loading" class="flex items-center justify-center">
                    <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Signing in...
                </span>
                <span v-else>Sign In</span>
            </button>
        </form>

        <div class="text-center mt-4">
                <p class="text-sm text-gray-600">
                    Don't have an account? 
                    <RouterLink to="/register" class="text-blue-600 hover:underline font-bold">
                        Register here
                    </RouterLink>
                </p>
            </div>
        
        <div class="bg-gray-50 px-8 py-4 text-center">
            <p class="text-xs text-gray-500">
                Secure connection protected by AES-256 encryption.
            </p>
        </div>
    </div>
</template>