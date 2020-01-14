import Vue from 'vue'

import TqChart from 'tqchart'
import 'tqchart/dist/tqchart.css'
const CHART_ID = 'web_chart'
const CHART_ID_FOCUS = 'web_chart_focus'
let klines = null
let chartInstance = null

const RevertDtToId = function (dt) {
  const [l, r] = [chartInstance.range.leftId, chartInstance.range.rightId]
  if (!klines || !klines.data || !klines.data[l] || dt < klines.data[l].datetime) return null
  // 可能整个图的right_id 大于 klines.last_id， 造成 klines.data[r].datetime 是 undefined
  const rightId = klines.data[r] ? r : klines.last_id
  if (dt <= klines.data[rightId].datetime) {
    for (let i = l; i < rightId + 1; i++) {
      if (dt - klines.data[i].datetime <= 0) return i
    }
  }
  return null
}

const GetDatetimeRange = function () {
  let [l, r] = [chartInstance.range.leftId, chartInstance.range.rightId]
  r = klines.data[r] ? r : klines.last_id
  if (!klines.data[l] || !klines.data[r]) return [-1, -1]
  return [klines.data[l].datetime, klines.data[r].datetime]
}

export default {
  name: 'tq-chart-components',
  data () {
    return {
      id: 'TQ-CHART',
      action: 'run'
    }
  },
  props: {
    instrumentId: {
      type: String,
      default: 'TQ.m@SHFE.au'
    },
    duration: {
      type: Number,
      default: 60 * 1e9
    },
    width: Number,
    height: Number,
    theme: {
      type: String,
      default: 'light'
    },
    mainType: {
      type: String,
      default: 'candle'
    }
  },
  render (h) {
    const data = {
      class: {
        "theme-light": this.theme === 'light',
        "theme-dark": this.theme === 'dark'
      },
      attrs: {
        id: this.id
      }
    }
    return h('div', data)
  },
  watch: {
    instrumentId: function(newVal, oldVal) {
      chartInstance.removeMarkAll()
      this.$nextTick(this.updateTqChart)
    },
    duration: function(newVal, oldVal) {
      chartInstance.removeMarkAll()
      this.$nextTick(this.updateTqChart)
    },
    width: function(newVal, oldVal) {
      if (chartInstance) {
        chartInstance.resize({
          width: newVal,
          height: this.height
        })
      }
    },
    height: function(newVal, oldVal) {
      if (chartInstance) {
        chartInstance.resize({
          width: this.width,
          height: newVal
        })
      }
    },
    mainType: function(newVal, oldVal) {
      chartInstance.removeMarkAll()
      this.$nextTick(this.updateTqChart)
    }
  },
  created(){
    klines = this.$tqsdk.get({
      name: 'klines',
      symbol: this.instrumentId,
      duration: this.duration
    })
    chartInstance = new TqChart({
      id: this.id,
      instrumentId: this.instrumentId,
      duration: this.duration,
      height: this.height,
      width: this.width,
      mainType: this.mainType,
      mainSeries: klines
    })

    let self = this
    chartInstance.on('showRangeChanged', function(range){
      if (range.rightId === -1 || range.leftId === -1) return
      if (self.mainType === 'close') {
        // 请求 n 天的数据
        let oneDay = 3600 * 24 * 1000 * 1000 * 1000
        let n = 1 // 3日日内图
        self.$tqsdk.set_chart({
          chart_id: CHART_ID,
          symbol: self.instrumentId,
          duration: self.duration,
          trading_day_start: oneDay * ( 1 - n),
          trading_day_count: oneDay * n
        })
      } else if (self.mainType === 'candle') {
        // 请求 range 前后的数据
        let realViewWidth = range.rightId - range.leftId
        self.$tqsdk.set_chart({
          chart_id: CHART_ID,
          symbol: self.instrumentId,
          duration: self.duration,
          left_kline_id: Math.max(range.leftId - realViewWidth, 0),
          view_width: realViewWidth * 3
        })
      }
    })
  },
  mounted(){
    chartInstance.init()
    let self = this
    this.$tqsdk.on("rtn_data", function(){
      // 更新持仓线
      self.updatePositionLine()
      // 检查新增的 trade 添加
      self.updateTrades()
      // 更新绘图数据
      self.updateTqSdkChartData()
      // 更新持仓矩形
      self.updatePositionRect()
      // 如果是回测就定位到某个 trade 的位置去，只定位一次
      if (self.action === 'run' && self.$tqsdk.get_by_path(['action', 'mode']) === 'backtest') {
        // 得到某一个 trade, 定位到那里去
        let account_id = self.$store.state.account_id
        if (account_id) {
          let trades = self.$tqsdk.get({
            name: 'trades',
            user_id: account_id
          })
          for(let trade_id in trades){
            let trade = trades[trade_id]
            if (chartInstance && chartInstance.symbol && chartInstance.duration) {
              self.$tqsdk.set_chart({
                chart_id: CHART_ID_FOCUS,
                symbol: chartInstance.symbol,
                duration: chartInstance.duration,
                view_width: chartInstance.bar.barNumbers,
                focus_datetime: trade.trade_date_time, // 日线及以上周期是交易日，其他周期是时间，UnixNano 北京时间
                focus_position: Math.floor(chartInstance.bar.barNumbers / 2) // 指定K线位于屏幕的相对位置,0 表示位于最左端
              })
              self.action = 'backtest'
            }
            break
          }
        }
      }
      // 更新 chart
      let chartFoucs = self.$tqsdk.get_by_path(['charts', CHART_ID_FOCUS])
      if (chartFoucs && !chartFoucs.more_data && chartFoucs.left_id && chartFoucs.right_id) {
        let [leftId, rightId] = [chartFoucs.left_id, chartFoucs.right_id]
        chartInstance.setRange(leftId, rightId)
        chartInstance.addHighlightBar('movetoid', leftId + Math.round(chartInstance.bar.barNumbers / 2 - 2))
        self.$tqsdk.set_chart({
          chart_id: CHART_ID_FOCUS,
          symbol: '',
          duration: chartInstance.duration,
          view_width: 0
        })
      } else {
        let chart = self.$tqsdk.get_by_path(['charts', CHART_ID])
        if (self.mainType === 'close' && chart && !chart.more_data && chart.left_id && chart.right_id) {
          let [leftId, rightId] = [chart.left_id, chart.right_id]
          chartInstance.setRange(leftId, rightId)
        }
        if (chart && !chart.more_data && self.$tqsdk.is_changed(klines)) {
          chartInstance.draw()
        }
      }
    })
    this.$eventHub.$on('moveChartToDt', function (datetime){
      this.$tqsdk.set_chart({
        chart_id: CHART_ID_FOCUS,
        symbol: chartInstance.symbol,
        duration: chartInstance.duration,
        view_width: chartInstance.bar.barNumbers,
        focus_datetime: datetime, // 日线及以上周期是交易日，其他周期是时间，UnixNano 北京时间
        focus_position: Math.floor(chartInstance.bar.barNumbers / 2) // 指定K线位于屏幕的相对位置,0 表示位于最左端
      })
    })
  },
  methods: {
    updateTqChart () {
      // 订阅初始 K 线数据
      this.$tqsdk.set_chart({
        chart_id: CHART_ID,
        symbol: this.instrumentId,
        duration: this.duration,
        view_width: 1000
      })
      klines = this.$tqsdk.get({
        name: 'klines',
        symbol: this.instrumentId,
        duration: this.duration
      })

      if (chartInstance) {
        let quote = this.$tqsdk.get_quote(this.instrumentId)
        chartInstance.setMainSeries(this.instrumentId, this.duration, klines, this.mainType)
        chartInstance.price_decs = quote.price_decs
        this.$nextTick(function () {
          this.updateTqSdkChartData()
          this.updateTrades(true)
          this.updatePositionRect(true)
        })
      }
    },
    updateTqSdkChartData () {
      let chartDatas = this.$tqsdk.get_by_path(['draw_chart_datas', chartInstance.symbol, chartInstance.duration])
      if (chartDatas) {
        for (let seriesId in chartDatas) {
          chartInstance.addSeries(seriesId, chartDatas[seriesId])
        }
      }
    },
    updatePositionLine (snapshot) { // 持仓线
      let account_id = this.$store.state.account_id
      if (!account_id) return
      let pos = this.$tqsdk.get({
        name: 'position',
        user_id: account_id,
        symbol: chartInstance.symbol
      })
      if (pos && pos.volume_long > 0) {
        chartInstance.addMark({
          id: 'pos_long',
          type: 'line',
          boardId: 'main',
          yAlign: 'right',
          xPos1: 0,
          xPos2: chartInstance.innerWidth,
          y1: pos.open_price_long,
          y2: pos.open_price_long,
          stroke: 'red',
          text: `多仓${pos.volume_long}手@${pos.open_price_long}`
        })
      } else {
        chartInstance.removeMark('pos_long')
      }
      if (pos && pos.volume_short > 0) {
        chartInstance.addMark({
          id: 'pos_short',
          type: 'line',
          boardId: 'main',
          yAlign: 'right',
          xPos1: 0,
          xPos2: chartInstance.innerWidth,
          y1: pos.open_price_short,
          y2: pos.open_price_short,
          stroke: 'green',
          text: `空仓${pos.volume_short}手@${pos.open_price_short}`
        })
      } else {
        chartInstance.removeMark('pos_short')
      }
    },
    updateTrades (updateAll) { // 成交标记
      let account_id = this.$store.state.account_id
      if (!account_id) return
      let trades =this.$tqsdk.get({
        name: 'trades',
        user_id: account_id
      })
      for(let trade_id in trades){
        let trade = trades[trade_id]
        if (updateAll) {
          if (trade.volume > 0 && trade.symbol === chartInstance.symbol) {
            chartInstance.addTradeArrow(trade_id, trade)
          }
        } else if (trade._epoch === this.$tqsdk.dm._epoch && trade.volume > 0 && trade.symbol === chartInstance.symbol) {
          chartInstance.addTradeArrow(trade_id, trade)
        }
      }
    },
    updatePositionRect (updateAll) { // 持仓记录
      let snapshots = this.$tqsdk.get_by_path(['snapshots'])
      for(let dt in snapshots){
        let snapshot = snapshots[dt]
        if (updateAll) {
          if (snapshot.positions && snapshot.positions.hasOwnProperty(chartInstance.symbol)) {
            chartInstance.addPositionRecord(dt, snapshot.positions[chartInstance.symbol])
          }
        } else if (snapshot._epoch === this.$tqsdk.dm._epoch && snapshot.positions && snapshot.positions.hasOwnProperty(chartInstance.symbol) ) {
          chartInstance.addPositionRecord(dt, snapshot.positions[chartInstance.symbol])
        }
      }
    }

  }
}

  // {
  //    aid: set_chart, # 请求图表数据
  //    chart_id: string, # 图表id,服务器只会维护每个id收到的最后一个请求的数据
  //    ins_list: string, 1024 max # 填空表示删除该图表，多个合约以逗号分割，第一个合约是主合约，所有id都是以主合约为准
  //    duration: int # 周期，单位ns, tick:0, 日线: 3600 * 24 * 1000 * 1000 * 1000

  //    # 下面有4种模式

  //    # a: 请求最新N个数据，并保持滚动(新K线生成会移动图表)
  //    view_width: int # 图表宽度

  //    # b: 指定一个K线id，向右请求N个数据
  //    view_width: int # 图表宽度
  //    left_kline_id: int, # 屏幕最左端的K线id

  //    # c: 使得指定日期的K线位于屏幕第M个柱子的位置
  //    view_width: int # 图表宽度
  //    focus_datetime: int # 日线及以上周期是交易日，其他周期是时间，UnixNano 北京时间
  //    focus_position: int, # 指定K线位于屏幕的相对位置,0 表示位于最左端

  //    # d: 指定交易日，返回对应的数据
  //    trading_day_start: int # 大于0:交易日的UnixNano 北京时间 0:当前交易日 小于0:前N个交易日 eg: -3600 * 24 * 1000 * 1000 * 1000 表示上一个交易日
  //    trading_day_count: int # 请求交易日天数 3600 * 24 * 1000 * 1000 * 1000 表示1天
  //  }

