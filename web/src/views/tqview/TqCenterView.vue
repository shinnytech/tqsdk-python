<template>
    <div class="tq-center-view">
        <!-- 上侧工具条 -->
        <tq-layout-area :width="width"
                        :height="topHeight"
                        :otherStyle="{backgroundColor: '#FEFEFE'}">
            <tq-layout-area :width="topHeight" :height="topHeight">
                <img class="logo" alt="Tianqin" src="@/assets/logo.png"
                     :style="{padding: '4px',
                          width: topHeight + 'px',
                          height: topHeight + 'px'}">
            </tq-layout-area>
            <tq-layout-area :width="300" :height="topHeight" :left="topHeight" :style="{paddingTop: '6px'}">
                <tq-chart-tool @on-change-duration="onChangeDuration"></tq-chart-tool>
            </tq-layout-area>
            <tq-layout-area :width="120" :height="topHeight" :left="topHeight + 300" :style="{paddingTop: '6px'}">
                <ButtonGroup size="small" shape="circle">
                    <Button @click="switchSymbol('pre')">
                        <Icon type="ios-arrow-back"></Icon>
                        pre
                    </Button>
                    <Button @click="switchSymbol('next')">
                        next
                        <Icon type="ios-arrow-forward"></Icon>
                    </Button>
                </ButtonGroup>
            </tq-layout-area>
        </tq-layout-area>
        <!-- 中间 K线图 -->
        <tq-layout-area :top="topHeight"
                        :width="width"
                        :height="centerHeight"
                        :otherStyle="{backgroundColor: '#FEFEFE'}">
            <tq-chart-components
                    :instrumentId="instrumentId"
                    :duration="duration"
                    :height="centerHeight"
                    :width="width"
                    :theme="theme"
            ></tq-chart-components>
        </tq-layout-area>
        <!-- 下侧面板 -->
        <tq-layout-area verticalAlign="bottom"
                        :width="width"
                        :height="bottomHeight"
                        :otherStyle="{
                          backgroundColor: '#FEFEFE',
                          boxShadow: showBottomShadow ? '0px -3px 4px -1px #AFAFAF' : ''}">
            <div class="bottom-area-handle" @mousedown="handleMousedown"></div>
            <logs></logs>
        </tq-layout-area>
    </div>
</template>
<script>
    import Vue from 'vue'
  import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
    import TqChartTool from '@/components/charts/TqChartTool.vue'
    import TqChartComponents from '@/components/charts/TqChartComponents'
    import Logs from '@/components/logs'
  import {on, off} from '@/utils/dom'
  const Thickness = 4
  export default {
    name: 'tq-center-view',
    components: {
      TqLayoutArea,
      TqChartComponents,
      TqChartTool,
      Logs
    },
    props: {
      width: Number,
    },
    data () {
      let defaultTopHeight = 38
      let _bottomHeightMin = 38
      return {
        topHeight: defaultTopHeight,
        centerHeight: 400,
        centerHeightMin: 200, // 中间高度最小值
        bottomHeightMin: _bottomHeightMin + Thickness, // 底部高度最小值
        bottomYOffset: defaultTopHeight + 400,
        bottomYOffsetMin: defaultTopHeight,
        bottomYOffsetMax: this.$root.windowHeight - _bottomHeightMin,
        bottomHeight: this.$root.windowHeight - defaultTopHeight - 400 - Thickness,
        isMoving: false,
        showBottomShadow: false,

        instrumentId: '',
        duration: 60000000000,
        subscribed: [],
        action: 'run',
        theme: 'light'
      }
    },
    methods: {
      onResize () {
        this.bottomYOffsetMax = this.$root.windowHeight - this.bottomTabsHeight
        this.computeLayouts()
      },
      computeLayouts () {
        let bottomHeight = this.$root.windowHeight - this.bottomYOffset
        if (bottomHeight <= this.bottomHeightMin) {
          bottomHeight = this.bottomHeightMin
          this.bottomYOffset = this.$root.windowHeight - bottomHeight
        }
        this.bottomHeight = bottomHeight - Thickness
        let centerAreaHeight = this.$root.windowHeight - this.topHeight - bottomHeight
        this.centerHeight = Math.max(centerAreaHeight, this.centerHeightMin)
      },
      handleMousedown (e) {
        this.isMoving = true
        on(document, 'mousemove', this.handleMove)
        on(document, 'mouseup', this.handleUp)
      },
      handleMove (e) {
        let pageOffset = e.pageY
        if (pageOffset >= this.bottomYOffsetMax || pageOffset <= this.bottomYOffsetMin) return
        this.showBottomShadow = pageOffset < this.centerHeightMin + this.topHeight
        this.bottomYOffset = pageOffset
        this.computeLayouts()
      },
      handleUp () {
        this.isMoving = false
        off(document, 'mousemove', this.handleMove)
        off(document, 'mouseup', this.handleUp)
      },
      onChangeDuration(d) {
        let [originStr, num, unit] = d.match(/^([0-9]+)([a-zA-Z]+)$/)
        if (unit === 'day') {
          this.duration = 60 * 1e9
        } else if (unit === 'm') {
          this.duration = num * 60 * 1e9
        } else if (unit === 'h') {
          this.duration = num * 3600 * 1e9
        } else if (unit === 'd') {
          this.duration = num * 24 * 3600 * 1e9
        }
      },
      switchSymbol(d){
        let i = this.subscribedIndex
        if (d === 'pre') {
          i = i === 0 ? this.subscribed.length - 1 : i-1
        } else if (d === 'next') {
          i = i === (this.subscribed.length - 1) ? 0 : i+1
        }
        if (i !== this.subscribedIndex){
          this.subscribedIndex = i
          this.instrumentId = Array.isArray(this.subscribed[i].symbol) ? this.subscribed[i].symbol[0] : this.subscribed[i].symbol
          this.duration = this.subscribed[i].dur_nano || 60 * 1e9
        }
      }
    },
    created () {
      this.$eventHub.$on('window_resize', this.onResize)
      let self = this

      this.$tqsdk.on('rtn_data', function(){
        self.subscribed = self.$tqsdk.get_by_path(['subscribed'])
        if (self.subscribed && self.subscribed[0] && self.instrumentId === '') {
          self.subscribedIndex = 0
          self.instrumentId = Array.isArray(self.subscribed[0].symbol) ? self.subscribed[0].symbol[0] : self.subscribed[0].symbol
          self.duration = self.subscribed[0].dur_nano || 60 * 1e9
        }
      })
      this.$eventHub.$on('changeTheme', function (){
        self.theme = self.theme === 'light' ? 'dark' : 'light'
      })
    }
  }
</script>
<style lang="scss">

    .bottom-area-handle {
        position: absolute;
        left: 0;
        top: -3px;
        height: 7px;
        width: 100%;
        cursor: ns-resize;
    }
</style>
