<template>
    <div class="tq-top-view">
        <tq-layout-area class="left-view" :height="height" :width="chartWidth">
            <tq-layout-area :height="26" :width="300">
                <button-group-durations
                        :duration="duration"
                        @onChangeDuration="onChangeDuration"></button-group-durations>
            </tq-layout-area>
            <!-- 中间 K线图 -->
            <tq-layout-area :top="26">
                <tq-chart-components
                        :instrumentId="instrumentId"
                        :duration="duration"
                        :height="height - 26"
                        :width="chartWidth"
                        :theme="theme"
                        :mainType="mainType"
                ></tq-chart-components>
            </tq-layout-area>
        </tq-layout-area>
        <tq-layout-area class="right-view" :height="height" :width="rightWidth" horizontalAlign="right">
            <tq-layout-area v-if="$store.state.mode !== 'backtest'"
                            :height="rightClosed ? height - 35 : 160" :width="rightWidth">
                <quote-info v-if="$store.state.mode !== 'backtest'" :symbol="instrumentId" :height="rightClosed ? height - 35 : 160" :width="rightWidth"></quote-info>
            </tq-layout-area>
            <tq-layout-area :top="$store.state.mode !== 'backtest' ? 160 : 0" :height="rightClosed ? 0 : 18" :width="rightWidth"
                            :otherStyle="{
                                backgroundColor: 'lightgrey',
                                color: '#333333',
                                fontSize: '12px',
                                fontWeight: '700',
                                overflow: 'hidden'
                            }">
                订阅合约列表
            </tq-layout-area>
            <tq-layout-area :verticalAlign="'bottom'" :bottom="35"
                            :height="rightClosed ? 0 : height-($store.state.mode !== 'backtest' ? 160 : 0)-18-35"
                            :width="rightWidth" :otherStyle="{overflowY: 'scroll'}">
                <subscribed-list @onChange="onChangeSelectedSubscribed"></subscribed-list>
            </tq-layout-area>
            <tq-layout-area :verticalAlign="'bottom'" :height="35" :width="rightWidth">
                <about-us :width="rightWidth"></about-us>
            </tq-layout-area>
            <div v-if="$store.state.mode !== 'backtest'" class="right-resize-tool" @click="toggleRightClosed">
                <Icon v-if="!rightClosed" type="ios-arrow-forward" />
                <Icon v-else type="ios-arrow-back" />
            </div>
        </tq-layout-area>
    </div>
</template>
<script>
    import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
    import ButtonGroupDurations from '@/components/charts/ButtonGroupDurations.vue'
    import TqChartComponents from '@/components/charts/TqChartComponents'
    import SubscribedList from '@/components/SubscribedList.vue'
    import QuoteInfo from '@/components/QuoteInfo.vue'
    import AboutUs from '@/components/AboutUs.vue'
  import {on, off} from '@/utils/dom'
  const Thickness = 4
  export default {
    name: 'tq-top-view',
    components: {
      TqLayoutArea,
      TqChartComponents,
      ButtonGroupDurations,
      QuoteInfo,
      SubscribedList,
      AboutUs
    },
    props: {
      width: Number,
      height: Number,
    },
    data () {
      let rightOpenedWidth = 240
      let rightClosedWidth = 80
      return {
        rightClosed: false,
        rightOpenedWidth: rightOpenedWidth,
        rightClosedWidth: rightClosedWidth,
        instrumentId: '',
        duration: 60000000000,
        theme: 'light',
        mainType: 'candle'
      }
    },
    computed: {
      chartWidth () {
        let chartWidth = this.$root.windowWidth - (this.rightClosed ? this.rightClosedWidth : this.rightOpenedWidth)
        return Math.max(chartWidth, 400) // 左侧图表宽度最少 400
      },
      rightWidth () {
        return (this.rightClosed ? this.rightClosedWidth : this.rightOpenedWidth) - 4
      }
    },
    methods: {
      toggleRightClosed () {
        this.rightClosed = !this.rightClosed
      },
      onChangeDuration(dur, per) {
        this.duration = dur
        if (per === '分时') {
          this.mainType = 'close'
        } else {
          this.mainType = 'candle'
        }
      },
      onChangeSelectedSubscribed(symbol, dur_nano){
        this.instrumentId = symbol
        this.duration = dur_nano ? dur_nano : 60000000000
        this.mainType = 'candle'
      }
    },
    created () {
      let self = this
      this.$tqsdk.on('rtn_data', function(){
        self.subscribed = self.$tqsdk.get_by_path(['subscribed'])
        if (self.subscribed && self.subscribed[0] && self.instrumentId === '') {
          self.subscribedIndex = 0
          self.instrumentId = Array.isArray(self.subscribed[0].symbol) ? self.subscribed[0].symbol[0] : self.subscribed[0].symbol
          self.duration = self.subscribed[0].dur_nano || 60 * 1e9
        }
      })
    }
  }
</script>
<style lang="scss">
    .tq-top-view {
        .left-view {
            background-color: #FFFFFF;
        }
        .right-view {
            background-color: #FFFFFF;
        }

        .right-resize-tool {
            position: absolute;
            bottom: 20%;
            left: -4px;
            height: 26px;
            width: 8px;
            color: #A0A0A0;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            background-color: #FEFEFE;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 10px;
        }
    }
</style>
