<template>
  <div class="audit-log-container">
    <div class="audit-header">
      <h1>Audit Log</h1>
      <div class="header-filters">
        <button @click="activeFilter = 'all'" 
                :class="['filter-btn', { active: activeFilter === 'all' }]">
          All actions
        </button>
        <button @click="activeFilter = 'security'" 
                :class="['filter-btn', { active: activeFilter === 'security' }]">
          Security events
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading audit log...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else-if="logs.length === 0" class="empty-state">
      <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
      </svg>
      <p>No entries in the log</p>
    </div>

    <div v-else>
      <!-- Statistics Summary -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon view">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-value">{{ getActionCount('view_file') }}</p>
            <p class="stat-label">Views</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon download">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-value">{{ getActionCount('download_file') }}</p>
            <p class="stat-label">Downloads</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon approve">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-value">{{ getActionCount('approve_request') }}</p>
            <p class="stat-label">Approvals</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon deny">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-value">{{ getActionCount('permission_denied') }}</p>
            <p class="stat-label">Access denied</p>
          </div>
        </div>
      </div>

      <!-- Audit Log Table -->
      <div class="audit-table-container">
        <table class="audit-table">
          <thead>
            <tr>
              <th>Date/Time</th>
              <th>Action</th>
              <th>User</th>
              <th>File</th>
              <th>Status</th>
              <th>IP Address</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in filteredLogs" :key="log.id" 
                :class="{ 'error-row': !log.success }">
              <td>
                <span class="timestamp">{{ formatDate(log.created_at) }}</span>
              </td>
              <td>
                <span :class="['action-badge', getActionClass(log.action)]">
                  {{ getActionLabel(log.action) }}
                </span>
              </td>
              <td>
                <div class="user-info">
                  {{ log.user?.username || 'System' }}
                  <small v-if="log.user?.first_name">
                    {{ log.user.first_name }} {{ log.user.last_name }}
                  </small>
                </div>
              </td>
              <td>
                <span v-if="log.medical_file">
                  File #{{ log.medical_file }}
                </span>
                <span v-else class="text-gray">-</span>
              </td>
              <td>
                <span :class="['status-badge', log.success ? 'success' : 'error']">
                  {{ log.success ? 'Success' : 'Failed' }}
                </span>
              </td>
              <td>
                <span class="ip-address">{{ log.ip_address || '-' }}</span>
              </td>
              <td>
                <button @click="showDetails(log)" class="details-btn">
                  <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="selectedLog" class="modal-overlay" @click="selectedLog = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Action Details</h2>
          <button @click="selectedLog = null" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Date/Time:</span>
            <span>{{ formatFullDate(selectedLog.created_at) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Action:</span>
            <span>{{ getActionLabel(selectedLog.action) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">User:</span>
            <span>{{ selectedLog.user?.username }} ({{ selectedLog.user?.email }})</span>
          </div>
          <div class="detail-row" v-if="selectedLog.ip_address">
            <span class="detail-label">IP Address:</span>
            <span>{{ selectedLog.ip_address }}</span>
          </div>
          <div class="detail-row" v-if="selectedLog.user_agent">
            <span class="detail-label">User Agent:</span>
            <span class="user-agent">{{ selectedLog.user_agent }}</span>
          </div>
          <div class="detail-row" v-if="selectedLog.error_message">
            <span class="detail-label">Error message:</span>
            <span class="error-text">{{ selectedLog.error_message }}</span>
          </div>
          <div class="detail-row" v-if="selectedLog.details && Object.keys(selectedLog.details).length > 0">
            <span class="detail-label">Additional details:</span>
            <pre class="json-details">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'AuditLogView',
  data() {
    return {
      logs: [],
      loading: false,
      error: null,
      activeFilter: 'all',
      selectedLog: null
    };
  },
  
  computed: {
    filteredLogs() {
      if (this.activeFilter === 'security') {
        const securityActions = ['login', 'logout', 'permission_denied'];
        return this.logs.filter(log => securityActions.includes(log.action));
      }
      return this.logs;
    }
  },
  
  mounted() {
    this.loadLogs();
  },
  
  methods: {
    async loadLogs() {
      this.loading = true;
      this.error = null;
      
      try {
        let response;
        if (this.activeFilter === 'security') {
          response = await api.getSecurityEvents();
        } else {
          response = await api.getAuditLogs();
        }
        this.logs = response.data;
      } catch (error) {
        this.error = "Error loading audit log";
        console.error('Error loading audit logs:', error);
      } finally {
        this.loading = false;
      }
    },
    
    getActionCount(action) {
      return this.logs.filter(log => log.action === action).length;
    },
    
    getActionClass(action) {
      const classes = {
        'view_file': 'view',
        'download_file': 'download',
        'upload_file': 'upload',
        'modify_file': 'modify',
        'delete_file': 'delete',
        'approve_request': 'approve',
        'reject_request': 'reject',
        'login': 'auth',
        'logout': 'auth',
        'permission_denied': 'deny'
      };
      return classes[action] || 'default';
    },
    
    getActionLabel(action) {
      const labels = {
        'view_file': 'View File',
        'download_file': 'Download',
        'upload_file': 'Upload',
        'modify_file': 'Modify',
        'delete_file': 'Delete',
        'approve_request': 'Approval',
        'reject_request': 'Rejection',
        'login': 'Login',
        'logout': 'Logout',
        'permission_denied': 'Access Denied'
      };
      return labels[action] || action;
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    formatFullDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    },
    
    showDetails(log) {
      this.selectedLog = log;
    }
  },
  
  watch: {
    activeFilter() {
      this.loadLogs();
    }
  }
};
</script>

<style scoped>
.audit-log-container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 1rem;
}

.audit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.audit-header h1 {
  font-size: 2rem;
  font-weight: bold;
  color: #111827;
}

.header-filters {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background-color: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background-color: #f9fafb;
}

.filter-btn.active {
  background-color: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

/* Statistics Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
}

.stat-icon svg {
  width: 1.5rem;
  height: 1.5rem;
}

.stat-icon.view {
  background-color: #dbeafe;
  color: #2563eb;
}

.stat-icon.download {
  background-color: #d1fae5;
  color: #059669;
}

.stat-icon.approve {
  background-color: #fef3c7;
  color: #d97706;
}

.stat-icon.deny {
  background-color: #fee2e2;
  color: #dc2626;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #111827;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
}

/* Audit Table */
.audit-table-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow-x: auto;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
}

.audit-table thead {
  background-color: #f9fafb;
}

.audit-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.audit-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.audit-table tbody tr:hover {
  background-color: #f9fafb;
}

.error-row {
  background-color: #fef2f2;
}

.timestamp {
  color: #6b7280;
  font-size: 0.875rem;
}

.action-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.action-badge.view {
  background-color: #dbeafe;
  color: #1e40af;
}

.action-badge.download {
  background-color: #d1fae5;
  color: #065f46;
}

.action-badge.upload {
  background-color: #e9d5ff;
  color: #6b21a8;
}

.action-badge.modify {
  background-color: #fef3c7;
  color: #92400e;
}

.action-badge.delete {
  background-color: #fee2e2;
  color: #991b1b;
}

.action-badge.approve {
  background-color: #d1fae5;
  color: #065f46;
}

.action-badge.reject {
  background-color: #fee2e2;
  color: #991b1b;
}

.action-badge.auth {
  background-color: #e0e7ff;
  color: #3730a3;
}

.action-badge.deny {
  background-color: #fee2e2;
  color: #991b1b;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-info small {
  color: #9ca3af;
  font-size: 0.75rem;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.success {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.error {
  background-color: #fee2e2;
  color: #991b1b;
}

.ip-address {
  font-family: monospace;
  color: #6b7280;
}

.text-gray {
  color: #9ca3af;
}

.details-btn {
  padding: 0.25rem 0.5rem;
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.details-btn:hover {
  background-color: #e5e7eb;
}

.details-btn .icon {
  width: 1rem;
  height: 1rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
}

.close-btn:hover {
  color: #374151;
}

.modal-body {
  padding: 1.25rem;
}

.detail-row {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 600;
  color: #374151;
}

.user-agent {
  font-family: monospace;
  font-size: 0.875rem;
  color: #6b7280;
  word-break: break-all;
}

.error-text {
  color: #dc2626;
}

.json-details {
  background-color: #f9fafb;
  padding: 0.75rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.75rem;
  overflow-x: auto;
}

/* Loading & Empty States */
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

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #f9fafb;
  border-radius: 0.5rem;
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1rem;
  color: #9ca3af;
}

.error-message {
  padding: 1rem;
  background-color: #fee2e2;
  color: #b91c1c;
  border-radius: 0.5rem;
  text-align: center;
}
</style>
