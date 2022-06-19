<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create Ingress </v-card-title>
      <v-card-text>
        <v-form @submit="post_ingress">
          <v-text-field
          v-model="name"
          :rules="[rules.required]"
          label="Name"
        ></v-text-field>

        <v-switch
          v-model="tls"
          :label="`Https: ${tls ? 'on' : 'off'}`"
        ></v-switch>

          <!-- Annotations Input -->
          <v-row v-for="(annotation, index) in annotations" :key="'annotations'+index">
            <v-col md="5">
              <v-text-field v-model="annotation.key" label="Annotation Key" :rules="[rules.required]"/>
            </v-col>
            <v-col md="5">
              <v-text-field v-model="annotation.value" label="Annotation Value" :rules="[rules.required]"/>
            </v-col>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="annotations.push({key:'', value:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="annotations.splice(index, 1)"
              >
              <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>

          <!-- Ingress Rules Input -->
          <v-row v-for="(rule, index) in ingress_rules" :key="'ingress_rules'+index">
              <v-col md="12">

                <v-text-field v-model="rule.host" label="Host" :rules="[rules.required]"/>
              </v-col>

              <v-row v-for="(path, rule_index) in rule.paths" :key="index+'path'+rule_index">
                <v-col md="12">

                <v-text-field v-model="path.path" label="Path" :rules="[rules.required]"/>
                </v-col>
                <v-col md="5">
                  <v-text-field v-model="path.service_name" label="Service Name" :rules="[rules.required]"/>
              </v-col>
                <v-col md="5">
                  <v-text-field v-model="path.service_port" label="Service Port" type="number" :rules="[rules.required]"/>
                </v-col>
                <v-col md="2" v-if="rule_index === 0">
                  <v-btn
                    icon
                    large
                    @click="rule.paths.push({path:'', service_name:'', service_port: 0})"
                  >
                  <v-icon>mdi-plus-circle</v-icon>
                  </v-btn>
                </v-col>
                <v-col md="2" v-else>
                  <v-btn
                    icon
                    color="red"
                    large
                    @click="rule.paths.splice(index, 1)"
                  >
                  <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="ingress_rules.push({ host: '', paths: [{ path: '', service_name:'', service_port: 0 }] })"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="ingress_rules.splice(index, 1)"
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
  name: 'IngressModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      tls: true,
      annotations: [{ key: '', value: '' }],
      ingress_rules: [{ host: '', paths: [{ path: '', service_name:'', service_port: 0 }] }],
      rules: {
        required: value => !!value || 'Required.'
      }
    }
  },
  methods: {
    async post_ingress (e) {
      e.preventDefault()
      let data = {
        name: this.name,
        tls: this.tls,
        annotations: this.annotations,
        rules: this.ingress_rules.map(rule => { return { ...rule, paths: rule.paths.map(path => { return { ...path, service_port: parseInt(path.service_port) } }) } })
      }
      this.$store.dispatch('ingresses/create_ingress', data)
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
