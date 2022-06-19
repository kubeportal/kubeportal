<template>
  <div class="text-left">
    <v-row no-gutters>
      <v-col>
        <v-card>
          <v-form class="wizard_form">
            <v-text-field v-model="form.servicename" required label="custom service name"></v-text-field>
            <v-text-field v-model="form.serviceport" required label="service port"></v-text-field>
            <v-text-field v-model="form.namespace" required label="namespace"></v-text-field>
            <v-text-field v-model="form.deploymentname" required label="deployment name"></v-text-field>
          </v-form>
        </v-card>
      </v-col>
      <v-col>
        <YamlContainer :yamlfile="yamlfile"/>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import YamlContainer from './YamlContainer'
import EventBus from '@/utils/eventbus'

export default {
  name: 'Service',
  components: { YamlContainer },

  data () {
    return {
      form: {
        serviceport: this.$store.getters['wizard/get_containerport'],
        servicename: this.$store.getters['wizard/get_servicename'],
        namespace: this.$store.getters['wizard/get_namespace'],
        deploymentname: this.$store.getters['wizard/get_deploymentname']
      }
    }
  },

  computed: {
    jsonfile () {
      return {
        'kind': 'Service',
        'apiVersion': 'v1',
        'metadata': {
          'name': this.form.servicename,
          'namespace': this.form.namespace
        },
        'spec': {
          'ports': [
            {
              'protocol': 'TCP',
              'port': this.form.serviceport,
              'targetPort': this.form.targetport
            }
          ],
          'selector': {
            'app': this.form.deploymentname
          }
        }
      }
    },
    yamlfile () {
      let string =
             'kind: Service\napiVersion: v1\nmetadata:\n  name: ' + this.form.servicename + '\n  namespace: ' + this.form.namespace + '\nspec:\n  ports:\n  - protocol: TCP\n    port: ' + this.form.serviceport + '\nselector:\n    app: ' + this.form.deploymentname + '\n'
      return string
    }
  },
  created () {
    EventBus.$on('SaveServiceData', (() => {
      this.$store.commit('set_servicename', this.form.servicename)
      this.$store.commit('set_service_port', this.form.serviceport)
      this.$store.commit('set_namespace', this.form.namespace)
      this.$store.commit('set_deployment_name', this.form.deploymentname)
    }))
  }
}
</script>

<style scoped>
  .card {
    margin-top: 1vw;
  }

  .wizard_form {
    width: 95%;
    margin: 0 1em;
  }
</style>
