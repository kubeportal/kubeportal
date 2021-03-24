import * as backend from '@/utils/backend'
import moment from 'moment'
const deployments_container = {
  module: {
    namespaced: true,
    state: {
      deployments_link: '',
      deployments: []
    },

    getters: {
      get_deployments_link (state) { return state.deployments_link },
      get_deployments (state) { return state.deployments }
    },

    mutations: {
      set_deployments_link (state, deployments_link) { state.deployments_link = deployments_link },
      set_deployments (state, deployments) { state.deployments = deployments },
      push_deployment (state, deployment) { state.deployments.push(deployment) }
    },

    actions: {
      async request_deployments (context) {
        const deployments_link = context.getters['get_deployments_link']
        let deployment_links = await backend.get(deployments_link)
        deployment_links.data['deployment_urls'].forEach(link => {
          backend.get(link).then(response => {
            console.log('DEPLOYMENTS', response)
            let deployment = response.data
            let data = {}
            data['name'] = deployment.name
            data['creation_timestamp'] = moment(deployment.creation_timestamp).format()
            data['replicas'] = deployment.replicas
            context.commit('push_deployment', data)
          })
        })
      }
    }
  }
}

export default deployments_container
