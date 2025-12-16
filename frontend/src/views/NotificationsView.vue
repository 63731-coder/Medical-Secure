<template>
  <div class="notifications-container">
    <div class="notifications-header">
      <h1>Notifications</h1>
      <div class="header-actions">
        <button v-if="unreadCount > 0" @click="markAllAsRead" class="btn-secondary">
          Mark all as read
        </button>
        <span class="notification-badge" v-if="unreadCount > 0">
          {{ unreadCount }} unread
        </span>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading notifications...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else-if="notifications.length === 0" class="empty-state">
      <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
      </svg>
      <p>No notifications</p>
    </div>

    <div v-else class="notifications-list">
      <div v-for="notification in notifications" :key="notification.id" 
           :class="['notification-item', { 'unread': !notification.is_read }]"
           @click="handleNotificationClick(notification)">
        
        <div class="notification-icon" :class="getNotificationIconClass(notification.notification_type)">
          <span v-if="notification.notification_type === 'file_action_request'">📄</span>
          <span v-else-if="notification.notification_type === 'appointment_request'">👨‍⚕️</span>
          <span v-else-if="notification.notification_type === 'request_approved'">✅</span>
          <span v-else-if="notification.notification_type === 'request_rejected'">❌</span>
        </div>

        <div class="notification-content">
          <h3 class="notification-title">{{ notification.title }}</h3>
          <p class="notification-message">{{ notification.message }}</p>
          <div class="notification-meta">
            <span class="notification-time">{{ formatDate(notification.created_at) }}</span>
            <span v-if="!notification.is_read" class="unread-indicator">Unread</span>
          </div>
        </div>

        <div v-if="notification.file_action_request && notification.file_action_request.status === 'pending'" 
             class="notification-actions">
          <button @click.stop="respondToFileAction(notification.file_action_request.id, 'approve')" 
                  class="btn-approve">
            Approve
          </button>
          <button @click.stop="respondToFileAction(notification.file_action_request.id, 'reject')" 
                  class="btn-reject">
            Reject
          </button>
        </div>

        <div v-else-if="notification.appointment_request && notification.appointment_request.status === 'pending'" 
             class="notification-actions">
          <button @click.stop="respondToAppointment(notification.appointment_request, 'approve')" 
                  class="btn-approve">
            Approve
          </button>
          <button @click.stop="respondToAppointment(notification.appointment_request, 'reject')" 
                  class="btn-reject">
            Reject
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'NotificationsView',
  data() {
    return {
      notifications: [],
      unreadCount: 0,
      loading: false,
      error: null,
      userProfile: null
    };
  },
  
  mounted() {
    this.loadNotifications();
    this.loadProfile();
  },
  
  methods: {
    async loadProfile() {
      try {
        const response = await api.getProfile();
        this.userProfile = response.data;
      } catch (error) {
        console.error('Error loading profile:', error);
      }
    },
    
    async loadNotifications() {
      this.loading = true;
      this.error = null;
      
      try {
        const [notificationsResponse, countResponse] = await Promise.all([
          api.getNotifications(),
          api.getUnreadNotificationCount()
        ]);
        
        this.notifications = notificationsResponse.data;
        this.unreadCount = countResponse.data.unread_count;
      } catch (error) {
        this.error = "Error loading notifications";
        console.error('Error loading notifications:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async handleNotificationClick(notification) {
      if (!notification.is_read) {
        try {
          await api.markNotificationAsRead(notification.id);
          notification.is_read = true;
          this.unreadCount = Math.max(0, this.unreadCount - 1);
        } catch (error) {
          console.error('Error marking notification as read:', error);
        }
      }
    },
    
    async markAllAsRead() {
      try {
        await api.markAllNotificationsAsRead();
        this.notifications.forEach(n => n.is_read = true);
        this.unreadCount = 0;
        this.$emit('notifications-updated', 0);
      } catch (error) {
        console.error('Error marking all as read:', error);
      }
    },
    
    async respondToFileAction(requestId, action) {
      try {
        const response = await api.respondToFileAction(requestId, action);
        alert(`Action ${action === 'approve' ? 'approved' : 'rejected'} successfully`);
        await this.loadNotifications();
      } catch (error) {
        alert(`Error responding: ${error.response?.data?.error || error.message}`);
      }
    },
    
    async respondToAppointment(request, action) {
      try {
        const patientId = this.userProfile?.profile?.id;
        if (!patientId) {
          alert('Unable to find your patient ID');
          return;
        }
        
        const response = await api.respondToAppointmentRequest(patientId, request.id, action);
        alert(`Request ${action === 'approve' ? 'approved' : 'rejected'} successfully`);
        await this.loadNotifications();
      } catch (error) {
        alert(`Error responding: ${error.response?.data?.error || error.message}`);
      }
    },
    
    getNotificationIconClass(type) {
      const classes = {
        'file_action_request': 'icon-file',
        'appointment_request': 'icon-appointment',
        'request_approved': 'icon-approved',
        'request_rejected': 'icon-rejected'
      };
      return classes[type] || 'icon-default';
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
      
      return date.toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'short',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    }
  }
};
</script>

<style scoped>
.notifications-container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 1rem;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.notifications-header h1 {
  font-size: 2rem;
  font-weight: bold;
  color: #111827;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background-color: #6b7280;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background-color: #4b5563;
}

.notification-badge {
  padding: 0.25rem 0.75rem;
  background-color: #ef4444;
  color: white;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: bold;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.notification-item:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.notification-item.unread {
  background-color: #eff6ff;
  border-color: #60a5fa;
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: #3b82f6;
  border-radius: 0.5rem 0 0 0.5rem;
}

.notification-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  border-radius: 0.5rem;
  margin-right: 1rem;
  flex-shrink: 0;
}

.icon-file {
  background-color: #fef3c7;
}

.icon-appointment {
  background-color: #dbeafe;
}

.icon-approved {
  background-color: #d1fae5;
}

.icon-rejected {
  background-color: #fee2e2;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #111827;
}

.notification-message {
  color: #6b7280;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.notification-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #9ca3af;
}

.unread-indicator {
  color: #3b82f6;
  font-weight: 600;
}

.notification-actions {
  display: flex;
  gap: 0.5rem;
  margin-left: 1rem;
}

.btn-approve, .btn-reject {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-approve {
  background-color: #10b981;
  color: white;
}

.btn-approve:hover {
  background-color: #059669;
}

.btn-reject {
  background-color: #ef4444;
  color: white;
}

.btn-reject:hover {
  background-color: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1rem;
  color: #9ca3af;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 1rem;
  background-color: #fee2e2;
  color: #b91c1c;
  border-radius: 0.5rem;
  text-align: center;
}
</style>
