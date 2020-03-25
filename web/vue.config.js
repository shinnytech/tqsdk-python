module.exports = {
  outputDir: '../tqsdk/web',
  publicPath: process.env.NODE_ENV === 'production' ? 'web/' : '/',
  lintOnSave: false,
  productionSourceMap: false,
  chainWebpack: config => {
    if (process.env.NODE_ENV ===  'production') {
      config.optimization.minimizer('terser').tap((args) => {
        args[0].terserOptions.compress.drop_console = true
        return args
      })
    }
  },
  configureWebpack: {}
}
