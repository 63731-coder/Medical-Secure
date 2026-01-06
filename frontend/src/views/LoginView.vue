<template>
    <div class="max-w-md mx-auto mt-10 bg-white rounded-xl shadow-md overflow-hidden md:max-w-lg border border-gray-100">
        <div class="bg-blue-600 p-6 text-center">
            <h2 class="text-2xl font-bold text-white">
                Secure Login
            </h2>
            <p class="text-blue-100 text-sm mt-1">
                Passwordless authentication with Secure ID
            </p>
        </div>

        <div class="p-8 space-y-6">
            <button
                @click="loginWithKeycloak"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 transform hover:scale-[1.02]"
            >
                🔐 Sign in with Secure ID
            </button>

            <p class="text-xs text-center text-gray-500">
                You will be redirected to a secure authentication service.
            </p>
        </div>

        <div class="bg-gray-50 px-8 py-4 text-center">
            <p class="text-xs text-gray-500">
                Protected by WebAuthn • No passwords stored
            </p>
        </div>
    </div>
</template>


<script>
/**
 * LoginView - Passwordless authentication page
 * Redirects users to Keycloak for WebAuthn authentication
 */
export default {
    name: "LoginView",
    methods: {
        loginWithKeycloak() {
            const params = new URLSearchParams({
                client_id: "medical-app",
                redirect_uri: "http://localhost:5173/callback",
                response_type: "code",
                scope: "openid profile email"
            });

            window.location.href =
                "http://localhost:8080/realms/medical-realm/protocol/openid-connect/auth?" +
                params.toString();
        }
    }
};
</script>