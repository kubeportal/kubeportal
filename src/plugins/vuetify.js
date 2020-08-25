import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader
import Vue from 'vue'
import Vuetify from 'vuetify/lib'

const vuetify = new Vuetify({
  theme: {
    themes: {
      light: {
        primary: '#424242',
        secondary: '#b0bec5',
        anchor: '#8c9eff'
      },
      dark: {
        primary: '#36392e',
        secondary: '#606357'
      }
    }
  },
  icons: {
    iconfont: 'mdi'
  }
})
Vue.use(Vuetify)

export default vuetify
