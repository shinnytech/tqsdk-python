<template>
    <div class="reports orders-table" :style="{height:height + 'px'}">
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
    import moment from 'moment'
    import {FormatDirection, FormatOffset} from '@/utils/formatter'
  export default {
    data () {
      return {
        tbodyRoot: null,
        columns: [{
          name: '成交合约',
          width: '100',
          key: 'instrument_id',
          cb: d => d.exchange_id + '.' + d.instrument_id
        }, {
          name: '方向',
          width: '60',
          key: 'direction',
          cb: d => FormatDirection(d.direction)
        }, {
          name: '开平',
          width: '60',
          key: 'offset',
          cb: d => FormatOffset(d.offset)
        }, {
          name: '报单价格',
          width: '60',
          key: 'limit_price'
        }, {
          name: '总手数',
          width: '60',
          key: 'volume_orign'
        }, {
          name: '报单时间',
          width: '140',
          key: 'insert_date_time',
          cb: d => moment(d.insert_date_time / 1000000).format('YYYY-MM-DD HH:mm:ss')
        }],
        columnsAppend: [{
          name: '未成交手数',
          key: 'volume_left',
          width: '80',
          cb: d => d.volume_left
        }, {
          name: '冻结保证金',
          width: '80',
          key: 'frozen_margin'
        }, {
          name: '状态',
          width: '60',
          key: 'status',
          cb: d => d.status === 'FINISHED' ? '已完成' : '未完成'
        }, {
          name: '提示信息',
          key: 'last_msg',
          width: '160',
        }],
        ordersTr: {}
      }
    },
    props: {
      height: Number
    },
    mounted () {
      this.tbodyNode = document.querySelector('.orders-table table tbody')
      let self = this
      this.$tqsdk.on('rtn_data', function(){
        let account_id = self.$store.state.account_id
        if (!account_id) return
        let orders = self.$tqsdk.getByPath(['trade', account_id, 'orders'])
        if (!orders) return
        for(let order_id in orders){
          if (self.ordersTr[order_id]) {
            self.update_order(orders[order_id], self.ordersTr[order_id])
          } else {
            let tr = self.append_order(orders[order_id])
            tr.onclick = function (event) {
              let trs = self.tbodyNode.querySelectorAll('tr')
              trs.forEach(node => node.className = '')
              tr.className = 'selected'
              self.$eventHub.$emit('moveChartToDt', orders[order_id].insert_date_time)
            }
            self.ordersTr[order_id] = tr
          }
        }
      })
    },
    methods: {
      append_order (order) {
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
      update_order(order, tr) {
        for (let i in this.columnsAppend) {
          let col = this.columns[i]
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
