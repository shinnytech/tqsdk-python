module.exports = {
  lintOnSave: false,
  productionSourceMap: false,
  chainWebpack: config => {
    if(config.plugins.has('extract-css')) {
      const extractCSSPlugin = config.plugin('extract-css')
      extractCSSPlugin && extractCSSPlugin.tap(() => [{
        filename: '[name].[contenthash:8].css',
        chunkFilename: '[name].[contenthash:8].css'
      }])
    }
  },
  configureWebpack: {
    output: {
      filename: '[name].[chunkhash:8].js',
      chunkFilename: '[name].[chunkhash:8].js'
    }
  }
}
