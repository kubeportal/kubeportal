import Vue from 'vue'
import Vuex from 'vuex'
import * as backend from './api/backend'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: {},
    metrics: ['kubernetes', 'api_server', 'cluster_nodes', 'cpu_cores', 'main_memory', 'deployed_pods', 'allocated_volumes', 'portal_users', 'kubeportal'],
    statistics : [],
    webapps: [],
    jwt: '',
    is_authenticated: ''
  },

  getters: {
    get_all_statistics (state) { return state.statistics },
    get_metrics (state) { return state.metrics },
    get_webapps (state) { return state.webapps },
    get_current_user (state) { return state.user },
    get_jwt (state) { return state.jwt },
    get_is_authenticated (state) { return state.is_authenticated }
  },

  mutations: {
    set_user (state, user) { state.user = user },
    update_statistics (state, metric) { state.statistics.push(metric) },
    update_webapps (state, webapps) { state.webapps = webapps },
    update_token (state, token) { state.jwt = token },
    set_is_authenticated (state, status) { state.is_authenticated = status }
  },
  actions: {
    async get_current_user (context, field) {
      const user = await backend.readByField('/users', field, context.state.jwt)
      context.commit('set_user', user)
      return user
    },
    async get_statistic_metric (context, field) {
      const statistics = await backend.readByField('/statistics', field, context.state.jwt)
      context.commit('update_statistics', statistics)
      return statistics
    },
    async get_webapps (context) {
      const webapps = await backend.read('/webapps', context.state.jwt)
      context.commit('update_webapps', webapps)
      return webapps
    },
    async post_login_data (context, request_body) {
      const response = await backend.create('/login', request_body)
      return response
    },
    async authorize_google_user (context, auth_response) {
      const response = await backend.create('/login/authorize_google_user', auth_response)
      return response
    }
  }
})
