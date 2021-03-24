<template>
  <v-card>
    <Dashboard :tabs="tabs" />
  </v-card>
</template>

<script>
import Dashboard from '@/components/Dashboard'
import Info from '@/components/Settings/Info/Info'
import KubernetesSettings from '@/components/Settings/KubernetesSettings/KubernetesSettings'
import Profile from '@/components/Settings/Profile/Profile'

export default {
  name: 'Settings',
  components: { Dashboard },
  computed: {
    user_state () {
      return this.$store.getters['users/get_user']['state']
    },
    tabs () {
      return [
        {
          icon: 'mdi-account-details',
          name: 'User',
          has_access: true,
          component: Profile
        }, {
          icon: 'mdi-kubernetes',
          name: 'Kubernetes',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: KubernetesSettings
        }, {
          icon: 'mdi-information-outline',
          name: 'Infos',
          has_access: this.user_state === 'ACCESS_APPROVED',
          component: Info
        }
      ]
    }
  }
}
</script>
