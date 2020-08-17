<template>
  <b-card class="maincard">
    <b-card-header>
      Cluster Statistics
    </b-card-header>

    <v-simple-table fixed-header>
      <template v-slot:default>
        <thead>
        <tr>
          <th class="text-left">Name</th>
          <th class="text-left">Value</th>
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
