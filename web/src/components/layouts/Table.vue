<template>
    <div class="reports orders-table" :style="{height:height + 'px'}">
        <table>
            <thead>
            <tr>
                <th v-for="col in columns" >{{col.name}}</th>
                <th v-for="col in columnsAppend" >{{col.name}}</th>
            </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</template>
<script>
  import {FormatDirection, FormatOffset} from '@/utils/formatter'
  export default {
    data () {
      return {
        tbodyRoot: null,

      }
    },
    props: {
      height: Number,
      /**
       * name: '未成交手数',
       * key: 'volume_left',
       * cb: d => d.exchange_id + '.' + d.instrument_id [option] 渲染文字
       * once: true [option] 只添加的时候计算一次
       */
      columns: []
    },
    mounted () {
      this.tbodyNode = document.querySelector('.orders-table table tbody')
      let self = this
      this.$tqsdk.on('rtn_data', function(){
        let account_id = self.$store.state.account_id
        if (!account_id) return
        let orders =self.$tqsdk.getByPath(['trade', account_id, 'orders'])
        if (!orders) return
        for(let order_id in orders){
          if (orders[order_id]._epoch === self.$tqsdk.dm._epoch) {
            if (self.ordersTr[order_id]) {
              self.update_order(orders[order_id], self.ordersTr[order_id])
            } else {
              self.ordersTr[order_id] = self.append_order(orders[order_id])
            }
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
