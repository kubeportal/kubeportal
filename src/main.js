import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import '@/assets/css/tailwind.css'
import logger from '@/plugins/logger'
import vuetify from './plugins/vuetify'
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'
import GAuth from 'vue-google-oauth2'

const gauthOption = {
  clientId: '516982342717-6ri9qn82ucchr13ftdec279bm2if82n0.apps.googleusercontent.com',
  scope: 'profile email',
  prompt: 'select_account'
}

Vue.use(GAuth, gauthOption)
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(logger)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')
