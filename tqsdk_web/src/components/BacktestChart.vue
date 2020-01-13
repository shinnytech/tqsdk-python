<template>
  <div class="backtest-report">
      <!-- 回测资金曲线 -->
      <e-chart ref="echart" height="200px" :width="width+'px'" :path-option="defaultOption">
      </e-chart>
  </div>
</template>

<script>
  import moment from 'moment'
  import EChart from '@/components/charts/echart'
  import { FormatPrice } from '@/utils/formatter'
  export default {
    components: {
      EChart
    },
    data () {
      return {

        daily_yield: [],
        defaultOption: [
          ['grid.top', '16px'],
          ['grid.left', '10px'],
          ['grid.bottom', '0px'],
          ['grid.right', '16px'],
          ['series[0]', {
            type: 'line',
            encode: {
              x: 'datetime',
              y: ['balance']
            },
            smooth: false,
            showAllSymbol: true,
            areaStyle: {}
          }],
          ['yAxis.show', true],
          ['yAxis.type', 'value'],
          ['yAxis.axisLabel', {
            show: true,
            formatter: function (value, index) {
              return value.toFixed(2)
            },
            color: '#333333'
          }],
          ['yAxis.splitLine', {
            show: true
          }],
          ['xAxis.show', true],
          ['xAxis.type', 'time'],
          ['xAxis.axisLabel', {
            show: true,
            color: '#333333'
          }],
          ['xAxis.splitLine', {
            show: true
          }],
          ['xAxis.boundaryGap', false],
          ['tooltip', {
            trigger: 'axis',
            triggerOn: 'mousemove|click'
          }]
        ]
      }
    },
    props: {
      height: Number,
      width: Number
    },
    methods: {
    },
    mounted () {
      let self = this
      this.$tqsdk.on('rtn_data', function() {
        let snapshots = self.$tqsdk.get_by_path(['snapshots'])
        let chartData = []
        for (let dt in snapshots) {
          if (dt > self.$store.state.end_dt) continue
          chartData.push([Number.parseInt(dt / 1e6), snapshots[dt].accounts.CNY.balance])
        }
        self.$refs.echart.update({
              dataset: {
                source: chartData
              }
            })
      })
    }
  }
</script>

<style lang="scss">
  .backtest-report {
    padding-left: 5px;
  }
</style>
