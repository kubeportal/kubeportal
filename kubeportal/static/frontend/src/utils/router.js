import Vue from 'vue'
import Router from 'vue-router'
import Home from '../views/Home.vue'
import Kubeportal from '../views/Kubeportal.vue'
import Login from '../views/Login.vue'
import Settings from '../views/Settings'
import store from '@/store/store'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      name: 'Home',
      path: '/',
      redirect: '/login',
      component: Home,
      meta: {
        requiresAuth: false
      }
    },
    {
      name: 'Kubeportal',
      path: '/kubeportal',
      component: Kubeportal,
      meta: {
        requiresAuth: true
      }
    },
    {
      name: 'Login',
      path: '/login',
      component: Login,
      meta: {
        requiresAuth: false
      }
    },
    {
      name: 'Settings',
      path: '/kubeportal/settings',
      component: Settings,
      meta: {
        requiresAuth: true
      }
    },
    {
      name: 'invalidUrl',
      path: '/*',
      redirect: '/login',
      component: Login
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.matched.some(route => route.meta.requiresAuth)) {
    // this route requires auth, check if logged in
    // if not, redirect to login page.
    if (!store.getters['users/get_user']['user_id']) {
      if (!from.name === 'Login') { next({ name: 'Login' }) }
    } else {
      next() // go to wherever I'm going
    }
  } else {
    next() // does not require auth, make sure to always call next()!
  }
})

export default router
