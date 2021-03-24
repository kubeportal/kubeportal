<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create Service </v-card-title>
      <v-card-text>
        <v-form @submit="post_service">
          <v-text-field
          v-model="name"
          :rules="name_rules"
          label="Name"
          required
        ></v-text-field>

        <v-select
          v-model="type"
          :items="type_items"
          label="Type"
          required
        ></v-select>

        <v-text-field
          v-model="app"
          label="App"
          required
        ></v-text-field>

        <v-text-field
          v-model="port"
          type="number"
          required
          label="Port"
        ></v-text-field>
        <v-select

          v-model="protocol"
          :items="protocol_items"
          label="Protocol"
          required
        ></v-select>
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
  name: 'IngressModak',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: ''
    }
  },
  methods: {
    async post_service (e) {
      e.preventDefault()
      console.log(this.name, this.type, this.app, this.protocol, this.port)
      let response = await backend.post(`/services/${this.namespace}/`, {
        name: this.name,
        type: this.type,
        selector: {
          app: this.app
        },
        ports: [
          {
            port: this.port,
            protocol: this.protocol
          }
        ]
      })
      console.log('POST SERVICE', response)
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
}
</style>
