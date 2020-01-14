<template>
    <div class="quote-info-container">
        <Row  class-name="quote-items-title">
            <Col :span="largeSize ? 12 : 24">
            <div>{{quote.ins_name}}</div>
            </Col>
            <Col :span="largeSize ? 12 : 24">
            <div>{{quote.ins_id}}</div>
            </Col>
        </Row>
        <Row>
            <Col :span="largeSize ? 6 : 12">
                <div>卖一</div>
            </Col>
            <Col :span="largeSize ? 9 : 12">
                <div>{{formatter(quote.ask_price1)}}</div>
            </Col>
            <Col :span="largeSize ? 9 : '0'">
                {{quote.ask_volume1}}
            </Col>
        </Row>
        <div class="outer">
            <div class="inner" :style="{width: innerWidth * 100 + '%'}"></div>
        </div>
        <Row>
            <Col :span="largeSize ? 6 : 12">
            买一
            </Col>
            <Col :span="largeSize ? 9 : 12">
            {{formatter(quote.bid_price1)}}</Col>
            <Col :span="largeSize ? 9 : '0'">
                {{quote.bid_volume1}}
            </Col>
        </Row>
        <Row :class-name="'quote-items ' + (largeSize ? 'large-size' : '')" >
            <Col :span="largeSize ? 6 : 24">
            最新价
            </Col>
            <Col :span="largeSize ? 6 : 24" :class="classOfColor">
            {{formatter(quote.last_price)}}
            </Col>
            <Col :span="largeSize ? 6 : 24">
            昨结算
            </Col>
            <Col :span="largeSize ? 6 : 24">
            {{formatter(quote.pre_settlement)}}
            </Col>

            <Col :span="largeSize ? 6 : 24">
            涨跌
            </Col>
            <Col :span="largeSize ? 6 : 24" :class="classOfColor">
            {{formatter(quote.change)}}
            </Col>
            <Col :span="largeSize ? 6 : 24">
            今开
            </Col>
            <Col :span="largeSize ? 6 : 24">
            {{quote.open}}
            </Col>

            <Col :span="largeSize ? 6 : 24">
            涨跌幅
            </Col>
            <Col :span="largeSize ? 6 : 24" :class="classOfColor">
            {{ quote.change_percent | toFixed }}%
            </Col>
            <Col :span="largeSize ? 6 : 24">
            最高
            </Col>
            <Col :span="largeSize ? 6 : 24">
            {{formatter(quote.highest)}}
            </Col>

            <Col :span="largeSize ? 6 : 24">
            总手
            </Col>
            <Col :span="largeSize ? 6 : 24" :class="classOfColor">
            {{formatterVolume(quote.volume)}}
            </Col>
            <Col :span="largeSize ? 6 : 24">
            最低
            </Col>
            <Col :span="largeSize ? 6 : 24">
            {{formatter(quote.lowest)}}
            </Col>

            <Col :span="largeSize ? 6 : '0'">
            涨停
            </Col>
            <Col :span="largeSize ? 6 : '0'" class="R">
            {{formatter(quote.upper_limit)}}
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            收盘
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            {{formatter(quote.close)}}
            </Col>

            <Col :span="largeSize ? 6 : '0'">
            跌停
            </Col>
            <Col :span="largeSize ? 6 : '0'" class="G">
            {{formatter(quote.lower_limit)}}
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            结算
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            {{formatter(quote.settlement)}}
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            持仓量
            </Col>
            <Col :span="largeSize ? 6 : '0'">
            {{quote.open_interest}}</Col>
            <Col :span="largeSize ? 6 : '0'">
            日增</Col>
            <Col :span="largeSize ? 6 : '0'">
            {{Number.isNaN(quote.open_interest - quote.pre_open_interest) ? '-' : quote.open_interest - quote.pre_open_interest}}</Col>
        </Row>
    </div>
</template>
<script>
  import { FormatPrice } from '@/utils/formatter'
    const initQuote = {
      ins_name: '-',
      ins_id: '-',
      price_decs: 2,
      last_price: '-',
      ask_price1: '-',
      ask_volume1: '-',
      bid_price1: '-',
      bid_volume1: '-',
      pre_settlement: '-', // 昨结算
      change: '-',
      change_percent: '-',
      open: '-',
      close: '-',
      highest: '-',
      volume: '-',
      lowest: '-',
      upper_limit: '-',
      lower_limit: '-',
      settlement: '-',
      open_interest: '-',
      pre_open_interest: '-',
    }
  export default {
    data () {
      return {
        quote: Object.assign({}, initQuote)
      }
    },
    props: {
      symbol: String,
      height: Number,
      width: Number
    },
    watch: {
      symbol: function (n, o) {
        this.$tqsdk.subscribeQuote(this.symbol)
        let quote = this.$tqsdk.getQuote(this.symbol)
        updateObject(this.quote, quote)
      }
    },
    computed: {
      classOfColor: function () {
        if (this.quote['change'] > 0) return 'R'
        else if (this.quote['change'] < 0) return 'G'
        else return ''
      },
      innerWidth: function () {
        return this.quote.bid_volume1 / (this.quote.bid_volume1 + this.quote.ask_volume1)
      },
      largeSize: function () {
        return this.width > 100
      }
    },
    created () {
      let self = this
      this.$tqsdk.subscribe_quote(this.symbol)
      this.$tqsdk.on('rtn_data', function() {
        let quote = self.$tqsdk.getQuote(self.symbol)
        updateObject(self.quote, quote)
      })
    },
    methods : {
      formatter: function (price) {
        return FormatPrice(price, this.quote.price_decs)
      },
      formatterVolume: function (volume) {
        if (typeof volume !== "number") return volume
        if (volume > 100000000) {
            return (volume / 100000000).toFixed(1) + '亿'
        } else if (volume > 10000) {
          return (volume / 100000000).toFixed(1) + '万'
        } else return volume
      }
    }
  }
  function updateObject(target, source) {
      Object.keys(initQuote).forEach(function(val, ind, arr){
        if (target[val] !== source[val]) target[val] = source[val]
      })
  }
</script>
<style lang="scss">
    .quote-info-container {
        font-size: 12px;
        line-height: 14px;
        .outer {
            height: 3px;
            width: 100%;
            background-color: #57c038;
            .inner {
                height: 3px;
                background-color: #fc5b57;
            }
        }
        .ivu-row.quote-items-title {
            padding: 4px 0px;
        }
        .ivu-row.quote-items {
            padding: 4px 0px;
            .ivu-col {
                &:nth-child(odd) {
                    padding-top: 4px;
                }
                &:nth-child(even) {
                    padding-bottom: 4px;
                }
                &.R {
                    color: red;
                }
                &.G {
                    color: green;
                }
            }

            &.large-size {
                .ivu-col {
                    padding: 0px;
                    &:nth-child(odd) {
                        color: #545454;
                        text-align: right;
                        padding-right: 4px;
                    }
                    &:nth-child(even) {
                        text-align: left;
                    }
                }
            }

        }

    }
</style>
