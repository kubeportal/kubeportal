<template>
  <div class="text-left main">
        <b-row no-gutters>
        <b-col>
            <b-card-body class="card">
              <b-form>
                <b-form-group label="custom ingress name:">
                  <b-form-input v-model="form.ingressname" required></b-form-input>
                </b-form-group>

                <b-form-group small label="domain:">
                  <b-form-select v-model="form.domainname" :options="domains" required></b-form-select>
               </b-form-group>

                <b-form-group label="subdomain:">
                  <b-form-input v-model="form.subdomain" required></b-form-input>
                </b-form-group>

                <b-form-group label="service name:">
                  <b-form-input v-model="form.servicename" required></b-form-input>
                </b-form-group>

                <b-form-group label="service port:">
                  <b-form-input v-model="form.serviceport" required></b-form-input>
                </b-form-group>

                <b-form-group label="namespace:">
                  <b-form-input v-model="form.namespace" required></b-form-input>
                </b-form-group>

                <b-form-group label="choose more annotations:" class="annotations">
                  <b-form-checkbox-group
                    v-model="selected"
                    :options="options"
                    name="flavour-2a"
                    stacked>
                  </b-form-checkbox-group>
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
  name: 'Ingress',
  components: { YamlContainer },

  data () {
    return {
      form: {
        ingressname: this.$store.getters['get_ingressname'],
        serviceport: this.$store.getters['get_serviceport'],
        servicename: this.$store.getters['get_servicename'],
        domainname: this.$store.getters['get_domainname'],
        subdomain: this.$store.getters['get_subdomain'],
        namespace: this.$store.getters['get_namespace']
      },
      domains: [{ text: 'choose...', value: '' }, 'demo.datexis.com', 'app.datexis.com', 'internal.datexis.com', 'api.datexis.com'],
      options: ['enable CORS', 'restriction to beuth network', 'cors-allow-origin'],
      sourceRange: '*',
      selected: []
    }
  },

  computed: {
    jsonfile () {
      return {
        'kind': 'Ingress',
        'apiVersion': 'extensions/v1beta1',
        'metadata': {
          'name': this.form.ingressname,
          'namespace': this.form.namespace,
          'annotations': {
            'cert-manager.io/cluster-issuer': 'letsencrypt',
            'kubernetes.io/ingress.class': 'nginx'
          }
        },
        'spec': {
          'tls': [
            {
              'hosts': [
                this.form.subdomain + '.' + this.form.domainname
              ],
              'secretName': this.form.subdomain + '-' + this.form.namespace + '-ingress-tls'
            }
          ],
          'rules': [
            {
              'host': this.form.subdomain + '.' + this.form.domainname,
              'http': {
                'paths': [
                  {
                    'backend': {
                      'serviceName': this.form.servicename,
                      'servicePort': this.form.serviceport
                    }
                  }
                ]
              }
            }
          ]
        }
      }
    },
    yamlfile () {
      let string
      string =
           'kind: Ingress\napiVersion: extensions/v1beta1\nmetadata:\n  name: ' + this.form.ingressname + '\n  namespace: ' + this.form.namespace + '\n  annotations:\n    cert-manager.io/cluster-issuer: letsencrypt\n    kubernetes.io/ingress.class: nginx\nspec:\n  tls:\n   - hosts:\n    - ' + this.form.subdomain + '.' + this.form.domainname + '\n    secretName: ' + this.form.subdomain + '-' + this.form.namespace + '-ingress-tls\n  rules:\n  - host: ' + this.form.subdomain + '.' + this.form.domainname + '\n    http:\n      paths:\n      - backend:\n          serviceName: ' + this.form.servicename + '\n          servicePort: ' + this.form.serviceport + '\n'
      return string
    }
  },
  methods: {
    commitData () {

    },
    async viewAll () {
      console.log('view all clicked')
      let hostname = this.form.subdomain + '.' + this.form.domainname
      console.log(hostname)
      this.commitData()
      if(await this.checkHostName()) {
        console.log('check ok')
      } else {
        console.log('Hostname already exists')
      }
    },
    async checkHostName () {
      let hostname = this.form.subdomain + '.' + this.form.domainname
      const validation = await this.$store.dispatch('validate_hostname', hostname)
      return validation
    }
  },
  created () {
    EventBus.$on('SaveIngressData', (() => {
      this.$store.commit('set_ingressname', this.form.ingressname)
      this.$store.commit('set_domainname', this.form.domainname)
      this.$store.commit('set_subdomain', this.form.subdomain)
      this.$store.commit('set_namespace', this.form.namespace)
      this.$store.commit('set_servicename', this.form.servicename)
      this.$store.commit('set_service_port', this.form.serviceport)
    }))
  }
}
</script>

<style scoped>
  .main {
    padding: 2vw 0vw 0vw 0vw;
  }
  .card {
    margin-top: 1vw;
  }

</style>
