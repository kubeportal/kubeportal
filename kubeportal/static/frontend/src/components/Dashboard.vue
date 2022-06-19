<template>
  <v-img content-class="vertical-img" src="../assets/mountain.jpeg">
    <v-tabs
      :vertical="desktop"
      class="sidenav"
      background-color="rgba(0, 0, 0, .5)"
      dark
      active-class="activeTab"
      show-arrows
      icons-and-text
    >
    <div v-if="desktop">
      <div class="logo text-center" @click="go_to_dashboard">
        <div class="d-inline-flex flex-wrap justify-center mt-4">
          <v-icon class="vertical-icon mr-4">mdi-view-dashboard-variant</v-icon>
          <div class="title">
            <small>{{ cluster_branding }}</small>
          </div>
        </div>
      </div>
      <v-container>
        <hr />
      </v-container>
    </div>
      <v-tab v-for="tab in filtered_tabs" :key="tab.name" class="tab">
        {{ tab.name }}
        <v-icon class="vertical-icon">{{ tab.icon }}</v-icon>
      </v-tab>
      <v-tab-item
        v-for="(tab, index) in filtered_tabs"
        :key="tab.name + index"
        class="items"
      >
        <TopBar :title="tab.name"/>
        <div class="p-1">
          <v-card-text> current namespace: {{ namespace }}</v-card-text>
          <component :is="tab.component"/>
        </div>
      </v-tab-item>
    </v-tabs>
  </v-img>
</template>

<script>
import TopBar from './TopBar'
export default {
  name: 'Dashboard',
  components: { TopBar },
  data () {
    return {
      width: window.outerWidth
    }
  },
  methods: {
    go_to_dashboard () {
      if (this.$route.name !== 'Kubeportal') {
        this.$router.push({ name: 'Kubeportal' })
      }
    },
    resize (e) {
      this.width = e.currentTarget.outerWidth
    }
  },
  props: ['tabs'],
  computed: {
    filtered_tabs () {
      return this.tabs.filter(tab => tab.has_access)
    },
    cluster_branding () {
      return this.$store.getters['api/get_branding']
    },
    desktop () {
      return this.width > 900
    },
    namespace () {
      return this.$store.getters['users/get_current_namespace']
    }
  },
  created () {
    this.$vuetify.theme.dark = this.$store.getters['users/get_dark_mode']
    window.addEventListener('resize', this.resize)
  },
  destroyed () {
    window.removeEventListener('resize', this.resize)
  }
}
</script>

<style lang="scss">
.p-1 {
  padding: 1em;
}

.vertical-icon {
  color: floralwhite;
}
.top-icon {
  width: 14px;
}

.sidenav {
  height: 100vh;
  left: -2px;
  top: -2px;
}

.activeTab {
  background: linear-gradient(to top right, #b3b3b3, #4d4d4d);
}
.tab {
  width: 15em;
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
.vertical-img {
  width: 100%;
  height: 100%;
}
.v-window.v-item-group.theme--light.v-tabs-items {
  background-color: rgba(0, 0, 0, 0);
}

.v-tooltip__content p {
  font-size: 1.2rem !important;
}

.v-tooltip__content .tooltip {
  margin: 2rem 1rem 2rem 1rem;
}

.v-tooltip__content h3 {
  font-size: 1.2rem !important;
  font-weight: bolder;
}
.v-tooltip__content hr {
  width: 75%;
  margin: 1rem 0 1rem 0;
}
</style>
