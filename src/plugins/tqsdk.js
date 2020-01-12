import Vue from 'vue'
import TQSDK from 'tqsdk'

let tqsdk = new TQSDK({
  wsTradeUrl: 'wss://opentd.shinnytech.com/trade/user0'
})

const NOOP = () => {}
let tqVmEventMap = {}
let tqsdkRe = /^tqsdk:/

function mixinEvents(Vue) {
  let on = Vue.prototype.$on
  let emit = Vue.prototype.$emit

  Vue.prototype.$on = function proxyOn(eventName, fn = NOOP) {
    const vm = this
    if (Array.isArray(eventName)) {
      eventName.forEach((item) => vm.$on(item, fn));
    } else if (tqsdkRe.test(eventName)) {
      if (!tqVmEventMap[vm._uid]) tqVmEventMap[vm._uid] = {}
      let tq_eventName = eventName.match(/^tqsdk:(.*)/)[1]
      if (!tqVmEventMap[vm._uid][tq_eventName]) tqVmEventMap[vm._uid][tq_eventName] = []
      tqVmEventMap[vm._uid][tq_eventName].push(fn)
      tqsdk.on(tq_eventName, fn.bind(vm))
    } else {
      on.call(vm, eventName, fn)
    }
    return vm
  }
}

function applyMixin(Vue) {
  Vue.mixin({
    beforeDestroy() {
      const vm = this
      const tqevents = tqVmEventMap[vm._uid] || {};
      for (let eventName in tqevents) {
        let eventsArr = tqevents[eventName]
        eventsArr.forEach((fn) => {
          tqsdk.removeEventListener(eventName, fn)
        })
      }
      delete tqVmEventMap[vm._uid];
    }
  })
}

function plugin(Vue) {
  if (plugin.installed) return
  plugin.installed = true
  mixinEvents(Vue)
  applyMixin(Vue)
}

Vue.use(plugin)

Vue.$tqsdk = tqsdk
Vue.prototype.$tqsdk = tqsdk

export default tqsdk;
