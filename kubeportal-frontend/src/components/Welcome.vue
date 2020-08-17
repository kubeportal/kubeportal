<template>
  <div>
  <b-card bg-variant="light" class="maincard">
    <b-card-text>
      Hello: {{ this.current_user.firstname }} !
    </b-card-text>
    <v-divider class="w-23 my-5" />
    <b-card-text>
      Fullname: {{ this.current_user.firstname }} {{ this.current_user.name }}
    </b-card-text>
    <b-card-text>
      Username: {{ this.current_user.username }}
    </b-card-text>
    <b-card-text>
      Kubernetes Service Account: {{ this.current_user.service_account }}
    </b-card-text>
  </b-card>
   <WebAppContainer />
  </div>
</template>

<script>
import WebAppContainer from './WebAppContainer'

export default {
  name: 'Welcome',
  components: { WebAppContainer },
  data () {
    return {
      metrics: this.$store.getters['get_metrics'],
      current_user: this.$store.getters['get_current_user']
    }
  },
  methods: {
    get_all_statistic_values () {
      this.metrics.map(this.request_metric_value)
    },
    async request_metric_value (metric) {
      let request_metric = metric.replace(/_/i, '')
      await this.$store.dispatch('get_statistic_metric', request_metric)
    }
  },
  created () {
    this.get_all_statistic_values()
  }
}
</script>
