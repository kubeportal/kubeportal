<template>
  <v-card>
    <v-card-title>Using Kubectl</v-card-title>
      <v-card-text>
        <Download />
        <div>
          <v-expansion-panels mandatory class="w-75 mx-auto">

            <v-expansion-panel>
              <v-expansion-panel-header class="button">
                <v-icon left class="icon">mdi-apple</v-icon>
                <v-icon left class="icon">mdi-linux</v-icon>
                MacOS/ Linux
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <OSInstallation :instructions="macUnix" />
              </v-expansion-panel-content>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-header class="button">
                <v-icon class="icon">mdi-microsoft-windows</v-icon>
                Windows
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <OSInstallation :instructions="windows" />
              </v-expansion-panel-content>
            </v-expansion-panel>

          </v-expansion-panels>
        </div>
      </v-card-text>
  </v-card>
</template>

<script>
import OSInstallation from './OSInstallation'
import KubeConfig from './KubeConfig'
import Download from './Download'

export default {
  name: 'KubeInstallation',
  components: { OSInstallation, KubeConfig, Download },

  data () {
    return {
      windows: ['Install kubectl for Windows', 'Navigate to your home directory: cd %USERPROFILE%', 'Create the .kube directory: mkdir .kube', 'Store the config file as .kube/config'],
      macUnix: ['Install kubectl with your package manager', 'Navigate to your home directory: cd ~', 'Create the .kube directory: mkdir .kube', 'Store the config file as .kube/config']
    }
  }
}

</script>

<style scoped lang="scss">
  .accordion{
    width: 60vw;
    margin: 0 auto;
  }

  .icon {
    color: white;
  }

  .button {
    background-color: #689F38 !important;
    color: white;
  }

</style>
