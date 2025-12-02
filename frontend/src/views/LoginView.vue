<script>
import axios from "axios";
import { deriveKeyFromPassword } from '../utils/crypto';

export default {
    name: "LoginPage",
    data() {
        return {
            username: "",
            password: "",
            errorMessage: ""
        };
    },
    methods: {
        async handleLogin() {
            this.errorMessage = ""; // Reset error
            try {
                // Adjust URL if needed
                const response = await axios.post("http://127.0.0.1:8000/api/token/", {
                    username: this.username,
                    password: this.password
                });

                console.log("Login successful:", response.data);

                // Store tokens securely
                localStorage.setItem("accessToken", response.data.access);
                localStorage.setItem("refreshToken", response.data.refresh);
                
                // CRITICAL: Generate encryption key from password
                deriveKeyFromPassword(this.password);

                this.$router.push("/");
            } catch (error) {
                console.error("Login error", error);
                this.errorMessage = "Invalid username or password.";
            }
        }
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
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200 transform hover:scale-[1.02]"
            >
                Sign In
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