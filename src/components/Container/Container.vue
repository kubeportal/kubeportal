<template>
  <v-card>
    <v-card-text> current namespace: {{ namespace }} </v-card-text>
    <div>
      <v-tabs fixed-tabs>
        <v-tab>
          <v-icon>mdi-desktop-classic</v-icon>
          Pods
        </v-tab>
        <v-tab>
          <v-icon>mdi-hexagon-multiple-outline</v-icon>
          Deployments
        </v-tab>

        <v-tab-item>
           <div>
            <v-btn color="green" icon @click="pod_overlay = true" x-large disabled>
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </div>
          <v-data-table
            :headers="pods_headers"
            :items="pods_data"
            :items-per-page="15"
            class="elevation-1"
            :search="search_pods"
          >
            <template v-slot:top>
              <v-text-field
                v-model="search_pods"
                label="Search"
                class="mx-4"
              ></v-text-field>
            </template>
          </v-data-table>
        </v-tab-item>
        <v-tab-item>
          <div>
            <v-btn color="green" icon @click="deployment_overlay = true" x-large disabled>
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
            <DeploymentModal
              @close="deployment_overlay = false"
              :overlay="deployment_overlay"
              :namespace="namespace"
            />
          </div>
          <v-data-table
            :headers="deployment_headers"
            :items="deployments_data"
            :items-per-page="15"
            class="elevation-1"
            :search="search_deployments"
          >
            <template v-slot:top>
              <v-text-field
                v-model="search_deployments"
                label="Search"
                class="mx-4"
              ></v-text-field>
            </template>
          </v-data-table>
        </v-tab-item>
      </v-tabs>
    </div>
  </v-card>
</template>

<script>
import TopBar from '@/components/TopBar'
import DeploymentModal from './DeploymentModal'

export default {
  name: 'Container',
  components: { TopBar, DeploymentModal },
  computed: {
    namespace () {
      return this.$store.getters['users/get_user']['namespace_names'].join(', ')
    },
    pods_data () {
      return this.$store.getters['pods/get_pods']
    },
    deployments_data () {
      return this.$store.getters['deployments/get_deployments']
    }
  },
  data () {
    return {
      deployment_overlay: false,
      pod_overlay: false,
      search_pods: '',
      search_deployments: '',
      pods_headers: [
        {
          text: 'Name',
          algin: 'start',
          sortable: false,
          value: 'name'
        },
        {
          text: 'Created at',
          value: 'creation_timestamp'
        },
        {
          text: 'Container',
          value: 'containers'
        },
        {
          text: 'Image',
          value: 'images'
        }
      ],
      deployment_headers: [
        {
          text: 'Name',
          algin: 'start',
          sortable: false,
          value: 'name'
        },
        {
          text: 'Created at',
          value: 'creation_timestamp'
        },
        {
          text: 'Replicas',
          value: 'replicas'
        }
      ]
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

<style>
</style>
