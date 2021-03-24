import * as backend from '@/utils/backend'
import moment from 'moment'

const ingresses_container = {
  module: {
    namespaced: true,
    state: {
      ingresses_link: [],
      ingresses: []
    },

    getters: {
      get_ingresses_link (state) { return state.ingresses_link },
      get_ingresses (state) { return state.ingresses }
    },

    mutations: {
      set_ingresses_link (state, ingresses_link) { state.ingresses_link = ingresses_link },
      set_ingresses (state, ingresses) { state.ingresses = ingresses },
      push_ingress (state, ingress) { state.ingresses.push(ingress) }
    },

    actions: {
      async request_ingresses (context) {
        const ingresses_link = context.getters['get_ingresses_link']
        const ingress_links = await backend.get(ingresses_link)
        ingress_links.data['ingress_urls'].forEach(link => {
          backend.get(link).then(response => {
            let ingress = response.data
            console.log('INGRESSES', ingress)
            let data = {}
            data['name'] = ingress.name
            data['tls'] = ingress.tls
            data['creation_timestamp'] = moment(ingress.creation_timestamp).format()
            data['annotations'] = ingress.annotations.map(anno => { return `${anno['key']}: ${anno['value']}` })
            data['hosts'] = ingress.rules.map(rule => {
              return rule.paths.map(path => {
                return data['tls']
                  ? `https://${rule.host}${path['path']}`
                  : `http://${rule.host}${path['path']}`
              })
            })
            data['host_links'] = data['hosts'][0].map(host => {
              return `<a href=${host}>${host}</a>`
            })

            data['services'] = ingress.rules.map(rule => {
              return rule.paths.map(path => `${path['service_name']}:${path['service_port']}`)
            })
            data['path'] = ingress.rules.map(rule => {
              return rule.paths.map(path => `${path['path']}`)
            })
            // @TODO this should happen inside of Network.vue or we need a refresh button
            data['status'] = data['hosts'][0].map(async host => {
              const XHR = new XMLHttpRequest()
              XHR.open('OPTIONS', host)
              let loading = () => {
                if (XHR.status < 300 && XHR.status >= 200) {
                  console.log(XHR.status)
                  data['status'] = 200
                } else {
                  console.warn(XHR.statusText, XHR.responseText)
                  data['status'] = XHR.status
                }
              }
              XHR.addEventListener('load', loading)
              XHR.send()
            })

            data['annotations'] = data['annotations'].join('<br>')
            data['hosts'] = data['hosts'].join('<br>').replace(',', '<br>')
            data['services'] = data['services'].join('<br>').replace(',', '<br>')
            data['path'] = data['path'].join('<br>').replace(',', '<br>')
            data['host_links'] = data['host_links'].join('<br>').replace(',', '<br>')
            context.commit('push_ingress', data)
          })
        })
      }
    }
  }
}

export default ingresses_container
