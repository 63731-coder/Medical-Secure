<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
    show: Boolean,
    title: String,
    message: String,
    confirmText: {
        type: String,
        default: 'Confirm'
    },
    cancelText: {
        type: String,
        default: 'Cancel'
    },
    isDangerous: {
        type: Boolean,
        default: false
    }
});

const emit = defineEmits(['confirm', 'cancel']);
</script>

<template>
    <Transition name="modal">
        <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click.self="emit('cancel')">
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
                <!-- Header -->
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
                </div>

                <!-- Body -->
                <div class="px-6 py-4">
                    <p class="text-gray-700">{{ message }}</p>
                </div>

                <!-- Footer -->
                <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3">
                    <button 
                        @click="emit('cancel')"
                        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        {{ cancelText }}
                    </button>
                    <button 
                        @click="emit('confirm')"
                        :class="[
                            'px-4 py-2 text-sm font-medium text-white rounded-lg transition',
                            isDangerous 
                                ? 'bg-red-600 hover:bg-red-700' 
                                : 'bg-blue-600 hover:bg-blue-700'
                        ]"
                    >
                        {{ confirmText }}
                    </button>
                </div>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
