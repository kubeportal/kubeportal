<template>
    <v-card class="logincard">
      <v-form @submit.prevent="login">
        <v-card-title>
          <v-icon class="icon ml-3 mb-7 mt-4">mdi-login-variant</v-icon>
          <span class="mb-7 mt-4">{{cluster_branding}}</span>
        </v-card-title>
        <v-card-text v-if="loading">
          <RequestSpinner />
        </v-card-text>
        <v-card-text v-else>
          <v-alert class="alert" dense outlined type="error" v-if="is_authenticated === false">Login Failed.</v-alert>
          <v-card-text>
            <v-text-field label="user name" v-model="username" required></v-text-field>
            <v-text-field type="password" v-model="password" label="password" required></v-text-field>
          </v-card-text>
          <div class="row">
            <v-btn type="submit" color="#689F38" class="signin">Sign In</v-btn>
          </div>
          <v-row>
            <p class="my-4 text">or</p>
          </v-row>
          <v-row>
            <v-btn class="signin" color="#689F38" @click="signInWithGoogle" >
              <v-icon  white small left>mdi-google</v-icon>
              Continue with Google
            </v-btn>
          </v-row>
        </v-card-text>
      </v-form>
    </v-card>
</template>

<script>
import RequestSpinner from '../components/RequestSpinner'
export default {
  name: 'Login',
  components: { RequestSpinner },
  data () {
    return {
      is_authenticated: '',
      username: '',
      password: '',
      loading: false
    }
  },
  computed: {
    cluster_branding () {
      return this.$store.getters['api/get_branding']
    }
  },
  methods: {
    async login () {
      this.loading = true
      const request_body = { username: this.username, password: this.password }
      const response = await this.$store.dispatch('users/authorize_user', request_body)
      // console.log('LOGIN', response)
      this.handle_login_response(response)
    },
    async signInWithGoogle () {
      let googleUser = await this.$gAuth.signIn()
      if (!googleUser) {
        this.is_authenticated = false
        return undefined
      }
      const auth_response = googleUser.getAuthResponse()
      // console.log('getAuthResponse', this.$gAuth.GoogleAuth.currentUser.get().getAuthResponse())
      const response = await this.$store.dispatch('users/authorize_google_user', auth_response)
      this.handle_login_response(response)
    },
    async handle_login_response (response) {
      if(!response) {
        this.loading = false
        this.is_authenticated = false
      } else if (response.status === 200) {
        this.is_authenticated = true
        this.$router.push({ name: 'Kubeportal' })
      }
    }
  },
  async mounted () {
    this.$store.dispatch('api/get_basic_api_information')
  }
}
</script>

<style scoped lang="scss">
  .logincard {
    margin: 5vh auto;
    width: 25%;
    min-width: 300px;
  }
  .signin {
    color: floralwhite;
    margin: auto;
    width: 100%
  }
  .text, .row {
    margin: auto;
  }
  .card-header {
    margin-bottom: 1vh;
  }
  .alert {
    margin: 1vw 0 1vw 0;
  }
</style>
