<template>
  <div>
    <DeploymentModal
      @close="deployment_overlay = false"
      :overlay="deployment_overlay"
      :namespace="namespace"
    />
    <v-data-table
      :headers="deployment_headers"
      :items="deployments_data"
      :items-per-page="10"
      class="elevation-1"
      :search="search_deployments"
      :sort-by.sync="sortBy"
    >
      <template v-slot:top>
        <v-row>
          <v-col md="1">
            <v-btn
              color="green"
              icon
              @click="deployment_overlay = true"
              x-large
            >
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </v-col>
          <v-col md="1">
            <v-btn
              icon
              @click="refresh_deployments"
              x-large
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-col>
          <v-col md="10">
            <v-text-field
              v-model="search_deployments"
              label="Search"
              class="mx-4"
            ></v-text-field>
          </v-col>
        </v-row>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import DeploymentModal from './DeploymentModal'
export default {
  name: 'DeploymentTable',
  components: { DeploymentModal },
  props: ['deployments_data', 'namespace'],
  data () {
    return {
      sortBy: 'name',
      deployment_overlay: false,
      search_deployments: '',
      deployment_headers: [
        {
          text: 'Name',
          algin: 'start',
          value: 'name'
        },
        {
          text: 'Replicas',
          value: 'replicas'
        },
        {
          text: 'Created',
          value: 'creation_timestamp'
        }
      ]
    }
  },
  methods: {
    refresh_deployments () {
      this.$store.dispatch('deployments/request_deployments')
    }
  }
}

</script>

<style>

</style>
