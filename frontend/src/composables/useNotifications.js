import { ref } from 'vue';

// Global notification state
const notifications = ref([]);
let notificationId = 0;

export const useNotifications = () => {
    const addNotification = (type, message, duration = 3000) => {
        const id = ++notificationId;
        const notification = {
            id,
            type, // 'success', 'error', 'warning', 'info'
            message,
            visible: true
        };
        
        notifications.value.push(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                removeNotification(id);
            }, duration);
        }
        
        return id;
    };
    
    const removeNotification = (id) => {
        const index = notifications.value.findIndex(n => n.id === id);
        if (index !== -1) {
            notifications.value.splice(index, 1);
        }
    };
    
    const success = (message, duration) => addNotification('success', message, duration);
    const error = (message, duration) => addNotification('error', message, duration);
    const warning = (message, duration) => addNotification('warning', message, duration);
    const info = (message, duration) => addNotification('info', message, duration);
    
    return {
        notifications,
        addNotification,
        removeNotification,
        success,
        error,
        warning,
        info
    };
};
