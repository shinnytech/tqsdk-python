<template>
    <div class="reports positions-table" :style="{height:height + 'px'}">
        <table>
            <thead>
            <tr>
                <th v-for="col in columns"  :width="col.width ? col.width+'px' : ''">{{col.name}}</th>
                <th v-for="col in columnsAppend"  :width="col.width ? col.width+'px' : ''">{{col.name}}</th>
            </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</template>
<script>
    import {FormatPrice} from '@/utils/formatter'
  export default {
    data () {
      return {
        tbodyRoot: null,
        columns: [{
          name: '持仓合约',
          width: '100',
          key: 'instrument_id',
          cb: d => d.exchange_id + '.' + d.instrument_id
        }],
        columnsAppend: [{
          name: '多仓',
          key: 'volume_long',
          width: '60',
        }, {
          name: '多头开仓均价',
          width: '80',
          key: 'open_price_long',
          cb: d => FormatPrice(d.open_price_long)
        }, {
          name: '多头浮动盈亏',
          width: '80',
          key: 'position_profit_long',
          cb: d => FormatPrice(d.position_profit_long)
        }, {
          name: '多头占用保证金',
          width: '80',
          key: 'margin_long',
          cb: d => FormatPrice(d.margin_long)
        }, {
          name: '空仓',
          key: 'volume_short',
          width: '60',
        }, {
          name: '空头开仓均价',
          width: '80',
          key: 'open_price_short',
          cb: d => FormatPrice(d.open_price_short)
        }, {
          name: '空头浮动盈亏',
          width: '80',
          key: 'position_profit_short',
          cb: d => FormatPrice(d.position_profit_short)
        }, {
          name: '空头占用保证金',
          width: '80',
          key: 'margin_short',
          cb: d => FormatPrice(d.margin_short)
        }],
        ordersTr: {}
      }
    },
    props: {
      height: Number
    },
    mounted () {
      this.tbodyNode = document.querySelector('.positions-table table tbody')
      let self = this
      this.$tqsdk.on('rtn_data', function(){
        let account_id = self.$store.state.account_id
        if (!account_id) return
        let positions = self.$tqsdk.getByPath(['trade', account_id, 'positions'])
        if (!positions) return
        for(let symbol in positions){
          if (self.ordersTr[symbol]) {
            self.update_position(positions[symbol], self.ordersTr[symbol])
          } else {
            self.ordersTr[symbol] = self.append_position(positions[symbol])
          }
        }
      })
    },
    methods: {
      append_position (order) {
        let tr = document.createElement('tr')
        for (let i in this.columns) {
          let col = this.columns[i]
          let td = this.get_td_text(col.cb ? col.cb(order) : order[col.key], col.key)
          tr.appendChild(td)
        }
        for (let i in this.columnsAppend) {
          let col = this.columnsAppend[i]
          let td = this.get_td_text(col.cb ? col.cb(order) : order[col.key], col.key)
          tr.appendChild(td)
        }
        this.tbodyNode.insertBefore(tr, this.tbodyNode.firstChild)
        return tr;
      },
      update_position(order, tr) {
        for (let i in this.columnsAppend) {
          let col = this.columnsAppend[i]
          let td = tr.querySelector('.' + col.key)
          let text = col.cb ? col.cb(order) : order[col.key]
          if (text !== td.textContent) this.update_td_text(text, td)
        }
      },
      get_td_text (text, className) {
        let td = document.createElement('td')
        td.className = className
        td.textContent = text
        return td
      },
      update_td_text (text, td) {
        td.textContent = text
      }
    }
  }
</script>
