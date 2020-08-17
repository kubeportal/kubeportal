<template>
  <v-app >
    <v-main>
      <v-toolbar flat class="blue-grey darken-4 toolbar">
        <v-icon class="icon">mdi-view-dashboard-variant</v-icon>
        <v-toolbar-title class="title">Data Science Cluster</v-toolbar-title>
      </v-toolbar>
      <router-view />
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

</style>
