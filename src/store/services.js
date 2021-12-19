import * as backend from '@/utils/backend'
import moment from 'moment'

const initial_state = () => {
  return {
    services_link: '',
    services: []
  }
}
const services_container = {
  module: {
    namespaced: true,
    state: initial_state,

    getters: {
      get_services_link (state) { return state.services_link },
      get_services (state) { return state.services }
    },

    mutations: {
      set_services_link (state, services_link) { state.services_link = services_link },
      set_services (state, services) { state.services = services },
      push_service (state, service) { state.services.push(service) },
      reset (state) {
        const s = initial_state()
        Object.keys(s).forEach(key => {
          state[key] = s[key]
        })
      }
    },

    actions: {
      async request_services (context) {
        context.commit('set_services', [])
        const services_link = context.getters['get_services_link']
        const service_links = await backend.get(services_link)
        service_links.data['service_urls'].forEach(link => {
          backend.get(link).then(response => {
            let service = response.data
            let data = {}
            data['name'] = service.name
            data['type'] = service.type
            data['creation_timestamp'] = moment(service.creation_timestamp).fromNow()
            if(service.selector) {
              data['selector'] = `${service.selector['key']}=${service.selector['value']}`
            }
            data['ports'] = service.ports.map(port => `${port['protocol']}:${port['port']} `)
            data['target_ports'] = service.ports.map(port => port['target_port'])
            data['formatted_ports'] = data['ports'].join('<br>')
            data['formatted_target_ports'] = data['target_ports'].join('<br>')
            context.commit('push_service', data)
          })
        })
      },
      async create_service (context, data) {
        const services_link = context.getters['get_services_link']
        const response = await backend.post(services_link, data)
        console.log('CREATE SERVICE RESPONSE', response)
      }
    }
  }
}

export default services_container
