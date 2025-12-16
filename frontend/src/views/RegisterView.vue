<script>
import axios from "axios";

export default {
    name: "RegisterPage",
    data() {
        return {
            username: "",
            email: "",
            password: "",
            confirmPassword: "",
            firstName: "",
            lastName: "",
            dateOfBirth: "",
            errorMessage: "",
            successMessage: ""
        };
    },
    methods: {
        async handleRegister() {
            this.errorMessage = "";
            this.successMessage = "";

            // 1. Basic Validation
            if (this.password !== this.confirmPassword) {
                this.errorMessage = "Passwords do not match.";
                return;
            }

            if (this.password.length < 8) {
                this.errorMessage = "Password must be at least 8 characters long.";
                return;
            }

            try {
                // 2. Prepare registration data (always patient)
                const registrationData = {
                    username: this.username,
                    email: this.email,
                    password: this.password,
                    first_name: this.firstName,
                    last_name: this.lastName,
                    user_type: 'patient',
                    date_of_birth: this.dateOfBirth
                };

                // 3. Call Django API
                await axios.post("http://127.0.0.1:8000/api/register/", registrationData);

                this.successMessage = "Account created successfully! Redirecting to login...";
                
                // 3. Redirect to Login after 2 seconds
                setTimeout(() => {
                    this.$router.push("/login");
                }, 2000);

            } catch (error) {
                console.error("Registration error", error);
                // Display specific error from Django if available
                if (error.response && error.response.data) {
                    this.errorMessage = JSON.stringify(error.response.data);
                } else {
                    this.errorMessage = "Registration failed. Please try again.";
                }
            }
        }
    }
};
</script>

<template>
    <div class="max-w-md mx-auto mt-10 bg-white rounded-xl shadow-md overflow-hidden md:max-w-lg border border-gray-100">
        <div class="bg-green-600 p-4 text-center">
            <h2 class="text-xl font-bold text-white">Create Account</h2>
            <p class="text-green-100 text-xs">Join SecureMed Portal</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="p-8 space-y-4">
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="firstName">
                        First Name
                    </label>
                    <input 
                        id="firstName"
                        type="text" 
                        v-model="firstName" 
                        required 
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                        placeholder="John"
                    />
                </div>
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="lastName">
                        Last Name
                    </label>
                    <input 
                        id="lastName"
                        type="text" 
                        v-model="lastName" 
                        required 
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                        placeholder="Doe"
                    />
                </div>
            </div>

            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="dateOfBirth">
                    Date of Birth
                </label>
                <input 
                    id="dateOfBirth"
                    type="date" 
                    v-model="dateOfBirth" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                />
            </div>

            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="username">
                    Username
                </label>
                <input 
                    id="username"
                    type="text" 
                    v-model="username" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                    placeholder="Choose a username"
                />
            </div>

            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                    Email Address
                </label>
                <input 
                    id="email"
                    type="email" 
                    v-model="email" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                    placeholder="name@example.com"
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
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                    placeholder="Create a strong password"
                />
            </div>

            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="confirmPassword">
                    Confirm Password
                </label>
                <input 
                    id="confirmPassword"
                    type="password" 
                    v-model="confirmPassword" 
                    required 
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition"
                    placeholder="Repeat password"
                />
            </div>

            <div v-if="errorMessage" class="bg-red-50 text-red-700 px-4 py-3 rounded text-sm">
                {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="bg-green-50 text-green-700 px-4 py-3 rounded text-sm">
                {{ successMessage }}
            </div>

            <button 
                type="submit"
                class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200 transform hover:scale-[1.02]"
            >
                Register
            </button>

            <div class="text-center mt-4">
                <p class="text-sm text-gray-600">
                    Already have an account? 
                    <RouterLink to="/login" class="text-green-600 hover:underline font-bold">
                        Sign In
                    </RouterLink>
                </p>
            </div>
        </form>
    </div>
</template>