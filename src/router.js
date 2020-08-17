import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import Kubeportal from './views/Kubeportal.vue'
import Login from './views/Login.vue'

Vue.use(Router)

export default new Router({
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
