<template>
  <v-card>
    <v-tabs vertical class="sidenav" dark active-class="activeTab">
      <v-img class="img"
        src="../assets/mountain.jpeg"
        gradient="to bottom left, rgba(18,18,18, .8), rgba(18, 18, 18, .3)">
        <div class="logo text-center" @click="go_to_dashboard">
          <v-row align="center" >
            <v-col>
              <v-icon class="icon">mdi-view-dashboard-variant</v-icon>
            </v-col>
            <v-col>
              <div class="title"><small>{{cluster_branding}}</small></div>
            </v-col>
          </v-row>
        </div>
        <v-container>
          <hr />
        </v-container>
        <v-tab v-for="tab in filtered_tabs" :key="tab.name">
          <v-row>
            <v-col sm="4">
              <v-icon class="icon">{{ tab.icon }}</v-icon>
            </v-col>
            <v-col sm="6">
              <div class="title">
                <small>{{ tab.name }}</small>
              </div>
            </v-col>
          </v-row>
        </v-tab>
      </v-img>
        <v-tab-item
          v-for="(tab, index) in filtered_tabs"
          :key="tab.name + index"
          class="items">
          <Node :tab="tab" />
        </v-tab-item>
    </v-tabs>
  </v-card>
</template>

<script>
import { showAt } from 'vue-breakpoints'
import Node from './Node'

export default {
  name: 'Dashboard',
  methods: {
    go_to_dashboard () {
      if (this.$route.name !== 'Kubeportal') {
        this.$router.push({ name: 'Kubeportal' })
      }
    }
  },
  components: { showAt, Node },
  props: ['tabs'],
  computed: {
    filtered_tabs () {
      return this.tabs.filter((tab) => tab.has_access)
    },
    cluster_branding () {
      return this.$store.getters['api/get_branding']
    }
  },
  created () {
    this.$vuetify.theme.dark = this.$store.getters['users/get_dark_mode']
  }
}
</script>

<style scoped lang="scss">
.icon {
  color: floralwhite;
}
.sidenav {
  height: 100vh;
  position: absolute;
  left: -2px;
  top: -2px;
  overflow: auto;
}

.activeTab {
  background: linear-gradient(to top right, #b3b3b3, #4d4d4d)
}

.logo {
  padding-top: 0.25em;
  width: 85%;
  margin: 0 auto;
  cursor: pointer;
}

hr {
  background-color: rgba(240, 240, 240, 0.5);
}

.title {
  color: floralwhite;
  text-align: center;
}
.items {
  max-height: 100vh;
}
.img {
  width: 12vw;
  height: 100vh;
  min-width: 200px;
}
</style>
