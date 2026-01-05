<template>
    <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">About SecureMed</h1>
        
        <p class="text-gray-600 mb-4 leading-relaxed">
            This project is a Proof of Concept (PoC) for a highly secure medical file exchange system. 
            It implements a <strong>Zero-Trust architecture</strong> where the server never has access to the 
            patient's data in plain text.
        </p>

        <h2 class="text-xl font-semibold text-gray-800 mt-6 mb-3">Key Features</h2>
        <ul class="list-disc pl-5 space-y-2 text-gray-600">
            <li>End-to-End Encryption (AES-256)</li>
            <li>Client-side key derivation (PBKDF2)</li>
            <li>Strict authentication protocol</li>
            <li>Secure document upload and retrieval</li>
        </ul>
    </div>
</template>

<script setup>
</script>