import Vue from 'vue'
import TqChart from 'tqchart'
import 'tqchart/dist/tqchart.css'
const CHART_ID = 'web_chart'
const CHART_ID_FOCUS = 'web_chart_focus'
let klines = null
let chartInstance = null

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
      symbol: this.instrumentId,
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
          duration: 60 * 1e9,
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
          let trades = self.$tqsdk.getByPath(['trade', account_id, 'trades'])
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
        if (self.mainType === 'close' && chart && !chart.more_data) {
          klines = self.$tqsdk.get({
            name: 'klines',
            symbol: self.instrumentId,
            duration: 60 * 1e9
          })
          if (klines && klines.trading_day_end_id > -1 && klines.trading_day_start_id > -1) {
            chartInstance.setRange(klines.trading_day_start_id, klines.trading_day_end_id)
          }
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
        let quote = this.$tqsdk.getQuote(this.instrumentId)
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
      if (chartDatas && chartDatas._epoch === this.$tqsdk.dm._epoch) {
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
          if (trade.volume > 0 && (trade.exchange_id + '.' + trade.instrument_id) === chartInstance.symbol) {
            chartInstance.addTradeArrow(trade_id, trade)
          }
        } else if (trade.volume > 0 && (trade.exchange_id + '.' + trade.instrument_id) === chartInstance.symbol) {
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
