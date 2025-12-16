import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/ProfileView.vue'

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
            component: LoginView
        },
        {
            path: '/register',   // <--- NOUVELLE ROUTE
            name: 'register',
            component: RegisterView
        },
        {
            path: '/doctors',
            name: 'doctor-list',
            component: () => import('../views/DoctorListView.vue')
        },
        {
            path: '/search-doctors',
            name: 'search-doctors',
            component: () => import('../views/SearchDoctorsView.vue')
        },
        {
            path: '/doctors/:id', // Route dynamique
            name: 'doctor-detail',
            component: () => import('../views/DoctorDetailView.vue')
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
    ]
})


// commentaire à enlever si on veut activer ne pas pouvoir naviger sans etre connecte

/*
// Simple Navigation Guard
router.beforeEach((to, from, next) => {
    const publicPages = ['/login', '/register', '/about'];
    const authRequired = !publicPages.includes(to.path);
    const loggedIn = localStorage.getItem('accessToken');

    if (authRequired && !loggedIn) {
        return next('/login');
    }
    next();
});
*/

export default router