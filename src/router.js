import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import Kubeportal from './views/Kubeportal.vue'
import Login from './views/Login.vue'
import store from '@/store'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      name: 'Home',
      path: '/',
      redirect: '/login',
      component: Home
    },
    {
      name: 'Kubeportal',
      path: '/kubeportal',
      component: Kubeportal
    },
    {
      name: 'Login',
      path: '/login',
      component: Login
    }
  ]
})

router.beforeEach((to, from, next) => {
  // to and from are both route objects. must call `next`.
  if(to.fullPath === '/kubeportal') {
    if(!store.state.jwt) {
      next('/login')
    }
  }
  if(to.fullPath === '/login') {
    if(store.state.jwt) {
      next('/kubeportal')
    }
  }
  next();
})

export default router
