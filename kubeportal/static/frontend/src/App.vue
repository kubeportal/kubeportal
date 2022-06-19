<template>
  <v-app >
    <v-main>
      <v-img max-height="100vh" class="background" src="./assets/mountain.jpeg">
        <router-view/>
      </v-img>
    </v-main>
  </v-app>
</template>

<script>

export default {
  name: 'App'
}
</script>

<style scoped lang="scss">
  .icon, .v-icon.icon {
    position: absolute;
    left: 15px;
    color: floralwhite;
  }
  .toolbar {
    color: floralwhite;
  }
  .title {
    padding: 0 1rem 0 3rem;
    color: floralwhite;
  }
  .background {
    height: 100%;
    width: 100vw;
  }
</style>
