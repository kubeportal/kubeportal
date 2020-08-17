<template>
  <b-card>
    <b-card-header>Config</b-card-header>
    <b-card-body class="yaml">
      <b-card-text>
        <pre>{{ yamlfile }}</pre>
      </b-card-text>
    </b-card-body>
  </b-card>
</template>

<script>
export default {
  name: 'YamlContainer',
  props: ['yamlfile']
}
</script>

<style scoped lang="scss">
  div.card {
    width: 40vw;
  }

</style>
