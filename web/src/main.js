import Vue from 'vue'
import moment from 'moment'
import App from './App.vue'
import TQSDK from 'tqsdk'
import './plugins/iview'
import store from './store'

Vue.config.productionTip = false
Vue.$eventHub = new Vue(); // Global event bus
Vue.prototype.$eventHub = Vue.$eventHub;

const RootData = {
  name: 'tianqin-web',
  windowHeight: window.innerHeight,
  windowWidth: window.innerWidth
}

const RootApp = new Vue({
  data: RootData,
  store,
  render: h => h(App),
  methods: {
    handlerResize: function () {
      RootData.windowHeight = window.innerHeight
      RootData.windowWidth = window.innerWidth
      this.$eventHub.$emit('window_resize', {
        width: RootData.windowWidth,
        height: RootData.windowHeight
      })
    }
  },
  created: function () {
    // https://developer.mozilla.org/en-US/docs/Web/Events/resize
    window.addEventListener('resize', resizeThrottler, false)
    let resizeTimeout
    function resizeThrottler () {
      if (!resizeTimeout) {
        resizeTimeout = setTimeout(function () {
          resizeTimeout = null
          RootApp.handlerResize()
        }, 200)
      }
    }
  },
  errorCaptured: (err, vm, info) => {
    console.error('App.errorCaptured', err, vm, info)
    return false
  },
  destroyed: () => {}
})

Vue.filter('toFixed', function (value, decs) {
  let n = Number(value)
  decs = Number.isInteger(decs) ? decs : 2
  return Number.isFinite(n) ? n.toFixed(decs) : (value ? value : '-')
})

GetTqsdkUrl().then(function(urlJson){
  let ins_url = urlJson['ins_url']
  let md_url = urlJson['md_url']
  if (ins_url === 'https://openmd.shinnytech.com/t/md/symbols/latest.json') {
    let dt = moment().format('YYYY-MM-DD HH:mm:ss.SSSSSS')
    ins_url = `https://openmd.shinnytech.com/t/md/symbols/${dt}.json`
  }
  if (urlJson['replay_dt']) {
    let index = ins_url.indexOf('/symbol')
    store.state.ctrl_url = ins_url.substring(0, index)
    let dt = moment(urlJson['replay_dt']/1e6).format('YYYY-MM-DD HH:mm:ss')
    dt += (Math.random() + '').substring(2, 8)
    ins_url = `https://openmd.shinnytech.com/t/md/symbols/${dt}.json`
  }

  Vue.$tqsdk = new TQSDK({
    symbolsServerUrl: ins_url,
    wsQuoteUrl: md_url,
    autoInit: false
  })
  Vue.prototype.$tqsdk = Vue.$tqsdk
  Vue.$tqsdk.initMdWebsocket()
  let tqWs = Vue.$tqsdk.addWebSocket(`ws://${TqsdkAddress}/ws`)
  tqWs.on('close', function(){
    store.commit('set_py_file_status', false)
  })
  tqWs.on('open', function(){
    store.commit('set_py_file_status', true)
  })

  Vue.$tqsdk.on('rtn_data', function(){
    let backtest = Vue.$tqsdk.get_by_path(['_tqsdk_backtest'])
    if (backtest && backtest.current_dt) {
      store.state.start_dt = backtest.start_dt
      store.state.end_dt = backtest.end_dt
    }
    let replay = Vue.$tqsdk.get_by_path(['_tqsdk_replay'])
    if (replay && replay.replay_dt) {
      store.state.replay_dt = replay.replay_dt
    }
    let action = Vue.$tqsdk.get_by_path(['action'])
    if (store.state.mode === '' && action)
      store.commit('set_action', action)
  })
  RootApp.$mount('#app')
})
