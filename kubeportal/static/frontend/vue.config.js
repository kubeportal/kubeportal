const path = require("path");
const webpack = require('webpack');

module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? '/static/frontend/' : 'http://127.0.0.1:8086',
  outputDir: path.resolve(__dirname, "../frontend_dist"),
  indexPath: '../../templates/vue-generated.html',

  configureWebpack: {
    performance: { hints: false },
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
  },

  chainWebpack: config => {
      /*
      Check for explanations: https://github.com/EugeneDae/django-vue-cli-webpack-demo
      */
      config.devServer
          .writeToDisk(filePath => filePath.endsWith('index.html'));
  }
}
