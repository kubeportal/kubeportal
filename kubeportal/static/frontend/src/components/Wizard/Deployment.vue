<template>
  <div class="text-left">
    <v-row no-gutters>
      <v-col>
        <v-card>
          <v-form class="wizard_form">
            <v-text-field v-model="form.deploymentname" required label="deployment name"></v-text-field>
            <v-text-field v-model="form.imagename" required label="image name" hint="schema: registry.datexis.com/<namespace>/<imagename>:<tag>"></v-text-field>
            <v-text-field v-model="form.namespace" required label="namespace"></v-text-field>
            <v-text-field v-model="form.containerport" required label="container port"></v-text-field>
            <v-text-field v-model="form.containername" required label="container name"></v-text-field>
            <v-subheader v-text="'choose advanced settings:'"></v-subheader>
            <v-select
              :items="['1', '2', '3', '4', '5', '6', '7', '8']"
              :value="2"
              label="CPU requests">
            </v-select>
            <v-select
              :items="['1', '2', '3', '4', '5', '6', '7', '8']"
              :value="4"
              label="CPU limits">
            </v-select>
            <v-select
              :items="['2', '4', '8', '16', '32', '64', '128', '256']"
              :value="8"
              label="memory requests">
            </v-select>
            <v-select
              :items="['2', '4', '8', '16', '32', '64', '128', '256']"
              :value="16"
              label="memory limits">
            </v-select>
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
  name: 'Deployment',
  components: { YamlContainer },

  data () {
    return {
      form: {
        imagename: this.$store.getters['wizard/get_imagename'],
        deploymentname: this.$store.getters['wizard/get_deploymentname'],
        containername: this.$store.getters['wizard/get_containername'],
        namespace: this.$store.getters['wizard/get_namespace'],
        containerport: this.$store.getters['wizard/get_containerport']
      },
      options: ['', 'restriction to beuth network', 'cors-allow-origin'],
      tooltip: 'dasdas'
    }
  },

  computed: {
    jsonfile () {
      return {
        'kind': 'Deployment',
        'apiVersion': 'extensions/v1beta1',
        'metadata': {
          'name': this.form.deploymentname,
          'namespace': this.form.namespace,
          'labels': {
            'app': this.form.deploymentname
          }
        },
        'spec': {
          'replicas': 1,
          'selector': {
            'matchLabels': {
              'app': this.form.deploymentname
            }
          },
          'template': {
            'metadata': {
              'labels': {
                'app': this.form.deploymentname
              }
            },
            'spec': {
              'containers': [
                {
                  'name': this.form.containername,
                  'image': this.form.imagename,
                  'ports': [
                    {
                      'name': 'client-port',
                      'containerPort': this.form.containerport,
                      'protocol': 'TCP'
                    }
                  ]
                }
              ],
              'imagePullSecrets': [
                {
                  'name': 'private-registry-auth'
                }
              ],
              'schedulerName': 'default-scheduler'
            }
          }
        }
      }
    },
    yamlfile () {
      let string
      string = 'kind: Deployment\napiVersion: extensions/v1beta1\nmetadata:\n  name: ' + this.form.deploymentname + '\n  namespace: ' + this.form.namespace + '\n  labels:\n    app: ' + this.form.deploymentname + '\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: ' + this.form.deploymentname + '\n  template:\n    metadata:\n      labels:\n        app: ' + this.form.deploymentname + '\n    spec:\n      containers:\n      - name: ' + this.form.containername + '\n        image: ' + this.form.imagename + '\n        ports:\n        - name: client-port\n          containerPort: ' + this.form.containerport + '\n          protocol: TCP\n      imagePullSecrets:\n      - name: private-registry-auth\n      schedulerName: default-scheduler\n'
      return string
    }
  },
  created () {
    EventBus.$on('SaveDeploymentData', (() => {
      this.$store.commit('wizard/set_deployment_name', this.form.deploymentname)
      this.$store.commit('wizard/set_container_port', this.form.containerport)
      this.$store.commit('wizard/set_service_port', this.form.containerport)
      this.$store.commit('wizard/set_servicename', this.form.deploymentname + '-service')
      this.$store.commit('wizard/set_ingressname', this.form.deploymentname + '-ingress')
      this.$store.commit('wizard/set_container_name', this.form.containername)
      this.$store.commit('wizard/set_namespace', this.form.namespace)
      this.$store.commit('wizard/set_image_name', this.form.imagename)
    }))
  }
}
</script>

<style scoped>

  .card{
    margin-top: 1vw;
  }

  .wizard_form {
    width: 95%;
    margin: 0 1em;
  }
</style>
