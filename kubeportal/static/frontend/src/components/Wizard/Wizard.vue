<template>
  <div>
    <v-stepper v-model="e1">
      <v-stepper-header>
        <v-stepper-step step="1" :complete="e1 > 1">
          Deployment
        </v-stepper-step>

        <v-divider></v-divider>

        <v-stepper-step step="2" :complete="e1 > 2"> Service </v-stepper-step>

        <v-divider></v-divider>

        <v-stepper-step step="3"> Ingress </v-stepper-step>
      </v-stepper-header>

      <v-stepper-items>
        <v-stepper-content step="1">
          <v-card>
            <Deployment />
          </v-card>
          <v-row>
            <v-spacer />
            <v-col md="1">
              <v-btn text color="primary" @click="e1 = 2"> next </v-btn>
            </v-col>
          </v-row>
        </v-stepper-content>

        <v-stepper-content step="2">
          <v-card>
            <Service />
          </v-card>

          <v-row>
            <v-spacer />
            <v-col md="1">
              <v-btn text color="primary" @click="e1 = 1"> back </v-btn>
            </v-col>

            <v-col md="1">
              <v-btn text color="primary" @click="e1 = 3"> next </v-btn>
            </v-col>
          </v-row>
        </v-stepper-content>

        <v-stepper-content step="3">
          <v-card>
            <Ingress />
          </v-card>

          <v-row>
            <v-spacer />
            <v-col md="1">
              <v-btn text color="primary" @click="e1 = 2"> back </v-btn>
            </v-col>

            <v-col md="2">
              <v-btn text color="primary" @click="deploy" disabled> deploy </v-btn>
            </v-col>
          </v-row>
        </v-stepper-content>
      </v-stepper-items>
    </v-stepper>
  </div>
</template>

<script>
import Deployment from '@/components/Wizard/Deployment'
import Service from '@/components/Wizard/Service'
import Ingress from '@/components/Wizard/Ingress'
import EventBus from '@/utils/eventbus.js'
export default {
  name: 'Wizard',
  components: { Deployment, Service, Ingress, EventBus },
  data () {
    return {
      e1: 1,
      tab: this.$store.getters['wizard/get_current_wizard_tab']
    }
  },
  methods: {
    deploy () {
      console.log('deployed')
    },
    SaveDataByOpenDeployment () {
      if (this.tab === 'Service') {
        EventBus.$emit('SaveServiceData')
      } else if (this.tab === 'Ingress') {
        EventBus.$emit('SaveIngressData')
      }
      this.$store.commit('set_current_wizard_tab', 'Deployment')
    },
    SaveDataByOpenService () {
      if (this.tab === 'Deployment') {
        EventBus.$emit('SaveDeploymentData')
      } else if (this.tab === 'Ingress') {
        EventBus.$emit('SaveIngressData')
      }
      this.$store.commit('set_current_wizard_tab', 'Service')
    },
    SaveDataByOpenIngress () {
      if (this.tab === 'Service') {
        EventBus.$emit('SaveServiceData')
      } else if (this.tab === 'Deployment') {
        EventBus.$emit('SaveDeploymentData')
      }
      this.$store.commit('set_current_wizard_tab', 'Ingress')
    }
  }
}
</script>

<style>
</style>
