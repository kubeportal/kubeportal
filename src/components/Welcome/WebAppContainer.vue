<template>
  <div>
      <hide-at :breakpoints="{small: 600, medium: 800, large: 1200}"  breakpoint="small">
      <RequestSpinner v-if="webapps.length === 0" />
      <div class="mt-5 d-inline-flex justify-lg-center justify-md-center justify-sm-center flex-wrap" v-else>
        <div v-for="app in webapps" :key="app.index">
          <v-hover v-slot="{ hover }" >
            <div class="app mr-7" @click="open_link(app.link_url)">
              <v-icon class="app-icon" large color="white">{{app_icon(app['category'])}}</v-icon>
              <v-card class="app-card pr-4 pl-7" :class="app.color" :elevation="hover ? 12 : 2">
                <v-card-text class="app-text white--text text-lg-button text-md-body-1 text-sm-body-1" :value="app.color">
                  {{ app.link_name }}
                </v-card-text>
              </v-card>
            </div>
          </v-hover>
        </div>
      </div>
      </hide-at>
      <show-at :breakpoints="{small: 600, medium: 800, large: 1200}"  breakpoint="small">
        <RequestSpinner v-if="webapps.length === 0" />
        <div class="my-2 pr-2 d-block justify-space-around" v-else>
        <div v-for="app in webapps" :key="app.index" >
          <div class="mobile-app" @click="open_link(app.link_url)">
            <v-icon class="mobile-app-icon" color="white">{{app_icon(app['category'])}}</v-icon>
            <v-card class="mobile-app-card mr-auto ml-auto mt-2" :class="app.color" :elevation="hover ? 12 : 2">
              <v-card-text class="mobile-app-text white--text" :value="app.color">
                {{ app.link_name }}
              </v-card-text>
            </v-card>
           </div>
          </div>
        </div>
      </show-at>
  </div>
</template>

<script>
import RequestSpinner from '@/components/RequestSpinner'
import { showAt, hideAt } from 'vue-breakpoints'

export default {
  name: 'WebAppContainer',
  components: { showAt, hideAt, RequestSpinner },
  data () {
    return {
      classes: ['blue', 'orange', 'yellowgreen', 'green'],
      hover: false
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
        webapp['color'] = this.$data.classes[index % 4]
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

.app, .mobile-app{
  width: 22vw;
  height: 8rem;
  position: relative;
  text-align: center;
  padding: 1vh;
}
.mobile-app {
  width: 100%;
  height: auto;
  display: block;
}
.app-icon {
  position: absolute;
  background-color: green;
  z-index: 1;
  left: 5%;
  bottom: 70%;
  height: 45px;
  width: 45px
}
.mobile-app-icon {
  position: absolute;
  background-color: green;
  z-index: 1;
  left: 6%;
  bottom: 60%;
  height: 40px;
  width: 40px
}
.app-card, .mobile-app-card {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 4.5rem;
  border-radius: 35px;
  min-width: 170px;
}
.mobile-app-card {
  width: 90%;
}

.mobile-app-text {
  font-size: 1.5rem;
}

.orange {
  background: linear-gradient(to bottom left, #f5c842, #755904);
}

.blue {
  background: linear-gradient(to bottom left,  #b3d9ff, #004d99);
}

.yellowgreen {
  background: linear-gradient(to bottom left, #e6e600, #808000);
}

.green {
  background: linear-gradient(to bottom left,  #99ffbb, #009933);
}
</style>
