<template>
  <div id="app">
      <tianqin></tianqin>
  </div>
</template>

<script>
    import Tianqin from '@/views/Tianqin.vue'
  export default {
    name: 'tq-app',
    components: {
      Tianqin
    },
  }
</script>

<style lang="scss">

    @import '../node_modules/view-design/dist/styles/iview.css';

    html, body {
        font-family: 'Avenir', Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        color: #4a4a4a;
        font-size: 12px;
        height: 100%!important;
        width: 100%!important;
        overflow: hidden;
    }

    #app {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        position: relative;
        display: flex;
        flex-direction: column;
        text-align: center;
        overflow: hidden;
    }
</style>
