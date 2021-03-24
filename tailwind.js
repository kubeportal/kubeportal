module.exports = {
  purge: [
    "./pages/**/*.vue", 
    "./components/**/*.vue", 
    "./plugins/**/*.vue",
    "./static/**/*.vue",
    "./store/**/*.vue"
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#319795', // teal-600
        'primary-light': '#38b2ac', // teal-500
        'primary-active': '#4fd1c5' // teal-400
      }
    }
  },
  variants: {},
  plugins: []
}
