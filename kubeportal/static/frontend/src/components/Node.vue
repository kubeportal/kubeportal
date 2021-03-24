<template>
  <div>
    <TopBar :title="tab.name"/>
    <v-card>
      <component :is="tab.component"/>
    </v-card>
  </div>
</template>

<script>
import TopBar from '@/components/TopBar'
export default {
  name: 'Node',
  props: ['tab'],
  components: { TopBar }
}
</script>

<style>

</style>
