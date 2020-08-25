<template>
  <b-card class="kubeinstallation">
    <b-card-header>Using Kubectl</b-card-header>
    <b-card-body class="kubeinstallation">
      <b-card-text>
        <p class="content">This configuration file is needed for Kubernetes client tools on your computer.
          It contains your personal access token.</p>
        <div class="row">
          <v-tooltip right>
            <template v-slot:activator="{ on, attrs }">
              <b-button v-bind="attrs" v-on="on" class="btn btn-secondary" aria-expanded="true" v-b-toggle.accordion-1>
                <v-icon class="icon" left>mdi-apple</v-icon>
                <v-icon class="icon" left>mdi-linux</v-icon>
                MacOS / Linux / Unix
              </b-button>
            </template>
            <span>{{ tooltip }}</span>
          </v-tooltip>
          <b-collapse id="accordion-1" v-b-visible accordion="accordion1" role="tabpanel">
          <OSInstallation :instructions="macUnix" />
          </b-collapse>
        </div>
        <div class="row" id="target">
          <v-tooltip right>
          <template v-slot:activator="{ on, attrs }">
            <b-button v-bind="attrs" v-on="on" class="btn btn-secondary" aria-expanded="true" v-b-toggle.accordion-2>
              <v-icon class="icon" left>mdi-microsoft-windows</v-icon>
              Windows
            </b-button>
          </template>
          <span>{{ tooltip }}</span>
          </v-tooltip>
          <b-collapse id="accordion-2" v-b-visible accordion="accordion2" role="tabpanel">
            <OSInstallation :instructions="windows" />
          </b-collapse>
        </div>
      </b-card-text>
    </b-card-body>
  </b-card>
</template>

<script>
import OSInstallation from './OSInstallation'
export default {
  name: 'KubeInstallation',
  components: { OSInstallation },
  props: ['yamlfile'],
  data () {
    return {
      tooltip: 'You can test your installation by calling kubectl cluster-info.',
      windows: ['Install kubectl for Windows', 'Navigate to your home directory: cd %USERPROFILE%', 'Create the .kube directory: mkdir .kube', 'Store the config file as .kube/config'],
      macUnix: ['Install kubectl with your package manager', 'Navigate to your home directory: cd ~', 'Create the .kube directory: mkdir .kube', 'Store the config file as .kube/config']
    }
  }
}
</script>

<style scoped lang="scss">
  .kubeinstallation {
    width: 30vw
  }
  .btn {
    margin: 2vw 0vw 1vw 0vw;
    color: floralwhite;
  }
  .icon {
    color: floralwhite;
  }
  .content {
    max-width: 80%;
  }
  @media (max-device-width: 1519px) {
    .kubeinstallation {
      width: 80vw
    }
  }
</style>
