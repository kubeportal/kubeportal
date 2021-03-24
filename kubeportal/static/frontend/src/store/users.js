import Vue from 'vue'
import * as backend from '@/utils/backend'
import store from './store.js'

const users_container = {
  module: {
    namespaced: true,

    state: {
      access_token: '',
      refresh_token: '',
      url: '',
      user: {
        webapp_ids: []
      },
      webapps: [],
      groups: [],
      approval_url: '',
      dark_mode: false,
      approving_admins: []
    },

    getters: {
      get_access_token (state) { return state.access_token },
      get_refresh_token (state) { return state.refresh_token },
      get_url (state) { return state.url },
      get_user (state) { return state.user },
      get_webapps (state) { return state.webapps },
      get_groups (state) { return state.groups },
      get_approval_url (state) { return state.approval_url },
      get_dark_mode (state) { return state.dark_mode },
      get_approving_admins (state) { return state.approving_admins }
    },

    mutations: {
      set_access_token (state, token) { state.access_token = token },
      set_refresh_token (state, token) { state.refresh_token = token },
      set_url (state, url) { state.url = url },
      set_user (state, user) { state.user = user },
      push_webapp (state, webapp) { state.webapps.push(webapp) },
      push_group (state, group) { state.groups.push(group) },
      set_webapps (state, webapps) { state.webapps = webapps },
      set_groups (state, groups) { state.groups = groups },
      set_approval_url (state, url) { state.approval_url = url },
      set_dark_mode (state) { state.dark_mode = !state.dark_mode },
      push_approving_admin (state, admin) { state.approving_admins.push(admin) },
      set_approving_admins (state, admins) { state.approving_admins = admins }
    },

    actions: {
      async post_login_data (context, request_body) {
        let login_url = store.getters['api/get_login_url']
        console.log('LOGIN URL', login_url)
        const response = await backend.post(store.getters['api/get_login_url'], request_body)
        if (response) {
          console.log('POST LOGIN DATA', response.data)
          context.commit('set_access_token', response.data['access_token'])
          context.commit('set_refresh_token', response.data['refresh_token'])
          context.commit('set_url', response.data['user_url'])
          context.commit('set_approval_url', response.data['user_approval_url'])
          store.commit('news/set_news_url', response.data['news_url'])
          store.commit('infos/set_infos_url', response.data['infos_url'])
          const user_details = await backend.get(response.data['user_url'])
          console.log('USER DETAILS', user_details.data)
          context.commit('set_user', user_details.data)
          context.dispatch('request_namespaces')
        }
        return response
      },

      async authorize_google_user (context, auth_response) {
        const response = await backend.post(store.getters['api/get_login_google_url'], auth_response)
        // @ TODO
        return response
      },
      async request_webapps (context) {
        const current_user = context.getters['get_user']
        console.log('CURRENT_USER', current_user)
        for (const webapp_url of current_user['webapp_urls']) {
          const response = await backend.get(webapp_url)
          let res_data = response.data
          if (res_data.link_url.includes('{{namespace}}')) {
            res_data.link_url = res_data.link_url.replace('{{namespace}}', current_user['namespace_names'][0])
          }
          // @TODO: Service accounts are currently urls
          // if (res_data.link_url.includes('{{serviceaccount}}')) {
          //   res_data.link_url = res_data.link_url.replace('{{serviceaccount}}', current_user['get_namespace'])
          // }
          context.commit('push_webapp', response.data)
        }
      },
      async request_groups (context) {
        const current_user = context.getters['get_user']
        for (const group_url of current_user['group_urls']) {
          const response = await backend.get(group_url)
          console.log('GROUP', response.data)
          context.commit('push_group', response.data)
        }
      },
      async request_namespaces (context) {
        const current_user = context.getters['get_user']
        if (current_user['state'] === 'ACCESS_APPROVED') {
          const response = await backend.get(current_user['namespace_urls'][0])
          console.log('NAMESPACE RESPONSE', response.data)
          store.commit('pods/set_pods_link', response.data['pods_url'])
          store.commit('deployments/set_deployments_link', response.data['deployments_url'])
          store.commit('services/set_services_link', response.data['services_url'])
          store.commit('ingresses/set_ingresses_link', response.data['ingresses_url'])
          store.commit('pvcs/set_pvc_link', response.data['persistentvolumeclaims_url'])
        }
      },
      async update_user (context, payload) {
        const response = await backend.patch(context.state.url, payload)
        context.commit('set_user', response.data)
      },
      async request_current_user (context) {
        const response = await backend.get(context.state.url)
        context.commit('set_user', response.data)
      },
      log_out () {
        backend.post(store.getters['api/get_logout_url'])
      },
      async switch_dark_mode (context) {
        context.commit('set_dark_mode')
        return context.getters['get_dark_mode']
      },
      async request_approving_info (context) {
        const response = await backend.get(context.state.approval_url)
        // console.log('APPROVING ADMINS GET', context.state.url + 'approval/')
        // const response = await backend.get(context.state.url + 'approval/')
        response.data['approving_admin_urls'].forEach(admin_url => {
          backend.get(admin_url).then(admin_res => {
            console.log('APPROVING ADMINS GET', admin_res.data)
            context.commit('push_approving_admin', { admin: admin_res.data, url: admin_url })
          })
        })
      },
      async send_approval_request (context, admin_urls) {
        admin_urls.forEach(url => {
          backend.post(context.state.approval_url, { approving_admin_url: url }).then(res => {
            console.log('SEND ADMIN APPROVAL RESPONSE', res)
            context.dispatch('request_current_user')
          })
        })
      }
    }
  }
}

export default users_container
