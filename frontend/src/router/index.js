import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import LoginViewKeycloak from '../views/LoginViewKeycloak.vue'
import CallbackView from '../views/CallbackView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/ProfileView.vue'
import api from '../services/api'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/about',
            name: 'about',
            // Chargement "paresseux" (lazy-loaded) pour l'optimisation
            component: () => import('../views/AboutView.vue')
        },
        {
            path: '/login',
            name: 'login',
            component: LoginViewKeycloak  // New Keycloak login
        },
        {
            path: '/login-legacy',
            name: 'login-legacy',
            component: LoginView  // Old password login
        },
        {
            path: '/callback',  // OAuth2 callback route
            name: 'callback',
            component: CallbackView
        },
        {
            path: '/register',   // <--- NOUVELLE ROUTE
            name: 'register',
            component: RegisterView
        },
        {
            path: '/doctors',
            name: 'doctor-list',
            component: () => import('../views/DoctorListView.vue'),
            meta: { requiresPatient: true }
        },
        {
            path: '/search-doctors',
            name: 'search-doctors',
            component: () => import('../views/SearchDoctorsView.vue'),
            meta: { requiresPatient: true }
        },
        {
            path: '/doctors/:id', // Route dynamique
            name: 'doctor-detail',
            component: () => import('../views/DoctorDetailView.vue'),
            meta: { requiresPatient: true }
        },
        {
            path: '/upload',
            name: 'upload',
            component: () => import('../views/UploadView.vue')
        },
        {
            path: '/profile',
            name: 'profile',
            component: ProfileView
        },
        {
            path: '/profile/edit',
            name: 'profile-edit',
            component: ProfileView
        },
        {
            path: '/records',
            name: 'records',
            component: () => import('../views/MedicalRecordsView.vue')
        },
        {
            path: '/my-patients',
            name: 'my-patients',
            component: () => import('../views/MyPatientsView.vue'),
            meta: { requiresDoctor: true }
        },
        {
            path: '/add-patient',
            name: 'add-patient',
            component: () => import('../views/AddPatientView.vue'),
            meta: { requiresDoctor: true }
        },
        {
            path: '/doctor-requests',
            name: 'doctor-requests',
            component: () => import('../views/DoctorRequestsView.vue'),
            meta: { requiresPatient: true }
        },
        {
            path: '/file-action-requests',
            name: 'file-action-requests',
            component: () => import('../views/FileActionRequestsView.vue'),
            meta: { requiresPatient: true }
        },
    ]
})


// commentaire à enlever si on veut activer ne pas pouvoir naviger sans etre connecte


// Simple Navigation Guard
router.beforeEach(async (to, from, next) => {
    const publicPages = ['/login', '/register', '/about', '/callback'];
    const authRequired = !publicPages.includes(to.path);
    const loggedIn = localStorage.getItem('access_token'); // Keycloak uses 'access_token'

    if (authRequired && !loggedIn) {
        return next('/login');
    }

    // Check if route requires specific user type
    if (to.meta.requiresDoctor || to.meta.requiresPatient) {
        try {
            const response = await api.getProfile();
            const userType = response.data.user_type;
            
            // Block doctors from patient-only routes
            if (to.meta.requiresPatient && userType !== 'patient') {
                console.warn('Access denied: Patient-only route');
                return next('/'); // Redirect to home
            }
            
            // Block patients from doctor-only routes
            if (to.meta.requiresDoctor && userType !== 'doctor') {
                console.warn('Access denied: Doctor-only route');
                return next('/'); // Redirect to home
            }
        } catch (error) {
            console.error('Failed to check user type:', error);
            return next('/');
        }
    }

    next();
});


export default router