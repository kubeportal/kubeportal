<template>
  <b-card-body>
    <b-card-text>
      <b-card>
          <pre>{{ yamlfile }}</pre>
      </b-card>
    </b-card-text>
  </b-card-body>
</template>

<script>
export default {
  name: 'YamlContainer',

  props: ['yamlfile']
}
</script>

<style scoped>

</style>
