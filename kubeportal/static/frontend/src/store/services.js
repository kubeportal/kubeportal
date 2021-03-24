import * as backend from '@/utils/backend'
const services_container = {
  module: {
    namespaced: true,
    state: {
      services_link: '',
      services: []
    },

    getters: {
      get_services_link (state) { return state.services_link },
      get_services (state) { return state.services }
    },

    mutations: {
      set_services_link (state, services_link) { state.services_link = services_link },
      set_services (state, services) { state.services = services },
      push_service (state, service) { state.services.push(service) }
    },

    actions: {
      async request_services (context) {
        const services_link = context.getters['get_services_link']
        const service_links = await backend.get(services_link)
        service_links.data['service_urls'].forEach(link => {
          backend.get(link).then(response => {
            let service = response.data
            console.log('SERVICES', service)
            let data = {}
            data['name'] = service.name
            data['type'] = service.type
            if(service.selector) {
              data['selector'] = `${service.selector['key']}=${service.selector['value']}`
            }
            // data['selector'] = JSON.stringify(service.selector)
            data['ports'] = service.ports.map(port => `${port['protocol']}:${port['port']} `)
            context.commit('push_service', data)
          })
        })
      }
    }
  }
}

export default services_container
