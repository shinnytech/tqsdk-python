<template>
    <div class="backtest-info" :style="{height:height + 'px'}">
        <Row>
            <Col :span="24" v-if="init_balance === '-'" class-name="spin-container">
            <Spin fix>
                <div class="loader">
                    <svg class="circular" viewBox="25 25 50 50">
                        <circle class="path" cx="50" cy="50" r="20" fill="none" stroke-width="6" stroke-miterlimit="10"></circle>
                    </svg>
                </div>
                回测进行中
            </Spin>
            </Col>
        </Row>
        <Row >
            <Col :span="6">起始资金</Col>
            <Col :span="6">{{init_balance| toFixed(2)}}</Col>
            <Col :span="6">总收益</Col>
            <Col :span="6">{{balance - init_balance | toFixed(2)}}</Col>

            <Col :span="6">结束资金</Col>
            <Col :span="6">{{balance| toFixed(2)}}</Col>
            <Col :span="6">总收益率</Col>
            <Col :span="6">{{ror * 100 | toFixed(2)}}%</Col>


            <Col :span="6">最大回撤</Col>
            <Col :span="6">{{max_drawdown * 100 | toFixed(2)}}%</Col>
            <Col :span="6">年化收益率</Col>
            <Col :span="6">{{annual_yield * 100 | toFixed(2)}}%</Col>


            <Col :span="6">总手续费</Col>
            <Col :span="6">{{commission| toFixed(2)}}</Col>
            <Col :span="6">年化夏普率</Col>
            <Col :span="6">{{sharpe_ratio | toFixed(2)}}</Col>

            <Col :span="6">胜率</Col>
            <Col :span="6">{{winning_rate * 100| toFixed(2)}}%</Col>
            <Col :span="6">盈亏额比</Col>
            <Col :span="6">{{profit_loss_ratio | toFixed(2)}}</Col>

            <Col :span="12" :style="{color:'#bd0000'}">天勤量化：{{getMsg(ror * 100)}}</Col>
        </Row>
    </div>
</template>
<script>
  import { FormatPrice } from '@/utils/formatter'
  export default {
    data () {
      return {
        init_balance: '-',
        balance: '-',
        ror: '-',
        annual_yield: '-',
        max_drawdown: '-',
        sharpe_ratio: '-',
        commission: '-',
        winning_rate: '-',
        profit_loss_ratio: '-'
      }
    },
    props: {
      height: Number,
      width: Number
    },
    methods: {
      getMsg: function (n) {
        if (n <= -100) {
          return '幸好是模拟账户，不然你就亏完啦'
        } else if (n <= -50) {
          return '触底反弹,与其执迷修改参数，不如改变策略思路去天勤官网策略库进修'
        } else if (n <= -20) {
          return '越挫越勇，不如去天勤量化官网策略库进修'
        } else if (n <= 0) {
          return '不要灰心，少侠重新来过'
        } else if (n <= 20) {
          return '策略看来小有所成'
        } else if (n <= 50) {
          return '策略看来的得心应手'
        } else if (n <= 100) {
          return '策略看来春风得意，堪比当代索罗斯'
        } else {
          return '策略看来独孤求败，小心过拟合噢'
        }
      }
    },
    mounted () {
      let self = this
      this.$tqsdk.on('rtn_data', function() {
        let account_id = self.$store.state.account_id
        if (!account_id) return
        let account = self.$tqsdk.getByPath(['trade', account_id, 'accounts', 'CNY'])
        if (account && account._tqsdk_stat) {
          self.init_balance = account._tqsdk_stat.init_balance
          self.balance = account._tqsdk_stat.balance
          self.max_drawdown = account._tqsdk_stat.max_drawdown
          self.annual_yield = account._tqsdk_stat.annual_yield
          self.ror = account._tqsdk_stat.ror
          self.sharpe_ratio = account._tqsdk_stat.sharpe_ratio
          self.winning_rate = account._tqsdk_stat.winning_rate
          self.profit_loss_ratio = account._tqsdk_stat.profit_loss_ratio
          let trades = self.$tqsdk.getByPath(['trade', account_id, 'trades'])
          let commission = 0
          for (let id in trades) commission += trades[id].commission
          self.commission = commission
        }
      })
    }
  }
</script>
<style lang="scss">
    .backtest-info {
        .ivu-row {
            .ivu-col {
                &:nth-child(odd) {
                    text-align: left;
                    padding: 2px 0px 2px 16px;
                }
                &:nth-child(even) {
                    text-align: right;
                    padding: 2px 16px 2px 0px;
                }
            }
        }

        @keyframes ani-spin {
            from { transform: rotate(0deg);}
            50%  { transform: rotate(180deg);}
            to   { transform: rotate(360deg);}
        }
        .ivu-col.spin-container{
            height: 60px;
            position: relative;
            .loader {
                width: 30px;
                height: 30px;
                position: relative;
                margin: 0 auto;
            }
            .circular {
                animation: rotate 2s linear infinite;
                height: 100%;
                transform-origin: center center;
                width: 100%;
                position: absolute;
                top: 0;
                bottom: 0;
                left: 0;
                right: 0;
                margin: auto;
            }
            circle.path {
                stroke-dasharray: 1,200;
                stroke-dashoffset: 0;
                animation: dash 1.5s ease-in-out infinite, color 6s ease-in-out infinite;
                stroke-linecap: round;
            }
        }
    }

    @keyframes color {
        0%, 100% {
            stroke: #d62d20;
        }
        40% {
            stroke: #0057e7;
        }
        66% {
            stroke: #008744;
        }
        80%, 90% {
            stroke: #ffa700;
        }
    }

    @keyframes dash {
        0% {
            stroke-dasharray: 1,200;
            stroke-dashoffset: 0;
        }
        50% {
            stroke-dasharray: 89,200;
            stroke-dashoffset: -35;
        }
        100% {
            stroke-dasharray: 89,200;
            stroke-dashoffset: -124;
        }
    }

</style>
