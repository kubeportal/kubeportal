<template>
  <b-card class="maincard">
    <v-tabs >
      <v-tab @click="SaveDataByOpenDeployment">
        <v-icon class="icon" left>mdi-hexagon-multiple-outline</v-icon>
          <div class="title"><small>Deployment</small></div>
      </v-tab>
      <v-tab @click="SaveDataByOpenService">
        <v-icon class="icon" left>mdi-transit-connection-horizontal</v-icon>
          <div class="title"><small>Service</small></div>
      </v-tab>
      <v-tab @click="SaveDataByOpenIngress">
        <v-icon class="icon" left>mdi-arrow-decision-outline</v-icon>
          <div class="title"><small>Ingress</small></div>
      </v-tab>

      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Deployment ref="Deployment" />
          </v-card-text>
        </v-card>
      </v-tab-item>
      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Service ref="Service" />
          </v-card-text>
        </v-card>
      </v-tab-item>
      <v-tab-item class="items">
        <v-card flat>
          <v-card-text>
            <Ingress ref="Ingress" />
          </v-card-text>
        </v-card>
      </v-tab-item>
    </v-tabs>
  </b-card>
</template>

<script>
import Deployment from './Deployment'
import Service from './Service'
import Ingress from './Ingress'
import EventBus from '../../plugins/eventbus.js'

export default {
  name: 'Generator',
  components: { Deployment, Service, Ingress, EventBus },
  data () {
    return {
      tab: this.$store.getters['get_current_generator_tab']
    }
  },
  methods: {
    SaveDataByOpenDeployment () {
      if(this.tab === 'Service') {
        EventBus.$emit('SaveServiceData')
      } else if (this.tab === 'Ingress') {
        EventBus.$emit('SaveIngressData')
      }
      this.$store.commit('set_current_generator_tab', 'Deployment')
    },
    SaveDataByOpenService () {
      if(this.tab === 'Deployment') {
        EventBus.$emit('SaveDeploymentData')
      } else if (this.tab === 'Ingress') {
        EventBus.$emit('SaveIngressData')
      }
      this.$store.commit('set_current_generator_tab', 'Service')
    },
    SaveDataByOpenIngress () {
      if(this.tab === 'Service') {
        EventBus.$emit('SaveServiceData')
      } else if (this.tab === 'Deployment') {
        EventBus.$emit('SaveDeploymentData')
      }
      this.$store.commit('set_current_generator_tab', 'Ingress')
    }
  }
}
</script>

<style scoped lang="scss">

</style>
