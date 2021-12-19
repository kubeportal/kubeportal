<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create Pod </v-card-title>
      <v-card-text>
        <v-form @submit="post_pod">
          <v-text-field v-model="name" label="Pod Name" :rules="[rules.required, rules.pod_name]"> </v-text-field>
          <v-row v-for="(container, index) in containers" :key="index">
            <v-col md="5">
              <v-text-field v-model="container.name" label="Container Name" :rules="[rules.required]"/>
            </v-col>
            <v-col md="5">
              <v-text-field v-model="container.image" label="Container Image" :rules="[rules.required]"/>
            </v-col>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="containers.push({name:'', image:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="containers.splice(index, 1)"
              >
              <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>

          <v-row justify="end">
            <v-col md="2">
              <v-btn @click="emit_event" color="error" type="button">
                Cancel
              </v-btn>
            </v-col>
            <v-col md="2">
              <v-btn color="success" type="submit"> Submit </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </v-overlay>
</template>

<script>
export default {
  name: 'PodModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      containers: [{ image:'', name:'' }],
      rules: {
        required: value => !!value || 'Required.',
        pod_name: value => {
          const pattern = /[a-z0-9]([-a-z0-9]*[a-z0-9])?/
          return pattern.test(value) || 'Invalid Pod Name.'
        }
      }
    }
  },
  methods: {
    async post_pod (e) {
      e.preventDefault()
      let data = {
        name: this.name,
        containers: this.containers
      }
      this.$store.dispatch('pods/create_pod', data)
      this.emit_event()
    },
    emit_event () {
      this.$emit('close', false)
    }
  }
}
</script>

<style scoped>
.modal {
  width: 50vw;
}
</style>
