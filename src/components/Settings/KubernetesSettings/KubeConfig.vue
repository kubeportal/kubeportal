<template>
  <v-card class="yaml-card">
    <v-card-title>Config</v-card-title>
    <v-card-text>
        <pre>{{ yamlfile }}</pre>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'KubeConfig',
  computed: {
    current_user () {
      return this.$store.getters['users/get_user']
    },
    yamlfile () {
      let string =
        'apiVersion: v1\nclusters:\n  - cluster:\n      insecure-skip-tls-verify: true\n      server: https://datexis-master2.beuth-hochschule.de:6443\n    name: data_science_cluster\ncontexts:\n  - context:\n      cluster: data_science_cluster\n      namespace: default\n      user: ' + this.current_user.username + '\n    name: ' + this.current_user.username + '\ncurrent-context: ' + this.current_user.username + '\nkind: Cluster\npreferences: {}\nusers:\n  - name: ' + this.current_user.username + '\n    user:\n      token: eyJhbllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllfmqfTjXg\n'
      return string
    }
  }
}
</script>

<style scoped lang="scss">

</style>
