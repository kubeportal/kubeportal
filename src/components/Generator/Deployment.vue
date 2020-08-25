<template>
  <div class="text-left main">
    <b-row no-gutters>
      <b-col>
        <b-card-body class="card">
          <b-form>
            <b-form-group label="deployment name:">
              <b-form-input v-model="form.deploymentname" required></b-form-input>
            </b-form-group>

            <b-form-group label="image name:" description="schema: registry.datexis.com/<namespace>/<imagename>:<tag>">
              <b-form-input v-model="form.imagename" required></b-form-input>
            </b-form-group>

            <b-form-group label="namespace:">
              <b-form-input v-model="form.namespace" required></b-form-input>
            </b-form-group>

            <b-form-group label="container port:">
              <b-form-input v-model="form.containerport" required></b-form-input>
            </b-form-group>

            <b-form-group label="container name:">
              <b-form-input v-model="form.containername" required></b-form-input>
            </b-form-group>

            <b-form-group label="choose advanced settings:" class="annotations">
              <b-form-group label="CPU requests:">
                <b-form-select
                  :options="[{ text: 'Choose...', value: 2 }, '1', '2', '3', '4', '5', '6', '7', '8']"
                  :value="2"></b-form-select>
              </b-form-group>

              <b-form-group label="CPU limits:">
                <b-form-select
                  :options="[{ text: 'Choose...', value: 4 }, '1', '2', '3', '4', '5', '6', '7', '8']"
                  :value="4"></b-form-select>
              </b-form-group>

              <b-form-group id="input-group-5" label="memory requests:" label-for="input-5">
                <b-form-select
                  :options="[{ text: 'Choose...', value: 8 }, '2', '4', '8', '16', '32', '64', '128', '256']"
                  :value="8"
                ></b-form-select>
              </b-form-group>

              <b-form-group label="memory limits:">
                <b-form-select
                  :options="[{ text: 'Choose...', value: 16 }, '2', '4', '8', '16', '32', '64', '128', '256']"
                  :value="16"
                ></b-form-select>
              </b-form-group>
            </b-form-group>
          </b-form>
        </b-card-body>
      </b-col>
      <b-col>
        <YamlContainer :yamlfile="yamlfile"/>
      </b-col>
    </b-row>
  </div>

</template>

<script>
import YamlContainer from './YamlContainer'
import EventBus from '../../plugins/eventbus.js'

export default {
  name: 'Deployment',
  components: { YamlContainer },

  data () {
    return {
      form: {
        imagename: this.$store.getters['get_imagename'],
        deploymentname: this.$store.getters['get_deploymentname'],
        containername: this.$store.getters['get_containername'],
        namespace: this.$store.getters['get_namespace'],
        containerport: this.$store.getters['get_containerport']
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
      this.$store.commit('set_deployment_name', this.form.deploymentname)
      this.$store.commit('set_container_port', this.form.containerport)
      this.$store.commit('set_service_port', this.form.containerport)
      this.$store.commit('set_servicename', this.form.deploymentname + '-service')
      this.$store.commit('set_ingressname', this.form.deploymentname + '-ingress')
      this.$store.commit('set_container_name', this.form.containername)
      this.$store.commit('set_namespace', this.form.namespace)
      this.$store.commit('set_image_name', this.form.imagename)
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
