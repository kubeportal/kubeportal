<template>
  <div>
    <PodModal
      @close="pod_overlay = false"
      :overlay="pod_overlay"
      :namespace="namespace"
    />
    <v-data-table
      :headers="pods_headers"
      :items="pods_data"
      :items-per-page="10"
      class="elevation-1"
      :search="search_pods"
      :sort-by.sync="sortBy"
    >
      <template v-slot:item="props">
        <tr @click="show_details(props.item)" class="tableRow">
          <td>{{ props.item.name }}</td>
          <td>
            <div v-for="image in props.item.images" :key="image">
              {{ image }}
            </div>
          </td>
          <td>
            <div
              v-for="container in props.item.containers"
              :key="container"
            >
              {{ container }}
            </div>
          </td>
          <td>{{ props.item.phase }}</td>
          <td>{{ props.item.creation_timestamp }}</td>
        </tr>
      </template>
      <template v-slot:top>
        <v-row>
          <v-col md="1">
            <v-btn
              color="green"
              icon
              @click="pod_overlay = true"
              x-large
            >
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </v-col>
          <v-col md="1">
            <v-btn
              icon
              @click="refresh_pods"
              x-large
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-col>
          <v-col md="10">
            <v-text-field
              v-model="search_pods"
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
import PodModal from './PodModal'
export default {
  name: 'PodTable',
  props: ['pods_data', 'namespace'],
  components: { PodModal },
  data () {
    return {
      sortBy: 'name',
      pod_overlay: false,
      search_pods: '',
      pods_headers: [
        {
          text: 'Name',
          algin: 'start',
          value: 'name'
        },
        {
          text: 'Image',
          value: 'images'
        },
        {
          text: 'Container',
          value: 'containers'
        },
        {
          text: 'Phase',
          value: 'phase'
        },
        {
          text: 'Created',
          value: 'creation_timestamp'
        }
      ]
    }
  },
  methods: {
    refresh_pods () {
      this.$store.dispatch('pods/request_pods')
    },
    show_details (pod) {
      this.$emit('show_details', pod)
    }
  }
}
</script>

<style scoped>
.tableRow {
  cursor: pointer;
}

</style>
