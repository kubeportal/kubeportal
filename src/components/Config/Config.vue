<template>
  <b-card class="maincard-adapt">
  <b-card-body>
    <div class="container-fluid">
    <div class="row">
      <div class="col-sm">
        <KubeConfig :yamlfile="yamlfile" />
      </div>
      <div class="col-sm">
        <KubeInstallation  />
      </div>
    </div>
    </div>
  </b-card-body>
  </b-card>
</template>

<script>
import KubeConfig from './KubeConfig'
import KubeInstallation from './KubeInstallation'

export default {
  name: 'Config',
  components: { KubeInstallation, KubeConfig },
  data () {
    return {
      current_user: this.$store.getters['get_current_user']
    }
  },

  computed: {
    yamlfile () {
      let string =
        'apiVersion: v1\nclusters:\n  - cluster:\n      insecure-skip-tls-verify: true\n      server: https://datexis-master2.beuth-hochschule.de:6443\n    name: data_science_cluster\ncontexts:\n  - context:\n      cluster: data_science_cluster\n      namespace: default\n      user: ' + this.current_user.username + '\n    name: ' + this.current_user.username + '\ncurrent-context: ' + this.current_user.username + '\nkind: Config\npreferences: {}\nusers:\n  - name: ' + this.current_user.username + '\n    user:\n      token: eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InJvb3QtdG9rZW4tMjg3bTQiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoicm9vdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImJlMWY3NmE4LWE2MGItMTFlOC1iNTI5LTBjYzQ3YTQ1MWE2ZSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OnJvb3QifQ.AN_4gI5WpEmJNCH4vBReSMJPbzYA-4T_EEOeExjKpmvJunWaaFazToYCn0TFrowDTYshx3y3O-BBlirtHCXfRpSzMhiGaac7WcQR1C9UOmEcRl8GGpOkhrs5ItwwVS5Eegb6DIirndvuNYUzS-x35yfPrZrIQD8BPArXMYB8Nko9Ikl0ufPO-3Kiw_p6q5nQ3b4y8hZf7t_8fhYbEFtvwyWMibjeCgEbx_Zl-2UnHa5UV6qbBkihZz2Wqpnf-wTWXBshuVwmqY1QJZfhvkrDSa4t2yu7E256EKNZbfOsve0kkTL67cdwAs5s3eioT90dIGa-pTHqK-cVMgfmqfTjXg\n'
      return string
    }
  }
}
</script>

<style scoped lang="scss">
  .config {
    display: inline;
  }
  div.card {
    min-width: 300px;
    max-width: 100%;
  }

  .maincard-adapt {
    max-width: 100%;
  }

  @media (max-device-width: 1519px) {

    .maincard-adapt {
      width: 86vw;
      max-width: 100%
    }

  }

</style>
