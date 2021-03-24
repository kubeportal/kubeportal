<template>
  <v-row class="p-4">
    <v-col lg="6">
      <v-card class="config">
        <v-card-title>
          <v-row>
            <v-col lg="3"> Config file </v-col>
            <v-spacer />
            <v-col lg="1" @click="download">
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn type="button" icon v-bind="attrs" v-on="on">
                    <v-icon> mdi-download </v-icon>
                  </v-btn>
                </template>
                <span>download config.yaml</span>
              </v-tooltip>
            </v-col>
          </v-row>
        </v-card-title>
        <v-card-text>
          <v-hover v-slot="{ hover }">
            <div>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn
                    type="button"
                    class="clipboard-btn"
                    icon
                    :class="{ 'on-hover': !hover }"
                    v-clipboard:copy="config_file"
                    v-clipboard:success="onCopy"
                    v-clipboard:error="onError"
                    v-bind="attrs"
                    v-on="on"
                  >
                    <v-icon> mdi-clipboard-multiple-outline </v-icon>
                  </v-btn>
                </template>
                <span>Copy to clipboard</span>
              </v-tooltip>
              <pre >
                {{ config_file }}
              </pre>
            </div>
          </v-hover>
          <div class="alerts">
            <v-alert v-if="success" dense type="success">
              Copied to clipboard!
            </v-alert>
            <v-alert v-if="error" dense type="error">
              Something went wrong!
            </v-alert>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col lg="6">
      <KubeInstallation />
    </v-col>
  </v-row>
</template>

<script>
import KubeInstallation from './KubeInstallation'
export default {
  name: 'KubernetesSettings',
  components: { KubeInstallation },
  data () {
    return {
      success: false,
      error: false
    }
  },
  computed: {
    current_user () { return this.$store.getters['users/get_user'] },
    user_groups () { return this.$store.getters['users/get_groups'] },
    config_file () {
      return `
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://datexis-master2.beuth-hochschule.de:6443
  name: data_science_cluster
contexts:
- context:
    cluster: data_science_cluster
    namespace: ${this.current_user['k8s_namespace']}
    user: ${this.current_user['username']}
  name: ${this.current_user['username']}
current-context: ${this.current_user['username']}
kind: Config
preferences: {}
users:
- name: ${this.current_user['username']}
  user:
    token: ${this.current_user['k8s_token']}`
    }
  },
  methods: {
    download () {
      const element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(this.config_file))
      element.setAttribute('download', 'config.yaml')
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    },
    onCopy () {
      this.success = true
      setTimeout(() => {
        this.success = false
      }, 1000)
    },
    onError () {
      console.log('error')
      this.error = true
      setTimeout(() => {
        this.error = false
      }, 1000)
    }
  }
}
</script>

<style scoped>
  .config {
    max-width: 50vw;
    height: 100%;
  }
  pre {
    color: var(--v-pre_color);
    white-space: pre-wrap;
    white-space: -moz-pre-wrap;
    white-space: -pre-wrap;
    white-space: -o-pre-wrap;
    word-wrap: break-word;
  }
  .alerts{
    position: absolute;
  }

  .clipboard-btn{
    position: absolute;
    right: 1%;
  }
  .on-hover{
    opacity: .5;
  }
  .btn {
    color: floralwhite;
  }

</style>
