<template>
  <div class="tq-home">
      <div class="layout-area layout-area-center"
            :style="{width: centerAreaWidth + 'px', left: '0px'}">
          <tq-center-view :width="centerAreaWidth"></tq-center-view>
      </div>
      <div class="layout-area layout-area-right"
           :style="{width: rightArea.width + 'px'}">
      </div>
  </div>
</template>

<script>
// @ is an alias to /src
import TqLeftView from './tqview/TqLeftView.vue'
import TqCenterView from './tqview/TqCenterView.vue'

const DefaultBarWidth = 38
const Thickness = 4

export default {
  name: 'tq-home',
  components: {
    TqLeftView,
    TqCenterView
  },
  data () {
    return {
      leftAreaWidth: DefaultBarWidth,
      centerAreaLeft: DefaultBarWidth + Thickness,
      rightArea: {
        width: DefaultBarWidth,
        pagesWidth: 300,
        toolsBarWidth: DefaultBarWidth
      }
    }
  },
  computed : {
    centerAreaWidth () {
      return this.$root.windowWidth - this.leftAreaWidth - Thickness
      // return this.$root.windowWidth
    }
  }
}
</script>

<style lang="scss">
    .tq-home {
        position: relative;
        width: 100%;
        height: 100%;
        background-color: #E0E0E0;
        .layout-area {
            position: absolute;
            height: 100%;
            &.layout-area-right{
                top: 0px;
                right: 0px;
            }
        }
    }
</style>
