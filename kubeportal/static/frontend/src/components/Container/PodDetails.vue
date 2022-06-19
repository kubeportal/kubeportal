<template>
  <div>
    <v-btn class="backBtn" @click="$emit('close_details')">
      <v-icon >mdi-arrow-left</v-icon>
      Back
    </v-btn>
    <v-tabs fixed-tabs >
      <v-tab>
        <v-icon class="mr-2">mdi-desktop-classic</v-icon>
        Details
      </v-tab>
      <v-tab v-if="use_elastic">
        <v-icon class="mr-2">mdi-hexagon-multiple-outline</v-icon>
        Logs
      </v-tab>

      <v-tab-item>
        <div>
          <v-card class="details">

            <v-card-title>Pod Name</v-card-title>
            <v-row class="detailRow">
              <v-col>{{ pod.name }}</v-col>
            </v-row>

            <v-card-title>Timestamps</v-card-title>
            <v-row class="detailRow">
              <v-col>
                created
                {{ pod.creation_timestamp }}
              </v-col>

              <v-col>
                started
                {{ pod.start_timestamp }}
             </v-col>
            </v-row>

            <v-card-title>Phase</v-card-title>
            <v-row class="detailRow">
              <v-col>{{ pod.phase }}</v-col>
            </v-row>

            <v-card-title>Pod UID</v-card-title>
            <v-row class="detailRow">
              <v-col>{{ pod.puid }}</v-col>
            </v-row>

            <v-card-title>Host IP</v-card-title>
            <v-row class="detailRow">
             <v-col>{{ pod.host_ip }}</v-col>
            </v-row>

            <v-card-title>Container</v-card-title>
            <v-row class="detailRow">
             <v-col
                v-for="container in pod.containers"
                :key="container"
              >
                {{ container }}
              </v-col>
            </v-row>

            <v-card-title>Images</v-card-title>
            <v-row class="detailRow">
             <v-col
                v-for="image in pod.images"
                :key="image"
              >
                {{ image }}
              </v-col>
            </v-row>

            <v-card-title>Volumes</v-card-title>
            <v-row class="detailRow"
              v-for="(volume, i) in pod.volumes"
                :key="volume.name"
              >
                <v-col>name: {{ pod.volumes[i].volume.name }}</v-col>
                <v-col>type: {{ pod.volumes[i].volume.type }}</v-col>
                <v-col>mountpath: {{ pod.volumes[i].mount_path }}</v-col>
            </v-row>
          </v-card>
        </div>
      </v-tab-item>
      <v-tab-item v-if="use_elastic">
        <Logs :pod="pod" :namespace="namespace" />
      </v-tab-item>
    </v-tabs>
  </div>
</template>

<script>
import Logs from '@/components/Logs'

export default {
  name: 'PodDetails',
  components: { Logs },
  props: ['pod', 'namespace'],
  methods: {
    close_details () {
      this.$emit('close_details')
    }
  },
  computed: {
    use_elastic () {
      return this.$store.getters['api/get_use_elastic']
    }
  }
}
</script>

<style scoped>
.details {
  width: 100%;
  height: 60vh;
  overflow-y: scroll;
}
.detailRow {
  padding: 0 1em;
}
.backBtn {
  margin-bottom: 1em;
}
</style>
