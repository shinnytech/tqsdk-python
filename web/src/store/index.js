import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    mode: '',
    broker_id: '',
    account_id: '',
    py_file_status: '',
    md_url_status: '',
    td_url_status: '',
    file_path: '',
    file_name: ''
  },
  mutations: {
    set_action(state, payload){
      Object.assign(state, payload)
    },
    set_py_file_status(state, payload){
      state.py_file_status = payload
    }
  },
  actions: {
  }
})

export default store
