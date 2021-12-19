import Vue from 'vue'
import Vuex from 'vuex'
import wizard from './wizard.js'
import infos from './infos.js'
import users from './users.js'
import api from './api.js'
import news from './news.js'
import pods from './pods.js'
import services from './services.js'
import ingresses from './ingresses.js'
import persistentvolumeclaims from './pvcs.js'
import deployments from './deployments.js'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {},
  getters: {},
  mutations: {},
  actions: {},
  modules: {
    users: users.module,
    infos: infos.module,
    wizard: wizard.module,
    api: api.module,
    news: news.module,
    pods: pods.module,
    deployments: deployments.module,
    services: services.module,
    ingresses: ingresses.module,
    pvcs: persistentvolumeclaims.module
  }
})

export default store
