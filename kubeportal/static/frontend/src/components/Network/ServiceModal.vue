<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create Service </v-card-title>
      <v-card-text>
        <v-form @submit="post_service">
          <v-text-field
          v-model="name"
          label="Name"
          required
        ></v-text-field>

        <v-select
          v-model="type"
          :items="type_items"
          label="Type"
          required
        ></v-select>

        <!-- Selectors Input -->
        <v-row v-for="(selector, index) in selectors" :key="'selector'+index">
          <v-col md="5">
            <v-text-field v-model="selector.key" label="Selector Key" :rules="[rules.required]"/>
          </v-col>
          <v-col md="5">
            <v-text-field v-model="selector.value" label="Selector Value" :rules="[rules.required]"/>
          </v-col>
          <v-col md="2" v-if="index === 0">
            <v-btn
              icon
              large
              @click="selectors.push({key:'', value:''})"
            >
            <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </v-col>
          <v-col md="2" v-else>
            <v-btn
              icon
              color="red"
              large
              @click="selectors.splice(index, 1)"
            >
            <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-col>
        </v-row>

        <!-- Ports Input -->
        <v-row v-for="(port, index) in ports" :key="'port'+index">
          <v-col md="5">
            <v-text-field v-model="port.port" label="Port" type="number" :rules="[rules.required]"/>
          </v-col>
          <v-col md="5">
            <v-select
            v-model="port.protocol"
            :items="protocol_items"
            label="Protocol"
          ></v-select>
          </v-col>
          <v-col md="2" v-if="index === 0">
            <v-btn
              icon
              large
              @click="ports.push({port:0, protocol:''})"
            >
            <v-icon>mdi-plus-circle</v-icon>
            </v-btn>
          </v-col>
          <v-col md="2" v-else>
            <v-btn
              icon
              color="red"
              large
              @click="ports.splice(index, 1)"
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
  name: 'ServiceModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      type: '',
      type_items: ['NodePort', 'CluserIP', 'LoadBalancer'],
      selectors: [{ key:'', value: '' }],
      protocol_items: ['TCP', 'UDP', 'SCTP'],
      ports: [{ port:0, protocol:'' }],
      rules: {
        required: value => !!value || 'Required.'
      }
    }
  },
  methods: {
    async post_service (e) {
      e.preventDefault()
      let data = {
        name: this.name,
        type: this.type,
        selector: this.selectors,
        ports: this.ports.map(port => { return { ...port, port: parseInt(port.port) } })
      }
      this.$store.dispatch('services/create_service', data)
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
