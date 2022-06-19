<template>
  <div>
    <v-card >
      <v-card-title>
        Cluster Details
      </v-card-title>
      <RequestSpinner v-if="all_statistics.length === 0" />
      <div >
        <v-simple-table fixed-header>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="first text-left">Name</th>
                <th class="second text-left">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in all_statistics" :key="index">
                <td>{{ Object.keys(item)[0] }}</td>
                <td>
                    {{ Object.values(item)[0] }}
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </div>
    </v-card>
    <v-card>
      <v-card-title>
        <a href="https://github.com/kubeportal/kubeportal"><v-icon>mdi-github</v-icon> Kubeportal</a>
      </v-card-title>
    </v-card>
  </div>
</template>

<script>
import RequestSpinner from '@/components/RequestSpinner'
import TopBar from '@/components/TopBar'

export default {
  name: 'Info',
  components: { RequestSpinner, TopBar },
  computed: {
    all_statistics () {
      return this.$store.getters['infos/get_cluster_info']
    }
  },
  methods: {
    request_cluster_infos () {
      if (this.all_statistics.length === 0) {
        this.$store.dispatch('infos/request_cluster_infos')
      }
    }
  },
  mounted () {
    this.request_cluster_infos()
  }
}
</script>

<style scoped lang="scss">
  a{
    text-decoration: none;
  }
  .first {
    width: 30rem;
  }
  .wrapper {
    height: 70vh !important;
  }
</style>
