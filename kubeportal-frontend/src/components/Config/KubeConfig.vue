<template>
  <b-card class="yaml-card">
    <b-card-header>Config</b-card-header>
    <b-card-body class="yaml-body">
      <b-card-text class="ma-1">
        <pre>{{ yamlfile }}</pre>
      </b-card-text>
    </b-card-body>
  </b-card>
</template>

<script>
export default {
  name: 'KubeConfig',
  props: ['yamlfile']
}
</script>

<style scoped lang="scss">
  div.card {
    min-width: 300px;
    max-width: 100%
  }
  .yaml-card {
    width: 35vw;
  }
  .yaml-body {
    width: 32vw;
  }

  @media (max-device-width: 1519px) {

    .yaml-card {
      width: 86vw
    }
    .yaml-body {
      width: 75vw;
    }
  }

</style>
