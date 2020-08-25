<template>
  <div class="text-left main">
      <b-row no-gutters>
        <b-col>
            <b-card-body class="card">
              <b-form>
                <b-form-group label="custom service name:">
                  <b-form-input v-model="form.servicename" required></b-form-input>
                </b-form-group>

                <b-form-group small label="service port">
                  <b-form-input v-model="form.serviceport" required></b-form-input>
               </b-form-group>

                <b-form-group label="namespace:">
                  <b-form-input v-model="form.namespace" required></b-form-input>
                </b-form-group>

                <b-form-group label="deployment name">
                  <b-form-input v-model="form.deploymentname" required></b-form-input>
                </b-form-group>
              </b-form>
            </b-card-body>
        </b-col>
        <b-col>
          <YamlContainer :yamlfile="yamlfile"/>
        </b-col>
      </b-row>
      <b-row>
        <div class="text-left">
        </div>
        <div class="text-right">
        </div>
      </b-row>
  </div>
</template>

<script>
import YamlContainer from './YamlContainer'
import EventBus from '../../plugins/eventbus.js'

export default {
  name: 'Service',
  components: { YamlContainer },

  data () {
    return {
      form: {
        serviceport: this.$store.getters['get_containerport'],
        servicename: this.$store.getters['get_servicename'],
        namespace: this.$store.getters['get_namespace'],
        deploymentname: this.$store.getters['get_deploymentname']
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
  .main {
    padding: 2vw 0vw 0vw 0vw;
  }
</style>
