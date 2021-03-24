<template>
  <div class="m-4">
    <v-card>
      <WebAppContainer />
    </v-card>
    <v-card class="mt-7">
      <v-card-title> NEWS </v-card-title>
      <v-list class="news">
        <v-list-item v-for="(item, index) in news" :key="index">
          <v-list-item-content>
            <v-row>
              <v-col sm=8>
                <v-icon v-if="item.priority === 2" color="red">mdi-alert-box-outline</v-icon>
                <v-icon v-if="item.priority === 1" color="orange">mdi-alert-box-outline</v-icon>
                {{ item.title }}
              </v-col>
              <v-spacer></v-spacer>
              <v-col sm=2>
                {{item.author}}
                {{item.created}}
              </v-col>
            </v-row>
            <hr />
            <div v-html="item.content" ></div>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<script>
import WebAppContainer from './WebAppContainer'
import TopBar from '@/components/TopBar'

export default {
  name: 'Welcome',
  components: { WebAppContainer, TopBar },
  computed: {
    news () {
      return this.$store.getters['news/get_news']
    }
  },
  methods: {
    async request_webapps () {
      let apps = this.$store.getters['users/get_webapps']

      if (apps.length === 0) {
        this.$store.dispatch('users/request_webapps')
      }
    }
  },
  mounted () {
    this.request_webapps()
    this.$store.dispatch('news/request_news')
  }
}
</script>

<style scoped lang="scss">

p {
  color: black !important;
}
.news {
  height: 25vh;
  overflow-y: scroll;
}
</style>
