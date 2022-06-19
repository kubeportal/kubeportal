<template>
  <v-card>
   <Dashboard :tabs="tabs"/>
  </v-card>
</template>

<script>
import Welcome from '@/components/Welcome/Welcome'
import Container from '@/components/Container/Container'
import Storage from '@/components/Storage/Storage'
import Network from '@/components/Network/Network'
import RequestAccess from '@/components/RequestAccess/RequestAccess'
import Wizard from '@/components/Wizard/Wizard'
import Dashboard from '@/components/Dashboard'

export default {
  name: 'App',

  components: { Welcome, Container, Storage, Network, RequestAccess, Wizard, Dashboard },
  computed: {
    user_state () {
      return this.$store.getters['users/get_user']['state']
    },
    tabs () {
      return [
        {
          icon: 'mdi-home-heart',
          name: 'Welcome',
          has_access: true,
          component: Welcome
        }, {
          icon: 'mdi-key',
          name: 'Request Access',
          has_access: this.user_state !== 'ACCESS_APPROVED',
          component: RequestAccess
        }, {
          icon: 'mdi-package',
          name: 'Container',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: Container
        }, {
          icon: 'mdi-database',
          name: 'Storage',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: Storage
        }, {
          icon: 'mdi-lan',
          name: 'Network',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: Network
        }, {
          icon: 'mdi-wizard-hat',
          name: 'Wizard',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: Wizard
        }
      ]
    }
  },
  created () {
    this.$vuetify.theme.dark = this.$store.getters['users/get_dark_mode']
  }
}
</script>
