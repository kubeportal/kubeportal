import moment from 'moment'

export default {
  install (Vue, options) {
    Vue.prototype.$log = log_to_console
  }
}

function log_to_console (input) {
  const timestamp = moment().format('YYYY-MM-DD HH:mm:ss')
  const route = this.$route.name
  console.info(`[${timestamp}] @${route}: ${input}`)
}
