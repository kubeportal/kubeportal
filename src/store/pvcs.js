import * as backend from '@/utils/backend'
import moment from 'moment'

const initial_state = () => {
  return {
    pvc_link: '',
    persistentvolumeclaims: [],
    storageclasses_url: '',
    storageclasses: []
  }
}

const persistentvolumeclaims_container = {
  module: {
    namespaced: true,
    state: initial_state,

    getters: {
      get_pvc_link (state) { return state.pvc_link },
      get_persistentvolumeclaims (state) { return state.persistentvolumeclaims },
      get_storageclasses_url (state) { return state.storageclasses_url },
      get_storageclasses (state) { return state.storageclasses }
    },

    mutations: {
      reset (state) {
        const s = initial_state()
        Object.keys(s).forEach(key => {
          state[key] = s[key]
        })
      },
      set_pvc_link (state, pvc_link) { state.pvc_link = pvc_link },
      set_persistentvolumeclaims (state, persistentvolumeclaims) { state.persistentvolumeclaims = persistentvolumeclaims },
      push_persistentvolumeclaim (state, persistentvolumeclaim) { state.persistentvolumeclaims.push(persistentvolumeclaim) },
      set_storageclasses_url (state, url) { state.storageclasses_url = url },
      set_storageclasses (state, storageclasses) { state.storageclasses = storageclasses }
    },

    actions: {
      async request_persistentvolumeclaims (context) {
        context.commit('set_persistentvolumeclaims', [])
        const pvc_link = context.getters['get_pvc_link']
        const persistentvolumeclaim_links = await backend.get(pvc_link)
        persistentvolumeclaim_links.data['persistentvolumeclaim_urls'].forEach(link => {
          backend.get(link).then(response => {
            let persistentvolumeclaim = response.data
            let data = {}
            data['name'] = persistentvolumeclaim.name
            data['creation_timestamp'] = moment(persistentvolumeclaim.creation_timestamp).fromNow()
            data['size'] = persistentvolumeclaim.size
            data['access_mode'] = persistentvolumeclaim.access_modes
            data['phase'] = persistentvolumeclaim.phase
            context.commit('push_persistentvolumeclaim', data)
          })
        })
      },
      async create_pvc (context, data) {
        const pvc_link = context.getters['get_pvc_link']
        const response = await backend.post(pvc_link, data)
        console.log('CREATE PVC RESPONSE', response)
      },
      async request_storageclasses (context) {
        const storageclasses_url = context.getters['get_storageclasses_url']
        backend.get(storageclasses_url).then(response => {
          let storageclass_names = ['(default)', ...response.data['classes']]
          context.commit('set_storageclasses', storageclass_names)
        })
      }
    }
  }
}

export default persistentvolumeclaims_container
