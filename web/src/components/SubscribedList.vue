<template>
    <div class="subscribed-list">
        <template v-for="symbol in subscribedSymbols">
            <template v-for="item in subscribed[symbol]">
                <Button size="small" long @click="onClick(symbol, item)">
                    {{symbol}} {{ParseDurationToString(item)}}
                </Button>
            </template>
        </template>
    </div>
</template>
<script>
    import { ParseDurationToString } from '@/utils/formatter'
    const subscribedSymbols = []
    const subscribed = {}
  export default {
    data () {
      return {
        subscribedSymbols,
        subscribed
      }
    },
    props: {},
    watch: {
      subscribedSymbols: function (newVal, oldVal) {
        console.log(newVal, oldVal)
      }
    },
    mounted () {
      let self = this
      this.$tqsdk.on('rtn_data', function() {
        let subList = self.$tqsdk.getByPath(['subscribed'])
        if (subList && subList._epoch === self.$tqsdk.dm._epoch) {
          for (let i in subList) {
            let item = subList[i]
            if (Array.isArray(item.symbol)) {
              for (let j in item.symbol) {
                self.addSubscribed(item.symbol[j], item.dur_nano)
              }
            } else {
              self.addSubscribed(item.symbol, item.dur_nano)
            }
          }
          self.updateSubscribedSymbols()
        }
      })
    },
    methods: {
      addSubscribed (symbol, dur_nano) {
        if (!subscribed[symbol]) {
          subscribed[symbol] = []
        }
        if (!dur_nano) dur_nano = ''
        if (!subscribed[symbol].includes(dur_nano)) {
          subscribed[symbol].push(dur_nano)
        }
      },
      updateSubscribedSymbols () {
        for (let symbol in subscribed) {
          if (subscribedSymbols.indexOf(symbol) === -1) {
            subscribedSymbols.push(symbol)
          }
        }
      },
      onClick (symbol, dur_nano) {
        this.$emit('onChange', symbol, dur_nano)
      },
      ParseDurationToString
    }
  }
</script>
