<script setup>
defineProps({
    type: {
        type: String,
        default: 'info', // 'success' or 'error'
        validator: (value) => ['success', 'error', 'info'].includes(value)
    },
    message: {
        type: String,
        required: true
    }
});
</script>

<template>
    <div v-if="message" class="p-4 rounded-md mb-4 text-sm font-medium border" :class="{
        'bg-green-50 text-green-700 border-green-200': type === 'success',
        'bg-red-50 text-red-700 border-red-200': type === 'error',
        'bg-blue-50 text-blue-700 border-blue-200': type === 'info'
    }">
        {{ message }}
    </div>
</template>