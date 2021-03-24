<template>
  <v-card class="p-4">
    <v-form @submit="user_form">
      <v-row>
        <v-col>First Name</v-col>
        <v-col>{{ current_user["firstname"] }}</v-col>
      </v-row>
      <v-row>
        <v-col>Last Name</v-col>
        <v-col>{{ current_user["name"] }}</v-col>
      </v-row>
      <v-row>
        <v-col>User Groups</v-col>
        <v-col>
          <span v-for="group in user_groups" :key="group.name">
            {{ group.name }} |
          </span>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          Primary eMail
          <!-- {{ current_user }} -->
          <!-- {{ user_groups }} -->
        </v-col>
        <v-col>
          <v-select
            dense
            solo
            :items="current_user['all_emails']"
            :label="current_user['primary_email']"
            v-model="selected_email"
          ></v-select>
        </v-col>
      </v-row>
      <v-row>
        <v-col> Namespaces shown </v-col>
        <v-col>
          <!-- <v-checkbox v-for="(namespace, i) in [current_user['k8s_namespace']]" color="green" :key=i :label="namespace" :value="namespace" v-model="selected_namespace"></v-checkbox> -->
          <v-select
            dense
            solo
            v-model="selected_namespace"
            :items="current_user['namespace_names']"
            :label="current_user['namespace_names'].join(', ')"
            multiple
          ></v-select>
        </v-col>
      </v-row>
      <v-row>
        <v-spacer />
        <v-col sm="2">
          <v-btn class="btn" color="#9f3838" @click="cancel"
            >cancel</v-btn
          ></v-col
        >
        <v-col sm="2">
          <v-btn class="btn" color="#689F38" type="submit">save</v-btn></v-col
        >
      </v-row>
    </v-form>
  </v-card>
</template>

<script>
export default {
  name: 'Profile',
  data () {
    return {
      selected_namespace: [],
      selected_email: ''
    }
  },
  computed: {
    current_user () { return this.$store.getters['users/get_user'] },
    user_groups () { return this.$store.getters['users/get_groups'] }
  },
  methods: {
    cancel () {
      this.$router.push({ name: 'Kubeportal' })
    },
    request_groups () {
      if (this.user_groups.length === 0) {
        this.$store.dispatch('users/request_groups')
      }
    },
    user_form (e) {
      e.preventDefault()
      const data = {
        firstname: this.current_user['firstname'],
        name: this.current_user['name']
      }
      if (this.selected_namespace.length !== 0) {
        console.log('NAMESPACE', this.selected_namespace)
        data['k8s_namespace'] = this.selected_namespace[0]
      }
      if (this.selected_email) {
        console.log('EMAIL', this.selected_email)
        data['primary_email'] = this.selected_email
      }
      this.$store.dispatch('users/update_user', data)
    }
  },
  mounted () {
    this.request_groups()
  }
}
</script>

<style scoped >
  .btn{
    color: floralwhite;
  }
</style>
