<template>
    <div class="account-info" :style="{height:height + 'px'}">
        <div> 账户权益: {{balance | toFixed}} </div>
        <div> 浮动盈亏: {{float_profit | toFixed}} </div>
        <div> 保证金占用: {{margin | toFixed}} </div>
        <div> 日内手续费: {{commission | toFixed}} </div>
        <div> 可用资金: {{available | toFixed}} </div>
    </div>
</template>
<script>
  export default {
    data () {
      return {
        available: '-', // 可用资金
        balance: '-', // 账户权益
        commission: '-', //手续费
        float_profit: '-', // 浮动盈亏
        margin: '-', // 占用资金
      }
    },
    props: {
      height: Number
    },
    computed: {
      account_id () {
        return this.$store.state.account_id
      }
    },
    mounted () {
      setImmediate(this.update.bind(this))
      this.$tqsdk.on('rtn_data', this.update)
    },
    methods: {
      update () {
        if (!this.account_id) return
        let account = this.$tqsdk.getByPath(['trade', this.account_id, 'accounts', 'CNY'])
        if (this.$tqsdk.isChanging(account)) {
          this.available = account.available
          this.balance = account.balance
          this.commission = account.commission
          this.float_profit = account.float_profit
          this.margin = account.margin
        }
      }
    }
  }
</script>
<style lang="scss">
    .account-info {
        padding: 3px 6px;
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        background-color: #e6f7ff;
        font-size: 14px;
        color: black;
        div {
            display: inline-flex;
            width: 20%;
        }
    }
</style>
