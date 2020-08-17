<template>
  <v-card class="app">
    <v-tabs vertical dark class="sidenav">
      <v-tab>
        <v-icon class="icon" left>mdi-home-heart</v-icon>
        <show-at breakpoint="mediumAndAbove">
          <div class="title"><small>Welcome</small></div>
        </show-at>
      </v-tab>
      <v-tab>
        <v-icon class="icon" left>mdi-file-document-outline</v-icon>
        <show-at breakpoint="mediumAndAbove">
          <div class="title"><small>Config</small></div>
        </show-at>
      </v-tab>
      <v-tab>
        <v-icon class="icon" left>mdi-chart-pie</v-icon>
        <show-at breakpoint="mediumAndAbove">
          <div class="title"><small>Statistics</small></div>
        </show-at>
      </v-tab>
      <v-tab @click="openAdmin" v-if="userIsAdmin">
        <v-icon class="icon" left>mdi-tools</v-icon>
        <show-at breakpoint="mediumAndAbove">
          <div class="title"><small>Admin</small></div>
        </show-at>
      </v-tab>
      <v-tab @click="logout">
        <v-icon class="icon" left>mdi-logout-variant</v-icon>
        <show-at breakpoint="mediumAndAbove">
          <div class="title"><small>Logout</small></div>
        </show-at>
      </v-tab>

      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Welcome />
          </v-card-text>
        </v-card>
      </v-tab-item>

      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Config />
          </v-card-text>
        </v-card>
      </v-tab-item>
      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Statistics />
          </v-card-text>
        </v-card>
      </v-tab-item>
    </v-tabs>
  </v-card>
</template>

<script>

import Welcome from '@/components/Welcome'
import Statistics from '@/components/Statistics'
import Config from '@/components/Config/Config'
import {showAt} from 'vue-breakpoints'

export default {
  name: 'App',

  components: { Statistics, Welcome, Config, showAt },
  data () {
    return {
      metrics: this.$store.getters['get_metrics']
    }
  },
  methods: {
    get_all_statistic_values () {
      this.metrics.map(this.request_metric_value)
    },
    async request_metric_value (metric) {
      let request_metric = metric.replace(/_/i, '')
      await this.$store.dispatch('get_statistic_metric', request_metric)
    },
    logout () {
      this.$store.commit('set_user', {})
      this.$store.commit('update_statistics', [])
      this.$store.commit('update_token', '')
      this.$store.commit('update_webapps', [])
      this.$store.commit('set_is_authenticated', '')
      this.$router.push({ name: 'Home' })
    },
    openAdmin () {
      window.location.href = 'https://cluster.datexis.com/admin/'
    }
  },
  computed: {
    userIsAdmin () {
      let current_user = this.$store.getters['get_current_user']
      return current_user['role'] === 'admin'
    }
  },
  created () {
    if(this.$store.getters['get_is_authenticated'] === '') {
      this.$router.push({ name: 'Home' })
    } else if (this.$store.getters['get_is_authenticated'] === true) {
      this.get_all_statistic_values()
    }
  }
}
</script>

<style scoped lang="scss">
  .icon {
    position: absolute;
    left: 15px;
    color: floralwhite;
  }
  .sidenav {
    height: 100vh;
    position: absolute;
    left: -2px;
    top: -2px;
    min-width: 100px;
  }
  .title {
    padding: 0 1rem 0 3rem;
  }

</style>
