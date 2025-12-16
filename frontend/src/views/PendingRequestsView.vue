<template>
  <div class="pending-requests-container">
    <h1>Pending Requests</h1>

    <div class="tabs">
      <button 
        :class="['tab', { active: activeTab === 'files' }]"
        @click="activeTab = 'files'"
      >
        Medical Files
        <span class="badge" v-if="pendingFileActions.length > 0">
          {{ pendingFileActions.length }}
        </span>
      </button>
      <button 
        :class="['tab', { active: activeTab === 'appointments' }]"
        @click="activeTab = 'appointments'"
        v-if="userType === 'patient'"
      >
        Doctor Requests
        <span class="badge" v-if="appointmentRequests.length > 0">
          {{ appointmentRequests.length }}
        </span>
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading requests...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- File Action Requests Tab -->
    <div v-else-if="activeTab === 'files'" class="requests-list">
      <div v-if="pendingFileActions.length === 0" class="empty-state">
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <p>No pending file requests</p>
      </div>

      <div v-else class="request-cards">
        <div v-for="request in pendingFileActions" :key="request.id" class="request-card">
          <div class="request-header">
            <div class="request-type-badge" :class="getActionTypeClass(request.action_type)">
              {{ getActionTypeLabel(request.action_type) }}
            </div>
            <div class="request-date">
              {{ formatDate(request.created_at) }}
            </div>
          </div>

          <div class="request-body">
            <div class="request-info">
              <h3>{{ request.name || request.medical_file?.name || 'Sans nom' }}</h3>
              <p class="request-description">{{ request.description || 'Pas de description' }}</p>
              <div class="request-meta">
                <span class="meta-item">
                  <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  Dr. {{ request.requested_by?.first_name }} {{ request.requested_by?.last_name }}
                </span>
                <span class="meta-item" v-if="request.note">
                  <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
                  </svg>
                  {{ request.note }}
                </span>
              </div>
            </div>

            <div class="request-actions">
              <button @click="respondToFileAction(request.id, 'approve')" class="btn-approve">
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Approve
              </button>
              <button @click="respondToFileAction(request.id, 'reject')" class="btn-reject">
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Appointment Requests Tab -->
    <div v-else-if="activeTab === 'appointments' && userType === 'patient'" class="requests-list">
      <div v-if="appointmentRequests.length === 0" class="empty-state">
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
        </svg>
        <p>No pending appointment requests</p>
      </div>

      <div v-else class="request-cards">
        <div v-for="request in appointmentRequests" :key="request.id" class="request-card">
          <div class="request-header">
            <div class="request-type-badge appointment">
              Appointment Request
            </div>
            <div class="request-date">
              {{ formatDate(request.created_at) }}
            </div>
          </div>

          <div class="request-body">
            <div class="request-info">
              <h3>Dr. {{ request.doctor?.user?.first_name }} {{ request.doctor?.user?.last_name }}</h3>
              <p class="request-description">
                Organization: {{ request.doctor?.organisation }}
              </p>
              <div class="request-meta">
                <span class="meta-item">
                  A doctor wishes to be assigned to your medical record
                </span>
              </div>
            </div>

            <div class="request-actions">
              <button @click="respondToAppointment(request.id, 'approve')" class="btn-approve">
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Accept
              </button>
              <button @click="respondToAppointment(request.id, 'reject')" class="btn-reject">
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'PendingRequestsView',
  data() {
    return {
      activeTab: 'files',
      pendingFileActions: [],
      appointmentRequests: [],
      loading: false,
      error: null,
      userType: null,
      userProfile: null
    };
  },
  
  mounted() {
    this.loadProfile();
    this.loadRequests();
  },
  
  methods: {
    async loadProfile() {
      try {
        const response = await api.getProfile();
        this.userProfile = response.data;
        this.userType = response.data.user_type;
      } catch (error) {
        console.error('Error loading profile:', error);
      }
    },
    
    async loadRequests() {
      this.loading = true;
      this.error = null;
      
      try {
        // Load file actions for patients
        if (this.userType === 'patient') {
          const fileResponse = await api.getPendingFileActions();
          this.pendingFileActions = fileResponse.data;
          
          // Load appointment requests
          const patientId = this.userProfile?.profile?.id;
          if (patientId) {
            const appointmentResponse = await api.getAppointmentRequests(patientId);
            this.appointmentRequests = appointmentResponse.data;
          }
        }
      } catch (error) {
        this.error = "Error loading requests";
        console.error('Error loading requests:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async respondToFileAction(requestId, action) {
      try {
        const response = await api.respondToFileAction(requestId, action);
        alert(`Action ${action === 'approve' ? 'approved' : 'rejected'} successfully`);
        await this.loadRequests();
        this.$router.push('/medical-records');
      } catch (error) {
        alert(`Error responding: ${error.response?.data?.error || error.message}`);
      }
    },
    
    async respondToAppointment(requestId, action) {
      try {
        const patientId = this.userProfile?.profile?.id;
        if (!patientId) {
          alert('Unable to find your patient ID');
          return;
        }
        
        const response = await api.respondToAppointmentRequest(patientId, requestId, action);
        alert(`Request ${action === 'approve' ? 'accepted' : 'rejected'} successfully`);
        await this.loadRequests();
      } catch (error) {
        alert(`Error responding: ${error.response?.data?.error || error.message}`);
      }
    },
    
    getActionTypeClass(type) {
      const classes = {
        'upload': 'upload',
        'modify': 'modify',
        'delete': 'delete'
      };
      return classes[type] || 'default';
    },
    
    getActionTypeLabel(type) {
      const labels = {
        'upload': 'File Upload',
        'modify': 'Modification',
        'delete': 'Deletion'
      };
      return labels[type] || type;
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};
</script>

<style scoped>
.pending-requests-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 1rem;
}

h1 {
  font-size: 2rem;
  font-weight: bold;
  color: #111827;
  margin-bottom: 2rem;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e5e7eb;
}

.tab {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: #6b7280;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab:hover {
  color: #374151;
}

.tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.badge {
  padding: 0.125rem 0.5rem;
  background-color: #ef4444;
  color: white;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: bold;
}

.request-cards {
  display: grid;
  gap: 1.5rem;
}

.request-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.request-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.request-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.request-type-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
}

.request-type-badge.upload {
  background-color: #dbeafe;
  color: #1e40af;
}

.request-type-badge.modify {
  background-color: #fef3c7;
  color: #92400e;
}

.request-type-badge.delete {
  background-color: #fee2e2;
  color: #991b1b;
}

.request-type-badge.appointment {
  background-color: #e9d5ff;
  color: #6b21a8;
}

.request-date {
  color: #6b7280;
  font-size: 0.875rem;
}

.request-body {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.request-info {
  flex: 1;
}

.request-info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.5rem;
}

.request-description {
  color: #6b7280;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.request-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.icon {
  width: 1rem;
  height: 1rem;
}

.request-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-approve, .btn-reject {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.btn-approve {
  background-color: #10b981;
  color: white;
}

.btn-approve:hover {
  background-color: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.25);
}

.btn-reject {
  background-color: #ef4444;
  color: white;
}

.btn-reject:hover {
  background-color: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(239, 68, 68, 0.25);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #f9fafb;
  border-radius: 0.75rem;
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

@media (max-width: 768px) {
  .request-body {
    flex-direction: column;
    align-items: stretch;
  }
  
  .request-actions {
    justify-content: stretch;
  }
  
  .btn-approve, .btn-reject {
    flex: 1;
    justify-content: center;
  }
}
</style>
