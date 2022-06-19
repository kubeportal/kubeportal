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

          <!-- Match Label Input -->
          <v-row v-for="(label, index) in match_labels" :key="'match_label'+index">
            <v-col md="5">
              <v-text-field v-model="label.key" label="Match Label Key" :rules="[rules.required]"/>
            </v-col>
            <v-col md="5">
              <v-text-field v-model="label.value" label="Match Label Value" :rules="[rules.required]"/>
            </v-col>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="match_labels.push({key:'', value:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="match_labels.splice(index, 1)"
              >
              <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-subheader>Pod Specifications</v-subheader>
          <v-text-field v-model="template_name" label="Pod Name" required> </v-text-field>

          <!-- Label Input -->
          <v-row v-for="(label, index) in template_labels" :key="'label'+index">
            <v-col md="5">
              <v-text-field v-model="label.key" label="Label Key" :rules="[rules.required]"/>
            </v-col>
            <v-col md="5">
              <v-text-field v-model="label.value" label="Label Value" :rules="[rules.required]"/>
            </v-col>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="template_labels.push({key:'', value:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="template_labels.splice(index, 1)"
              >
              <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>

          <!-- Container Input -->
          <v-row v-for="(container, index) in template_containers" :key="'container'+index">
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
                @click="template_containers.push({name:'', image:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="template_containers.splice(index, 1)"
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
  name: 'DeploymentModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      replicas: 1,
      match_labels: [{ key:'', value: '' }],
      template_name: '',
      template_labels: [{ key: '', value: '' }],
      template_containers: [{ name: '', image:'' }],
      rules: {
        required: value => !!value || 'Required.'
      }

    }
  },
  methods: {
    async post_deployment (e) {
      e.preventDefault()
      let data = {
        name: this.name,
        replicas: parseInt(this.replicas),
        match_labels: this.match_labels,
        pod_template: {
          name: this.template_name,
          labels: this.template_labels,
          containers: this.template_containers
        }
      }

      this.$store.dispatch('deployments/create_deployment', data)
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
  /* background-color: var(--v-primary) !important; */
}
</style>
