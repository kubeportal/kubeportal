const webpack = require('webpack')
module.exports = {
  configureWebpack: {
    performance: { hints: false },
    plugins: [
      new webpack.DefinePlugin({
        'process.env.VUE_APP_BASE_URL': JSON.stringify(process.env.VUE_APP_BASE_URL)
      })
    ]
  },
  devServer: {
    overlay: {
      warnings: false,
      errors: false
    },
    compress: false,
    disableHostCheck: true,
    port: 8086,
    host: '0.0.0.0'
  }
}
