import Vue from 'vue'
import VueRouter from 'vue-router'
import TianqinTwo from '../views/TianqinTwo.vue'
import TianqinHome from '../views/TianqinHome.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'tianqin',
    component: TianqinHome
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
