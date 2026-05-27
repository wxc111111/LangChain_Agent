import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      component: () => import('../components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('../views/Home.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'users',
          name: 'UserList',
          component: () => import('../views/users/UserList.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'users/create',
          name: 'UserCreate',
          component: () => import('../views/users/UserCreate.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'users/:id',
          name: 'UserDetail',
          component: () => import('../views/users/UserDetail.vue'),
          meta: { requiresAuth: true, requiresAdmin: true },
        },
        {
          path: 'agent',
          name: 'AgentChat',
          component: () => import('../views/agent/AgentChat.vue'),
          meta: { requiresAuth: true },
        },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()
  const token = localStorage.getItem('access_token')

  if (to.matched.some((r) => r.meta.requiresAuth) && !token) {
    return next('/login')
  }

  if (to.meta.guest && token) {
    return next('/')
  }

  if (token && !auth.user) {
    await auth.fetchUser()
  }

  if (to.matched.some((r) => r.meta.requiresAdmin) && !auth.isAdmin) {
    return next('/')
  }

  next()
})

export default router
