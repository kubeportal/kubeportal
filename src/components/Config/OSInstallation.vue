<template>
  <v-list-item>
    <v-list-item-content>
      <v-list-item-title v-for="instruction in instructions" :key="instruction.index">
        <v-icon class="icon" left>mdi-hand-pointing-right</v-icon>
        {{ instruction }}</v-list-item-title>
    </v-list-item-content>
  </v-list-item>
</template>

<script>
export default {
  name: 'OSInstallation',
  props: ['instructions']
}
</script>

<style scoped lang="scss">


</style>
