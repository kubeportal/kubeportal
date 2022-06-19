import * as backend from '@/utils/backend'
import moment from 'moment'

const initial_state = () => {
  return {
    deployments_link: '',
    deployments: []
  }
}

const deployments_container = {
  module: {
    namespaced: true,
    state: initial_state,

    getters: {
      get_deployments_link (state) { return state.deployments_link },
      get_deployments (state) { return state.deployments }
    },

    mutations: {
      reset (state) {
        const s = initial_state()
        Object.keys(s).forEach(key => {
          state[key] = s[key]
        })
      },
      set_deployments_link (state, deployments_link) { state.deployments_link = deployments_link },
      set_deployments (state, deployments) { state.deployments = deployments },
      push_deployment (state, deployment) { state.deployments.push(deployment) }
    },

    actions: {
      async request_deployments (context) {
        context.commit('set_deployments', [])
        const deployments_link = context.getters['get_deployments_link']
        let deployment_links = await backend.get(deployments_link)
        deployment_links.data['deployment_urls'].forEach(link => {
          backend.get(link).then(response => {
            let deployment = response.data
            let data = {}
            data['name'] = deployment.name
            data['creation_timestamp'] = moment(deployment.creation_timestamp).fromNow()
            data['replicas'] = deployment.replicas
            context.commit('push_deployment', data)
          })
        })
      },
      async create_deployment (context, data) {
        const deployments_link = context.getters['get_deployments_link']
        const response = await backend.post(deployments_link, data)
        console.log('CREATE DEPLOYMENT RESPONSE', response)
      }
    }
  }
}

export default deployments_container
