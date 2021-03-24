import * as backend from '@/utils/backend'
import moment from 'moment'
const pods_container = {
  module: {
    namespaced: true,
    state: {
      pods_link: '',
      pods: []
    },

    getters: {
      get_pods_link (state) { return state.pods_link },
      get_pods (state) { return state.pods }
    },

    mutations: {
      set_pods_link (state, pods_link) { state.pods_link = pods_link },
      set_pods (state, pods) { state.pods = pods },
      push_pod (state, pod) { state.pods.push(pod) }
    },

    actions: {
      async request_pods (context) {
        const pods_link = context.getters['get_pods_link']
        let pod_links = await backend.get(pods_link)
        pod_links.data['pod_urls'].forEach(link => {
          backend.get(link).then(response => {
            let pod = response.data
            console.log('PODS', pod)
            let data = {}
            data['name'] = pod.name
            data['creation_timestamp'] = moment(pod.creation_timestamp).format()
            data['containers'] = pod.containers.map((container) => container.name)
            data['images'] = pod.containers.map((container) => container.image)

            context.commit('push_pod', data)
          })
        })
      }
    }
  }
}

export default pods_container
