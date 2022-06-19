<template>
  <div>
    <v-tabs fixed-tabs>
      <v-tab>
        <v-icon class="mr-2">mdi-desktop-classic</v-icon>
        PVC
      </v-tab>
      <v-tab-item>

        <PVCModal
          @close="overlay = false"
          :overlay="overlay"
          :namespace="namespace"
        />
        <v-data-table
          :headers="pvc_headers"
          :items="pvcs_data"
          :items-per-page="10"
          class="elevation-1"
          :search="search_pvc"
          :sort-by.sync="sortBy"
        >
          <template v-slot:top>
            <v-row>
              <v-col md="1">
                <v-btn color="green" icon x-large @click="overlay = true">
                  <v-icon>mdi-plus-circle</v-icon>
                </v-btn>
              </v-col>
              <v-col md="1">
                <v-btn
                  icon
                  @click="refresh_pvc"
                  x-large
                >
                  <v-icon>mdi-refresh</v-icon>
                </v-btn>
              </v-col>
              <v-col md="10">
                <v-text-field
                  v-model="search_pvc"
                  label="Search"
                  class="mx-4"
                ></v-text-field>
              </v-col>
            </v-row>
          </template>
        </v-data-table>
      </v-tab-item>
    </v-tabs>
  </div>
</template>

<script>
import PVCModal from './PVCModal'

export default {
  name: 'Storage',
  components: { PVCModal },
  data () {
    return {
      sortBy: 'name',
      overlay: false,
      search_pvc: '',
      pvc_headers: [
        {
          text: 'Name',
          algin: 'start',
          value: 'name'
        },
        {
          text: 'Access Mode',
          value: 'access_mode'
        },
        {
          text: 'Phase',
          value: 'phase'
        },
        {
          text: 'Size',
          value: 'size'
        },
        {
          text: 'Created',
          value: 'creation_timestamp'
        }
      ]
    }
  },
  computed: {
    namespace () {
      return this.$store.getters['users/get_current_namespace']
    },
    pvcs_data () {
      return this.$store.getters['pvcs/get_persistentvolumeclaims']
    }
  },
  methods: {
    refresh_pvc () {
      this.$store.dispatch('pvcs/request_persistentvolumeclaims')
    }
  },
  mounted () {
    if (this.pvcs_data.length === 0) {
      this.$store.dispatch('pvcs/request_persistentvolumeclaims')
    }
  }
}
</script>

<style>
</style>
