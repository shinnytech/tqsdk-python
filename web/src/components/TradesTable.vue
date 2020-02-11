<template>
    <div class="reports trades-table" :style="{height:height + 'px'}">
        <table>
            <thead>
            <tr>
                <th v-for="col in columns" :width="col.width ? col.width+'px' : ''" >{{col.name}}</th>
            </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</template>
<script>
    import moment from 'moment'
    import {FormatDirection, FormatOffset} from '@/utils/formatter'
  export default {
    data () {
      return {
        tbodyRoot: null,
        columns: [{
          name: '成交合约',
          key: 'instrument_id',
          width: '100',
          cb: d => d.exchange_id + '.' + d.instrument_id
        }, {
          name: '方向',
          key: 'direction',
          width: '60',
          cb: d => FormatDirection(d.direction)
        }, {
          name: '开平',
          key: 'offset',
          width: '60',
          cb: d => FormatOffset(d.offset)
        }, {
          name: '成交价格',
          width: '60',
          key: 'price'
        }, {
          name: '手数',
          width: '60',
          key: 'volume'
        }, {
          name: '成交时间',
          key: 'trade_date_time',
          width: '140',
          cb: d => moment(d.trade_date_time / 1000000).format('YYYY-MM-DD HH:mm:ss')
        }, {
          name: '报单编号',
          key: 'trade_id',
          width: '260',
        }]
      }
    },
    props: {
      height: Number
    },
    mounted () {
      this.tbodyNode = document.querySelector('.trades-table table tbody')
      let self = this

      let update = function () {
        let account_id = self.$store.state.account_id
        if (!account_id) return
        let list = []
        let trades = self.$tqsdk.getByPath(['trade', account_id, 'trades'])
        if (!trades) return
        for(let trade_id in trades){
          if (trades[trade_id]._epoch === self.$tqsdk.dm._epoch) {
            list.push(trades[trade_id])
          }
        }
        list.sort(function (a, b) {
          return a.trade_date_time - b.trade_date_time
        })
        for (let j=0; j<list.length; j++){
          let tr = self.append_trade(list[j])
          tr.onclick = function (event) {
            let trs = self.tbodyNode.querySelectorAll('tr')
            trs.forEach(node => node.className = '')
            tr.className = 'selected'
            self.$eventHub.$emit('moveChartToDt', list[j].trade_date_time)
          }
        }
      }
      update()
      this.$tqsdk.on('rtn_data', update)
    },
    methods: {
      append_trade (trade) { // trade or log'
        let tr = document.createElement('tr')
        for (let i in this.columns) {
          let col = this.columns[i]
          let td = this.get_td_text(col.cb ? col.cb(trade) : trade[col.key], col.key)
          tr.appendChild(td)
        }
        this.tbodyNode.insertBefore(tr, this.tbodyNode.firstChild)
        return tr;
      },
      get_td_text (text) {
        let td = document.createElement('td')
        td.textContent = text
        return td
      }
    }
  }
</script>
