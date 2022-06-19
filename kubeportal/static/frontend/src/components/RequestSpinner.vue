<template>
  <div class="text-center m-4">
        <v-progress-circular
        :size="50"
        color="primary"
        indeterminate
      ></v-progress-circular>
    </div>
</template>

<script>
export default {
  name: 'RequestSpinner'
}
</script>

<style>
</style>
