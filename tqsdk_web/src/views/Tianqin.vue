<template>
  <div class="tq-home">
      <div class="layout-area header-container">
        <tq-header-view :height="headerHeight" :width="$root.windowWidth"></tq-header-view>
      </div>
      <div class="layout-area top-container" :style="{height:topHeight+'px'}">
        <tq-top-view :height="topHeight" :width="$root.windowWidth"></tq-top-view>
      </div>
      <div class="layout-area bottom-container" :style="{
                            height:bottomHeight+'px',
                            top: bottomYOffset+4+'px',
                            backgroundColor: '#FEFEFE',
                          boxShadow: showBottomShadow ? '0px -3px 4px -1px #AFAFAF' : ''}">
          <div class="bottom-area-handle" @mousedown="handleMousedown"></div>
          <tq-bottom-view :height="bottomHeight" :width="$root.windowWidth"></tq-bottom-view>
      </div>
  </div>
</template>

<script>
  import TqHeaderView from './tianqinViews/TqHeaderView.vue'
  import TqTopView from './tianqinViews/TqTopView.vue'
  import TqBottomView from './tianqinViews/TqBottomView.vue'
import {on, off} from '@/utils/dom'

const HeaderHeight = 38
const Thickness = 4
const BottomHeightMin = 56

export default {
  name: 'tq-home',
  components: {
    TqHeaderView,
    TqTopView,
    TqBottomView
  },
  data () {
    let defaultTopHeight = Math.max(260, Math.round(this.$root.windowHeight / 5 * 3))
    let _bottomYOffset = HeaderHeight + defaultTopHeight + Thickness
    return {
      isMoving: false,
      headerHeight: HeaderHeight,
      topHeight: defaultTopHeight,
      topHeightMin: 260, // 中间高度最小值
      bottomYOffset: _bottomYOffset,
      bottomYOffsetMin: HeaderHeight * 2,
      bottomYOffsetMax: this.$root.windowHeight - BottomHeightMin,
      bottomHeight: this.$root.windowHeight - _bottomYOffset - Thickness,
      showBottomShadow: false
    }
  },
  methods: {
    onResize () {
      this.bottomYOffsetMax = this.$root.windowHeight - BottomHeightMin
      this.computeLayouts()
    },
    handleMousedown (e) {
      this.isMoving = true
      on(document, 'mousemove', this.handleMove)
      on(document, 'mouseup', this.handleUp)
    },
    handleMove (e) {
      let pageOffset = e.pageY
      if (pageOffset >= this.bottomYOffsetMax || pageOffset <= this.bottomYOffsetMin) return
      this.bottomYOffset = pageOffset
      this.computeLayouts()
    },
    handleUp () {
      this.isMoving = false
      off(document, 'mousemove', this.handleMove)
      off(document, 'mouseup', this.handleUp)
    },
    computeLayouts() {
      let bottomHeight = this.$root.windowHeight - this.bottomYOffset
      if (bottomHeight <= BottomHeightMin) {
        bottomHeight = BottomHeightMin
        this.bottomYOffset = this.$root.windowHeight - bottomHeight
      }
      this.showBottomShadow = this.bottomYOffset < this.topHeightMin + HeaderHeight
      this.bottomHeight = bottomHeight - Thickness
      let topContainerHeight = this.$root.windowHeight - HeaderHeight - bottomHeight - Thickness
      this.topHeight = Math.max(topContainerHeight, this.topHeightMin)
    }
  },
  created() {
    this.$eventHub.$on('window_resize', this.onResize)
    this.computeLayouts()
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
            &.header-container {
                height: 38px;
                width: 100%;
                background-color: #FFFFFF;
            }
            &.top-container {
                top: 42px;
                width: 100%;
            }
            &.bottom-container {
                width: 100%;
                background-color: #FFFFFF;
                .bottom-area-handle {
                    position: absolute;
                    left: 0;
                    top: -3px;
                    height: 7px;
                    width: 100%;
                    cursor: ns-resize;
                }
            }
        }
    }
</style>
