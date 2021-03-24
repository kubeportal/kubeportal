<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create Deployment </v-card-title>
      <v-card-text>
        <v-form @submit="post_deployment">
          <v-text-field v-model="name" label="Name" required> </v-text-field>
          <v-text-field
            v-model="replicas"
            label="Replicas"
            type="number"
            required
          >
          </v-text-field>
          <v-row align="center">
            <v-col>
              <v-btn color="success" type="submit"> Submit </v-btn>
            </v-col>
            <v-col>
              <v-btn @click="emit_event" color="error" type="button">
                Cancel
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </v-overlay>
</template>

<script>
import * as backend from '@/utils/backend'
export default {
  name: 'DeploymentModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      replicas: 1
    }
  },
  methods: {
    async post_deployment (e) {
      e.preventDefault()
      console.log(this.name, this.replicas)
      let response = await backend.post(`/deployments/${this.namespace}/`, {
        name: this.name,
        replicas: this.replicas
      })
      console.log('DEPLOYMENT POST', response)
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
  width: 20vw;
  /* background-color: var(--v-primary) !important; */
}
</style>
