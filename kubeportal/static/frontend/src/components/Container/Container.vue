<template>
  <div>
    <PodDetails @close_details="close_details" v-if="is_show_details" :pod="pod" :namespace="namespace"/>
    <v-tabs fixed-tabs v-if="!is_show_details">
      <v-tab>
        <v-icon class="mr-2">mdi-desktop-classic</v-icon>
        Pods
      </v-tab>
      <v-tab>
        <v-icon class="mr-2">mdi-hexagon-multiple-outline</v-icon>
        Deployments
      </v-tab>

      <v-tab-item>
        <PodTable @show_details="show_details" :pods_data="pods_data" :namespace="namespace"/>
      </v-tab-item>
      <v-tab-item>
        <DeploymentTable :deployments_data="deployments_data" :namespace="namespace" />
      </v-tab-item>
    </v-tabs>
  </div>
</template>

<script>
import TopBar from '@/components/TopBar'
import DeploymentModal from './DeploymentModal'
import DeploymentTable from './DeploymentTable'
import PodModal from './PodModal'
import PodTable from './PodTable'
import PodDetails from './PodDetails'

export default {
  name: 'Container',
  components: { TopBar, DeploymentModal, DeploymentTable, PodModal, PodTable, PodDetails },
  data () {
    return {
      is_show_details: false,
      pod: {}
    }
  },
  computed: {
    namespace () {
      return this.$store.getters['users/get_current_namespace']
    },
    pods_data () {
      return this.$store.getters['pods/get_pods']
    },
    deployments_data () {
      return this.$store.getters['deployments/get_deployments']
    }
  },
  methods: {
    show_details (pod) {
      this.is_show_details = true
      this.pod = pod
    },
    close_details () {
      this.is_show_details = false
    }
  },
  mounted () {
    if (this.pods_data.length === 0) {
      this.$store.dispatch('pods/request_pods')
    }
    if (this.deployments_data.length === 0) {
      this.$store.dispatch('deployments/request_deployments')
    }
  }
}
</script>

<style scoped>
</style>
