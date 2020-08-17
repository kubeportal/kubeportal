<template>
  <div class="ma-8 container-sm align-content-between">
    <b-button v-for="app in webapps" :key="app.index" class="app-button">
      {{ app.name }}
    </b-button>
  </div>
</template>

<script>
export default {
  name: 'WebAppContainer',
  computed: {
    webapps () {
      return this.$store.getters['get_webapps']
    }
  },
  async created () {
    await this.$store.dispatch('get_webapps')
  }
}
</script>

<style scoped lang="scss">
  .app-button {
    margin: 2vw 2vw 2vw 0vw;
    width: 18vw;
    min-width: 110px;
    height: 8vh;
    color: white;
    transition: 0.3s ease;
    opacity: 0.8;
    transform: translate(0, 0);
    -ms-transform: translate(0, 0%);
    background-color: #757575;
  }
  .app-button:hover {
    opacity: 1;
    transform: scale(1.1);
  }
</style>
