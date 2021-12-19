<template>
  <div class="text-left">
    <v-row no-gutters>
      <v-col>
        <v-card>
          <v-form class="wizard_form">
            <v-text-field v-model="form.ingressname" required label="cutom ingress name"></v-text-field>
            <v-select v-model="form.domainname" :items="domains" required label="domain"></v-select>
            <v-text-field v-model="form.subdomain" required label="subdomain"></v-text-field>
            <v-text-field v-model="form.servicename" required label="service name"></v-text-field>
            <v-text-field v-model="form.serviceport" required label="service port"></v-text-field>
            <v-text-field v-model="form.namespace" required label="namespace"></v-text-field>
            <v-subheader v-text="'choose more annotations:'"></v-subheader>
            <v-checkbox label="enable CORS" v-model="allow_cors" color="blue"></v-checkbox>
            <v-checkbox label="restriction to beuth network" v-model="allow_restriction" color="blue"></v-checkbox>
            <v-checkbox label="cors-allow-origin" v-model="allow_cors_origin" color="blue"></v-checkbox>
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
  name: 'Ingress',
  components: { YamlContainer },

  data () {
    return {
      form: {
        ingressname: this.$store.getters['wizard/get_ingressname'],
        serviceport: this.$store.getters['wizard/get_serviceport'],
        servicename: this.$store.getters['wizard/get_servicename'],
        domainname: this.$store.getters['wizard/get_domainname'],
        subdomain: this.$store.getters['wizard/get_subdomain'],
        namespace: this.$store.getters['wizard/get_namespace']
      },
      domains: ['demo.datexis.com', 'app.datexis.com', 'internal.datexis.com', 'api.datexis.com'],
      sourceRange: '*',
      selected: [],
      allow_cors: false,
      allow_restriction: false,
      allow_cors_origin: false
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
      let hostname = this.form.subdomain + '.' + this.form.domainname
      this.commitData()
      if(await this.checkHostName()) {
        // console.log('check ok')
      } else {
        // console.log('Hostname already exists')
      }
    },
    async checkHostName () {
      let hostname = this.form.subdomain + '.' + this.form.domainname
      const validation = await this.$store.dispatch('wizard/validate_hostname', hostname)
      return validation
    }
  },
  created () {
    EventBus.$on('SaveIngressData', (() => {
      this.$store.commit('wizard/set_ingressname', this.form.ingressname)
      this.$store.commit('wizard/set_domainname', this.form.domainname)
      this.$store.commit('wizard/set_subdomain', this.form.subdomain)
      this.$store.commit('wizard/set_namespace', this.form.namespace)
      this.$store.commit('wizard/set_servicename', this.form.servicename)
      this.$store.commit('wizard/set_service_port', this.form.serviceport)
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
