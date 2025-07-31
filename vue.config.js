const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // Production build settings
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  
  // Output directory
  outputDir: 'dist',
  
  // Assets directory
  assetsDir: 'static',
  
  // Development server settings
  devServer: {
    port: 8080,
    open: true,
    host: '0.0.0.0',
    https: false,
    hot: true,
    historyApiFallback: true
  },
  
  // Build optimization
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            name: 'chunk-vendors',
            test: /[\\/]node_modules[\\/]/,
            priority: 10,
            chunks: 'initial'
          },
          plotly: {
            name: 'chunk-plotly',
            test: /[\\/]node_modules[\\/]plotly\.js/,
            priority: 20,
            chunks: 'all'
          }
        }
      }
    }
  },
  
  // CSS settings
  css: {
    extract: process.env.NODE_ENV === 'production',
    sourceMap: process.env.NODE_ENV !== 'production'
  },
  
  // PWA settings (if needed)
  pwa: {
    name: 'PCM Trend Analysis Dashboard',
    themeColor: '#667eea',
    msTileColor: '#667eea',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'default',
    workboxPluginMode: 'GenerateSW',
    workboxOptions: {
      skipWaiting: true,
      clientsClaim: true
    }
  },
  
  // Linting settings
  lintOnSave: process.env.NODE_ENV !== 'production',
  
  // Production source maps
  productionSourceMap: false
}) 
