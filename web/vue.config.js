module.exports = {
  pages: {
    index: {
      entry: 'src/main.js',
      template: 'public/index.html',
      filename: 'index.html',
      // chunks to include on this page, by default includes extracted common chunks and vendor chunks.
      chunks: ['chunk-vendors', 'chunk-common', 'index']
    }
  },
  lintOnSave: false,
  productionSourceMap: false,
  chainWebpack: config => {
    if(process.env.NODE_ENV ===  'production' && config.plugins.has('extract-css')) {
      const extractCSSPlugin = config.plugin('extract-css')
      extractCSSPlugin && extractCSSPlugin.tap(() => [{
        filename: '[name].[contenthash:8].css',
        chunkFilename: '[name].[contenthash:8].css'
      }])
    }
  },
  configureWebpack: {
    // output: {
    //   filename: '[name].[chunkhash:8].js',
    //   chunkFilename: '[name].[chunkhash:8].js'
    // },
    optimization: {
      splitChunks: {
        chunks: 'all'
        // minSize: 10000,
        // maxSize: 250000,
      }
    }
  }
}
