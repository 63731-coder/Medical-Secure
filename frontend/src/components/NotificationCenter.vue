<template>
    <div class="relative">
        <!-- Notification Bell Button -->
        <button @click="toggleDropdown" 
            class="relative p-2 text-white hover:text-blue-100 hover:bg-blue-700 rounded-full transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <!-- Badge -->
            <span v-if="totalCount > 0" 
                class="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                {{ totalCount > 9 ? '9+' : totalCount }}
            </span>
        </button>

        <!-- Dropdown Menu -->
        <div v-if="isOpen" 
            @click.stop
            class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
            
            <!-- Header -->
            <div class="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                <h3 class="text-lg font-semibold text-gray-900">Notifications</h3>
                <button v-if="totalCount > 0" @click="markAllAsRead" 
                    class="text-xs text-blue-600 hover:text-blue-800 font-medium">
                    Mark all as read
                </button>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="p-6 text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p class="text-gray-500 text-sm mt-2">Loading notifications...</p>
            </div>

            <!-- Notifications List -->
            <div v-else-if="notifications.length > 0" class="divide-y divide-gray-100">
                <div v-for="notification in notifications" :key="notification.id"
                    @click="handleNotificationClick(notification)"
                    :class="[
                        'p-4 hover:bg-gray-50 cursor-pointer transition',
                        !notification.read ? 'bg-blue-50' : ''
                    ]">
                    <div class="flex items-start">
                        <div :class="[
                            'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center mr-3',
                            notification.type === 'doctor_request' ? 'bg-purple-100 text-purple-600' :
                            notification.type === 'doctor_removal' ? 'bg-red-100 text-red-600' :
                            notification.type === 'file_action' ? 'bg-orange-100 text-orange-600' :
                            'bg-blue-100 text-blue-600'
                        ]">
                            <svg v-if="notification.type === 'doctor_request' || notification.type === 'doctor_removal'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            <svg v-else-if="notification.type === 'file_action'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900">{{ notification.title }}</p>
                            <p class="text-sm text-gray-600 mt-1">{{ notification.message }}</p>
                            <p class="text-xs text-gray-400 mt-1">{{ formatTime(notification.created_at) }}</p>
                        </div>
                        <div v-if="!notification.read" class="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full ml-2"></div>
                    </div>
                </div>
            </div>

            <!-- Empty State -->
            <div v-else class="p-8 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p class="text-gray-500 text-sm">No notifications</p>
                <p class="text-gray-400 text-xs mt-1">You're all caught up!</p>
            </div>
        </div>

        <!-- Backdrop to close dropdown -->
        <div v-if="isOpen" @click="closeDropdown" class="fixed inset-0 z-40"></div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();
const isOpen = ref(false);
const loading = ref(false);
const notifications = ref([]);
const userType = ref(null);

// Auto-refresh interval (every 30 seconds)
let refreshInterval = null;

const totalCount = computed(() => {
    return notifications.value.filter(n => !n.read).length;
});

const toggleDropdown = () => {
    isOpen.value = !isOpen.value;
    if (isOpen.value) {
        fetchNotifications();
    }
};

const closeDropdown = () => {
    isOpen.value = false;
};

const fetchNotifications = async () => {
    loading.value = true;
    try {
        // Get user type
        const profileRes = await api.getProfile();
        userType.value = profileRes.data.user_type;
        
        const notificationsList = [];
        
        if (userType.value === 'patient') {
            // Fetch doctor requests
            const requestsRes = await api.getRequests();
            const pendingDoctorRequests = requestsRes.data.filter(r => r.status === 'pending');
            
            pendingDoctorRequests.forEach(request => {
                const isRemoval = request.action_type === 'remove';
                notificationsList.push({
                    id: `doctor_req_${request.id}`,
                    type: isRemoval ? 'doctor_removal' : 'doctor_request',
                    title: isRemoval ? 'Doctor Removal Request' : 'New Doctor Access Request',
                    message: isRemoval 
                        ? `Dr. ${request.doctor.user.last_name} from ${request.doctor.organisation} requests to be removed from your doctors list`
                        : `Dr. ${request.doctor.user.last_name} from ${request.doctor.organisation} wants to access your medical records`,
                    created_at: request.created_at,
                    read: false,
                    action: () => router.push('/doctor-requests')
                });
            });
            
            // Fetch file action requests
            const fileActionsRes = await api.getFileActionRequests();
            const pendingFileActions = fileActionsRes.data.filter(r => r.status === 'pending');
            
            pendingFileActions.forEach(request => {
                const actionText = request.action_type === 'upload' ? 'upload a new file' :
                                 request.action_type === 'edit' ? 'edit a file' :
                                 'delete a file';
                
                notificationsList.push({
                    id: `file_action_${request.id}`,
                    type: 'file_action',
                    title: 'File Action Request',
                    message: `Dr. ${request.doctor.user.last_name} wants to ${actionText} for ${request.patient.user.first_name}`,
                    created_at: request.created_at,
                    read: false,
                    action: () => router.push('/file-action-requests')
                });
            });
        }
        
        // Sort by date (most recent first)
        notificationsList.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        notifications.value = notificationsList;
    } catch (error) {
        console.error('Failed to fetch notifications:', error);
    } finally {
        loading.value = false;
    }
};

const handleNotificationClick = (notification) => {
    if (notification.action) {
        notification.action();
    }
    closeDropdown();
};

const markAllAsRead = () => {
    notifications.value.forEach(n => n.read = true);
};

const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
};

onMounted(() => {
    fetchNotifications();
    // Refresh notifications every 30 seconds
    refreshInterval = setInterval(fetchNotifications, 30000);
});

onUnmounted(() => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// Expose totalCount for parent components
defineExpose({
    totalCount
});
</script>
