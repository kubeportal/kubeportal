import * as backend from '@/utils/backend'
import moment from 'moment'

const initial_state = () => {
  return {
    pods_link: '',
    pods: [],
    pod_logs: {},
    page_numbers: {}
  }
}

const pods_container = {
  module: {
    namespaced: true,
    state: initial_state,

    getters: {
      get_pods_link (state) {
        return state.pods_link
      },
      get_pods (state) {
        return state.pods
      },
      get_pod_logs (state) {
        return state.pod_logs
      },
      get_page_numbers (state) {
        return state.page_numbers
      }
    },

    mutations: {
      reset (state) {
        const s = initial_state()
        Object.keys(s).forEach(key => {
          state[key] = s[key]
        })
      },
      set_pods_link (state, pods_link) {
        state.pods_link = pods_link
      },
      set_pods (state, pods) {
        state.pods = pods
      },
      push_pod (state, pod) {
        state.pods.push(pod)
      },
      set_page_number (state, data) {
        state.page_numbers[data.pod_name] = data.page_number
      }
    },

    actions: {
      async request_pods (context) {
        context.commit('set_pods', [])
        const pods_link = context.getters['get_pods_link']
        let pod_links = await backend.get(pods_link)
        pod_links.data['pod_urls'].forEach(link => {
          backend.get(link).then(response => {
            let pod = response.data
            let data = {}
            data = { ...pod }
            data['creation_timestamp'] = moment(pod.creation_timestamp).fromNow()
            data['start_timestamp'] = moment(pod.start_timestamp).fromNow()
            data['containers'] = pod.containers.map(container => container.name)
            data['images'] = pod.containers.map(container => container.image)
            data['volume_names'] = pod.containers.map(container =>
              container.volume_mounts.map(volume => volume.volume.name))[0]
            data['volume_type'] = pod.containers.map(container =>
              container.volume_mounts.map(volume => volume.volume.type)[0])
            data['mountpath'] = pod.containers.map(container => container.volume_mounts.map(volume => volume.mount_path))[0]
            data['volumes'] = pod.containers.map(container => container.volume_mounts)[0]
            data['logs_url'] = pod.logs_url
            context.commit('push_pod', data)
          })
        })
      },
      async create_pod (context, data) {
        const pods_link = context.getters['get_pods_link']
        backend.post(pods_link, data)
      },
      async request_logs (_, data) {
        let link = data.logs_url + '?page=' + data.page_number
        const response = await backend.get(link)
        let result = response.data.hits.map(hit => {
          let log = {}
          log['log'] = hit._source.log
          log['stream'] = hit._source.stream
          log['timestamp'] = moment(hit._source['@timestamp']).format('MMMM Do YYYY, h:mm:ss a')
          log['_id'] = hit._id
          return log
        })
        let total = response.data.total
        return [result, total]
      },
      async request_zip_logs_download (_, data) {
        const response = await backend.get(data.logs_url, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', data.file_name)
        document.body.appendChild(link)
        link.click()
      }
    }
  }
}

export default pods_container
