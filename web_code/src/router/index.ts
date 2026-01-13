import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '../components/LoginPage.vue'
import Home from '../components/Home.vue'
import Generate from '../components/Generate.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { requiresAuth: true }
    },
    {
      path: '/v2',
      name: 'generate',
      component: Generate,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    }
  ],
})

// 路由守卫：检查是否需要认证
router.beforeEach((to, from, next) => {
  // 检查路由是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 检查是否有认证token
    const token = localStorage.getItem('authToken')
    
    if (!token) {
      // 没有token，重定向到登录页面
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 记录当前路径，登录后可以跳转回来
      })
    } else {
      // 有token，继续访问
      next()
    }
  } else {
    // 不需要认证的路由，直接访问
    next()
  }
})

export default router
