<template>
  <v-card class="yaml_card">
    <v-card-text>
      <pre>{{ yamlfile }}</pre>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'YamlContainer',

  props: ['yamlfile']
}
</script>

<style scoped>
  .yaml_card {
    height: 100%;
    margin-left: 2em;
  }

  pre {
    color: var(--v-pre_color);
  }
</style>
