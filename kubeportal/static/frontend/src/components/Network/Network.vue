<template>
  <v-card>
    <v-card-text>
        current namespace: {{ namespace }}
    </v-card-text>
    <div>
      <v-tabs fixed-tabs>
        <v-tab>
          <v-icon>mdi-transit-connection</v-icon>
          Services
        </v-tab>
        <v-tab>
          <v-icon>mdi-lan-pending</v-icon>
          Ingresses
        </v-tab>

        <v-tab-item>
          <div>
            <v-btn color="green" icon @click="service_overlay = true" x-large disabled>
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
            <ServiceModal @close="service_overlay = false" :overlay="service_overlay" :namespace="namespace" />
          </div>
          <v-data-table
            :headers="services_headers"
            :items="services_data"
            :items-per-page="5"
            class="elevation-1"
            :search="search_services"
          >
            <template v-slot:top>
              <v-text-field
                v-model="search_services"
                label="Search"
                class="mx-4"
              ></v-text-field>
            </template>
          </v-data-table>
        </v-tab-item>
        <v-tab-item>
          <div>
            <v-btn color="green" icon @click="ingress_overlay = true" x-large disabled>
              <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </div>
        <v-data-table
            :headers="ingresses_headers"
            :items="ingresses_data"
            :items-per-page="5"
            class="elevation-1"
            :search="search_ingresses"
          >
          <template v-slot:item="props">
            <tr>
              <td><span class='host' v-html=props.item.host_links /></td>
              <td>
                <v-icon v-if='props.item.status === 200' style="color: #689F38" class="icon ">mdi-checkbox-blank-circle</v-icon>
                <v-icon v-else class="icon" style="color: #a10000" >mdi-checkbox-blank-circle</v-icon>
              </td>
              <td>{{props.item.name}}</td>
              <td> <span v-html=props.item.annotations /></td>
              <td>{{props.item.tls}}</td>
              <td><span v-html=props.item.services /></td>
              <td><span v-html=props.item.creation_timestamp /></td>
            </tr>
          </template>
            <template v-slot:top>
              <v-text-field
                v-model="search_ingresses"
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
import ServiceModal from './ServiceModal'
import IngressModal from './IngressModal'

export default {
  name: 'Network',
  components: { TopBar, ServiceModal, IngressModal },
  computed: {
    namespace () {
      return this.$store.getters['users/get_user']['namespace_names'].join(', ')
    },
    services_data () {
      return this.$store.getters['services/get_services']
    },
    ingresses_data () {
      return this.$store.getters['ingresses/get_ingresses']
    }
  },
  data () {
    return {
      service_overlay: false,
      ingress_overlay: false,
      search_services: '',
      search_ingresses: '',
      services_headers: [
        {
          text: 'Name',
          algin: 'start',
          sortable: true,
          value: 'name'
        },
        {
          text: 'Type',
          value: 'type'
        },
        {
          text: 'Selector',
          value: 'selector'
        },
        {
          text: 'Ports',
          value: 'ports'
        }
      ],
      ingresses_headers: [
        {
          text: 'Hosts',
          value: 'host_links',
          algin: 'start',
          sortable: true
        },
        {
          text: 'Status',
          value: 'status'
        },
        {
          text: 'Name',
          value: 'name'
        },
        {
          text: 'Annotations',
          value: 'annotations'
        },
        {
          text: 'TLS',
          value: 'tls'
        },
        {
          text: 'Service',
          value: 'services'
        },
        {
          text: 'Created at',
          value: 'creation_timestamp'
        }
      ]
    }
  },
  mounted () {
    if (this.services_data.length === 0) {
      this.$store.dispatch('services/request_services')
    }
    if (this.ingresses_data.length === 0) {
      this.$store.dispatch('ingresses/request_ingresses')
    }
  },

  methods: {
  }
}
</script>

<style scoped>
.host a {
  font-size: larger;
}
</style>
