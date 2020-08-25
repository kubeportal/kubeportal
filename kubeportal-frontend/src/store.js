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
    is_authenticated: '',
    deploymentname: '',
    imagename: '',
    containername: '',
    containerport: '',
    targetport: '',
    serviceport: '',
    namespace: '',
    servicename: '',
    ingressname: '',
    domainname: '',
    subdomain: '',
    hostname_valid: '',
    current_generator_tab: 'Deployment'
  },

  getters: {
    get_all_statistics (state) { return state.statistics },
    get_metrics (state) { return state.metrics },
    get_webapps (state) { return state.webapps },
    get_current_user (state) { return state.user },
    get_jwt (state) { return state.jwt },
    get_is_authenticated (state) { return state.is_authenticated },
    get_deploymentname (state) { return state.deploymentname },
    get_imagename (state) { return state.imagename },
    get_containername (state) { return state.containername },
    get_containerport (state) { return state.containerport },
    get_serviceport (state) { return state.serviceport },
    get_namespace (state) { return state.namespace },
    get_servicename (state) { return state.servicename },
    get_domainname (state) { return state.domainname },
    get_subdomain (state) { return state.subdomain },
    get_ingressname (state) { return state.ingressname },
    get_hostname_valid (state) { return state.hostname_valid },
    get_current_generator_tab (state) { return state.current_generator_tab }
  },

  mutations: {
    set_user (state, user) { state.user = user },
    update_statistics (state, metric) { state.statistics.push(metric) },
    update_webapps (state, webapps) { state.webapps = webapps },
    update_token (state, token) { state.jwt = token },
    set_is_authenticated (state, status) { state.is_authenticated = status },
    set_deployment_name (state, name) { state.deploymentname = name },
    setTargetPort (state, port) { state.targetport = port },
    set_service_port (state, port) { state.serviceport = port },
    set_servicename (state, name) { state.servicename = name },
    set_namespace (state, namespace) { state.namespace = namespace },
    set_ingressname (state, ingressname) { state.ingressname = ingressname },
    set_container_port (state, port) { state.containerport = port },
    set_container_name (state, name) { state.containername = name },
    set_image_name (state, name) { state.imagename = name },
    set_domainname (state, name) { state.domainname = name },
    set_subdomain (state, name) { state.subdomain = name },
    setHostnameValidation (state, valid) { state.validate_hostname = valid },
    set_current_generator_tab (state, tab) { state.current_generator_tab = tab }
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
    },
    async validate_hostname (context, payload) {
      let request_body = { 'hostname' : payload }
      const validation = await backend.create('/check/ingress', request_body)
      console.log(validation)
      context.commit('setHostnameValidation', validation)
    }
  }
})
