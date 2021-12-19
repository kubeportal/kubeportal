import * as backend from '@/utils/backend'
import moment from 'moment'

const initial_state = () => {
  return {
    ingresses_link: [],
    ingresses: []
  }
}
const ingresses_container = {
  module: {
    namespaced: true,
    state: initial_state,

    getters: {
      get_ingresses_link (state) { return state.ingresses_link },
      get_ingresses (state) { return state.ingresses }
    },

    mutations: {
      set_ingresses_link (state, ingresses_link) { state.ingresses_link = ingresses_link },
      set_ingresses (state, ingresses) { state.ingresses = ingresses },
      set_ingress_host_status (state, data) {
        state.ingresses[data.index].status = data.status
        state.ingresses[data.index].time = data.time
      },
      push_ingress (state, ingress) { state.ingresses.push(ingress) },
      reset (state) {
        const s = initial_state()
        Object.keys(s).forEach(key => {
          state[key] = s[key]
        })
      }
    },

    actions: {
      async request_ingresses (context) {
        context.commit('set_ingresses', [])
        const ingresses_link = context.getters['get_ingresses_link']
        const ingress_links = await backend.get(ingresses_link)
        ingress_links.data['ingress_urls'].forEach((link, index) => {
          backend.get(link).then(response => {
            let ingress = response.data
            if (ingress) {
              let data = {}
              data['name'] = ingress.name
              data['tls'] = ingress.tls
              data['creation_timestamp'] = moment(ingress.creation_timestamp).fromNow()
              data['annotations'] = ingress.annotations.map(anno => { return `${anno['key']}: ${anno['value']}` })
              data['hosts'] = ingress.rules.map(rule => {
                return rule.paths.map(path => {
                  return data['tls']
                    ? `https://${rule.host}${path['path']}`
                    : `http://${rule.host}${path['path']}`
                })
              })[0]
              data['host_links'] = data['hosts'].map(host => {
                return `<a href=${host}>${host}</a>`
              })

              data['services'] = ingress.rules.map(rule => {
                return rule.paths.map(path => `${path['service_name']}:${path['service_port']}`)
              })[0]
              data['path'] = ingress.rules.map(rule => {
                return rule.paths.map(path => `${path['path']}`)
              })[0]
              data['status'] = 'pending'
              data['time'] = 'n/a'
              data['formatted_annotations'] = data['annotations'].join('<br>')
              data['formatted_services'] = data['services'].join('')
              data['formatted_path'] = data['path'].join('')
              data['formatted_host_links'] = data['host_links'].join('<br>')
              context.commit('push_ingress', data)
              //@TODO: multiple hosts?
              context.dispatch('check_availablity', { host: data['hosts'][0], index })
            }
          })
        })
      },
      async check_availablity (context, data) {
        let status = true
        let startTime = performance.now()
        let time
        fetch(data.host, { mode: 'no-cors' })
          .then((resp) => {
            if (!resp.ok || resp.status !== 200) status = false
            if (resp.type === 'opaque') status = true
            time = (performance.now() - startTime).toFixed(2)
            context.commit('set_ingress_host_status', { index: data.index, status, time })
          }).catch(() => {
            status = false
            time = 'n/a'
            context.commit('set_ingress_host_status', { index: data.index, status, time })
          })
      },
      async create_ingress (context, data) {
        const ingresses_link = context.getters['get_ingresses_link']
        const response = await backend.post(ingresses_link, data)
        console.log('CREATE INGRESS RESPONSE', response)
      }
    }
  }
}

export default ingresses_container
