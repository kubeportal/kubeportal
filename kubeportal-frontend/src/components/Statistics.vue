<template>
  <b-card class="maincard">
    <b-card-header>
      Cluster Statistics
    </b-card-header>

    <div>
    <v-simple-table fixed-header>
      <template v-slot:default>
        <thead>
        <tr>
          <th class="first text-left">Name</th>
          <th class="second text-left">Value</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="item in all_statistics" :key="item.index">
          <td>{{ Object.keys(item)[0] }}</td>
          <td>{{ Object.values(item)[0]}}</td>
        </tr>
        </tbody>
      </template>
    </v-simple-table>
    </div>
  </b-card>
</template>

<script>

export default {
  name: 'Statistics',
  computed: {
    all_statistics () {
      console.log(this.$store.getters['get_all_statistics'])
      return this.$store.getters['get_all_statistics']
    }
  }
}
</script>

<style scoped lang="scss">
  .first {
    width: 30rem;
  }
</style>
