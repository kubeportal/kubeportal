<template>
  <v-overlay :value="overlay">
    <v-card class="modal" light>
      <v-card-title> Create PVC </v-card-title>
      <v-card-text>
        <v-form @submit="post_pvc">
          <v-text-field v-model="name" label="PVC Name" :rules="[rules.required]"> </v-text-field>
          <v-row v-for="(access_mode, index) in access_modes" :key="'acces_modes'+index">
            <v-col md="10">
              <v-select
                v-model="access_mode.value"
                :items="access_modes_items"
                label="Access Mode"
                :rules="[rules.required]"
              ></v-select>
            </v-col>
            <v-col md="2" v-if="index === 0">
              <v-btn
                icon
                large
                @click="access_modes.push({value:''})"
              >
              <v-icon>mdi-plus-circle</v-icon>
              </v-btn>
            </v-col>
            <v-col md="2" v-else>
              <v-btn
                icon
                color="red"
                large
                @click="access_modes.splice(index, 1)"
              >
              <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>

          <v-select
            v-model="storage_class_name"
            :items="storageclasses"
            label="Storage Class name"
          ></v-select>
          <v-row>
            <v-col md="10">
              <v-text-field v-model="size" label="Size" :rules="[rules.required]"> </v-text-field>
            </v-col>
            <v-col md="2">
              <v-select
                v-model="size_type"
                :items="size_items"
                label="Unit"
              ></v-select>
            </v-col>
          </v-row>
          <v-row justify="end">
            <v-col md="2">
              <v-btn @click="emit_event" color="error" type="button">
                Cancel
              </v-btn>
            </v-col>
            <v-col md="2">
              <v-btn color="success" type="submit"> Submit </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </v-overlay>
</template>

<script>
export default {
  name: 'PVCModal',
  props: { overlay: Boolean, namespace: String },
  data () {
    return {
      name: '',
      access_modes: [{ value:'' }],
      access_modes_items: ['ReadWriteOnce', 'ReadOnlyMany', 'ReadWriteMany'],
      storage_class_name: '(default)',
      size: '',
      size_type: 'Gi',
      size_items: ['Ki', 'Mi', 'Gi', 'Ti'],
      rules: {
        required: value => !!value || 'Required.'
      }
    }
  },
  computed: {
    storageclasses () {
      return this.$store.getters['pvcs/get_storageclasses']
    }
  },
  methods: {
    async post_pvc (e) {
      e.preventDefault()
      let data = {
        name: this.name,
        access_modes: this.access_modes.map(mode => mode.value),
        storage_class_name: this.storage_class_name === '(default)' ? '' : this.storage_class_name,
        size: this.size + this.size_type
      }
      this.$store.dispatch('pvcs/create_pvc', data)
      this.emit_event()
    },
    emit_event () {
      this.$emit('close', false)
    }
  },
  mounted () {
    if (this.storageclasses.length === 0) {
      this.$store.dispatch('pvcs/request_storageclasses')
    }
  }
}
</script>

<style scoped>
.modal {
  width: 50vw;
}
</style>
