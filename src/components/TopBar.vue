<template>
  <v-toolbar flat class="topBar">
    <v-toolbar-title>{{title}}</v-toolbar-title>
    <v-spacer/>
    <div class="text-center">
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            color="primary"
            dark
            v-bind="attrs"
            v-on="on"
            icon
          >
            <v-icon>mdi-account</v-icon>
          </v-btn>
        </template>

        <v-list flat>
          <v-subheader>Signed in as: {{current_user['username']}}</v-subheader>

          <v-list-item @click="push_route('Kubeportal')" class="listItem">
              <v-list-item-icon>
                <v-icon>mdi-view-dashboard-variant</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <!-- <v-switch></v-switch> -->
                <v-list-item-title>Dashboard</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item @click="push_route('Settings')" class="listItem">
              <v-list-item-icon>
                <v-icon>mdi-account</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>Settings</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item @click="switch_dark_mode" class="listItem">
              <v-list-item-icon>
                <v-icon>mdi-brightness-6</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <!-- <v-switch></v-switch> -->
                <v-list-item-title>Darkmode</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item  v-if="current_user['admin']" @click="open_admin" class="listItem">
              <v-list-item-icon>
                <v-icon>mdi-tools</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>Admin</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

            <v-list-item @click="logout" class="listItem">
              <v-list-item-icon>
                <v-icon>mdi-logout-variant</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>Logout</v-list-item-title>
              </v-list-item-content>
            </v-list-item>

        </v-list>
      </v-menu>
    </div>
  </v-toolbar>
</template>

<script>
export default {
  name: 'TopBar',
  props: ['title'],
  computed: {
    current_user () {
      return this.$store.getters['users/get_user']
    }
  },
  methods: {
    async switch_dark_mode () {
      this.$vuetify.theme.dark = await this.$store.dispatch('users/switch_dark_mode')
    },
    logout () {
      this.$store.dispatch('users/log_out')
      this.$store.commit('users/set_user', {})
      this.$store.commit('users/set_webapps', [])
      this.$store.commit('pods/set_pods', [])
      this.$store.commit('deployments/set_deployments', [])
      this.$store.commit('services/set_services', [])
      this.$store.commit('ingresses/set_ingresses', [])
      this.$store.commit('pvcs/set_persistentvolumeclaims', [])
      this.$store.commit('infos/set_cluster_info', [])
      this.$store.commit('api/set_csrf_token', '')
      this.$store.commit('users/set_access_token', '')
      this.$router.push({ name: 'Home' })
    },
    open_admin () {
      window.open(`${process.env['VUE_APP_BASE_URL']}/admin/`, '_blank')
    },
    push_route (name) {
      if (this.$route.name !== name) {
        this.$router.push({ name: name })
      }
    }
  }
}
</script>

<style scoped>
  .topBar {
    max-width: 100vw;
  }

  .listItem {
    margin-right: 1em;
  }

</style>
