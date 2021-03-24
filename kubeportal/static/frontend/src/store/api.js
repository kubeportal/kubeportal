import * as backend from '@/utils/backend'

const api_container = {
  module: {
    namespaced: true,

    state: {
      branding: '',
      csrf_token: '',
      login_url: '',
      login_google_url: '',
      logout_url: ''
    },
    getters: {
      get_branding (state) { return state.branding },
      get_csrf_token (state) { return state.csrf_token },
      get_login_url (state) { return state.login_url },
      get_login_google_url (state) { return state.login_google_url },
      get_logout_url (state) { return state.logout_url }
    },

    mutations: {
      set_branding (state, branding) { state.branding = branding },
      set_csrf_token (state, csrf_token) { state.csrf_token = csrf_token },
      set_login_url (state, login_url) { state.login_url = login_url },
      set_login_google_url (state, login_google_url) { state.login_google_url = login_google_url },
      set_logout_url (state, logout_url) { state.logout_url = logout_url }
    },

    actions: {
      async get_basic_api_information (context) {
        let response = await backend.get('')
        context.commit('set_branding', response.data['branding'])
        context.commit('set_csrf_token', response.data['csrf_token'])
        context.commit('set_login_url', response.data['login_url'])
        context.commit('set_login_google_url', response.data['login_google_url'])
        context.commit('set_logout_url', response.data['logout_url'])
      }
    }
  }
}

export default api_container
