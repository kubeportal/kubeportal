import * as backend from '@/utils/backend'
import moment from 'moment'
const persistentvolumeclaims_container = {
  module: {
    namespaced: true,
    state: {
      pvc_link: '',
      persistentvolumeclaims: []
    },

    getters: {
      get_pvc_link (state) { return state.pvc_link },
      get_persistentvolumeclaims (state) { return state.persistentvolumeclaims }
    },

    mutations: {
      set_pvc_link (state, pvc_link) { state.pvc_link = pvc_link },
      set_persistentvolumeclaims (state, persistentvolumeclaims) { state.persistentvolumeclaims = persistentvolumeclaims },
      push_persistentvolumeclaim (state, persistentvolumeclaim) { state.persistentvolumeclaims.push(persistentvolumeclaim) }
    },

    actions: {
      async request_persistentvolumeclaims (context) {
        const pvc_link = context.getters['get_pvc_link']
        console.log('ooooooooooooooooooooooooooooooooooooooo')
        console.log(pvc_link)

        const persistentvolumeclaim_links = await backend.get(pvc_link)
        console.log(persistentvolumeclaim_links)
        persistentvolumeclaim_links.data['persistentvolumeclaim_urls'].forEach(link => {
          backend.get(link).then(response => {
            console.log('persistentvolumeclaims', response.data)
            let persistentvolumeclaim = response.data
            let data = {}
            data['name'] = persistentvolumeclaim.name
            data['creation_timestamp'] = moment(persistentvolumeclaim.creation_timestamp).format()
            data['size'] = persistentvolumeclaim.size
            data['access_mode'] = persistentvolumeclaim.access_modes
            data['phase'] = persistentvolumeclaim.phase
            context.commit('push_persistentvolumeclaim', data)
          })
        })
      }
    }
  }
}

export default persistentvolumeclaims_container
