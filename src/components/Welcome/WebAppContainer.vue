<template>
  <div>
    <RequestSpinner v-if="webapps.length === 0" />
    <div class="my-4" v-else>
      <v-row class="p-3">
        <v-hover v-for="app in webapps" :key="app.index" v-slot="{ hover }">
          <v-col lg="3">
            <div class="app" :class="{ 'on-hover': hover }" @click="open_link(app.link_url)">
              <v-card class="app-icon" :elevation="hover ? 12 : 2">
                <v-card-text class="app-icon-text">
                  <v-icon large color="white">{{app_icon(app['category'])}}</v-icon>
                </v-card-text>
              </v-card>
              <v-card class="app-text" :class="app.color" :elevation="hover ? 12 : 2">
                <v-card-text  :value="app.color" class="text-md-h5 white--text">
                  {{ app.link_name }}
                  <!-- {{ app.link_url }} -->
                </v-card-text>
              </v-card>
            </div>
          </v-col>
        </v-hover>
      </v-row>
    </div>
  </div>
</template>

<script>
import RequestSpinner from '@/components/RequestSpinner'

export default {
  name: 'WebAppContainer',
  components: { RequestSpinner },
  data () {
    return {
      classes: ['blue', 'yellowgreen', 'green']
    }
  },
  computed: {
    webapps () {
      return this.modify_webapps(this.$store.getters['users/get_webapps'])
    }
  },
  methods: {
    modify_webapps (webapps) {
      webapps.forEach((webapp, index) => {
        webapp['color'] = this.$data.classes[index % 3]
      })
      return webapps
    },
    open_link (link) {
      window.open(link, '_blank')
    },
    app_icon (category) {
      switch (category) {
        case 'GENERIC': return 'mdi-view-quilt'
        case 'DOCUMENTATION': return 'mdi-text-box-multiple'
        case 'COMMUNICATION': return 'mdi-comment-account'
        case 'KUBERNETES': return 'mdi-kubernetes'
        case 'DEVELOPER': return 'mdi-developer-board'
        case 'DATABASE': return 'mdi-database'
        case 'MONITORING': return 'mdi-monitor-share'
      }
    }
  }
}
</script>

<style scoped lang="scss">

.app {
  width: 20vw;
  height: 12vh;
  position: relative;
  text-align: center;
  padding: 1vh;
}

.app-icon {
  position: absolute;
  background-color: green;
  z-index: 1;
  left: 5%;
  bottom: 70%;
}

.app-icon-text{
  padding: 5px;
}

.app-text{
  display: flex;
  justify-content: center;
  align-items: center;
  height: 4rem;
  border-radius: 40px;
  min-width: 100px;
}

.v-card.on-hover.theme--dark{
  background-color: rgba(#FFF, 0.8);
  .v-card__text{
    color: #000
  }
}

.blue {
  background: dodgerblue linear-gradient(to bottom left,  #b3d9ff, #004d99);
}

.yellowgreen {
  background: yellowgreen linear-gradient(to bottom left, #e6e600, #808000);
}

.green {
  background: green linear-gradient(to bottom left,  #99ffbb, #009933);
}
</style>
