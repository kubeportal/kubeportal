import Vue from 'vue'
import App from './App.vue'
import VuexPersistence from 'vuex-persist'
import store from './store/store'
import logger from './utils/logger'
import vuetify from './utils/vuetify'
import router from './utils/router'
import GAuth from 'vue-google-oauth2'
import VueClipboard from 'vue-clipboard2'
import moment from 'moment'

moment.defaultFormat = 'MMM DD hh:mm:ss'

const gauthOption = {
  clientId: '516982342717-6ri9qn82ucchr13ftdec279bm2if82n0.apps.googleusercontent.com',
  scope: 'profile email',
  prompt: 'select_account'
}

const vuexLocalStorage = new VuexPersistence({
  key: 'vuex', // The key to store the state on in the storage provider.
  storage: window.localStorage
  // reducer: (state) => ({ users: state.users })
}).plugin(store)

Vue.use(GAuth, gauthOption)
Vue.use(VueClipboard)
Vue.use(logger)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')

export default vuexLocalStorage
