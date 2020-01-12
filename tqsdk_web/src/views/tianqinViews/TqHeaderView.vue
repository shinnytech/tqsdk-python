<template>
    <div class="tq-header-view">
        <tq-layout-area :height="height"
            :otherStyle="{backgroundColor: '#FEFEFE'}">
            <a href="https://www.shinnytech.com/tianqin/" target="_blank">
                <img class="logo" alt="Tianqin" src="@/assets/logo.png"
                     :style="{padding: '4px',
                          width: height + 'px',
                          height: height + 'px'}">
            </a>
        </tq-layout-area>
        <tq-layout-area :height="height" :left="height" :width="240"
                        :otherStyle="{paddingTop: '8px'}">
            <!-- 策略名称 -->
            {{$store.state.file_name}}
        </tq-layout-area>
        <tq-layout-area :height="height" :left="height + 240" :width="380"
                        :otherStyle="{paddingTop: '8px', backgroundColor: $store.state.mode === 'backtest' ? '#FAF5EA' : $store.state.mode === 'replay' ? '#F0E2FA' : '#FFF'}">
            <!-- 账户名称 / 回测区间 / 复盘时间、速度、控制器 -->
            <div v-if="$store.state.mode === 'run'">账户：{{$store.state.broker_id}},{{$store.state.account_id}} </div>
            <div v-if="$store.state.mode === 'backtest'">回测区间： {{formatDt($store.state.start_dt)}} -- {{formatDt($store.state.end_dt)}} </div>
            <div v-if="$store.state.mode === 'replay'">
                <tq-replay-ctrl></tq-replay-ctrl>
            </div>
        </tq-layout-area>
        <tq-layout-area :height="height" :width="160" :horizontalAlign="'right'" :otherStyle="{paddingTop: '8px'}">
            <!-- py文件 / 行情状态 / 交易状态 -->
            <Badge :color="!$store.state.py_file_status ? 'red' : 'green'" text="py文件" />
            <Badge :color="!$store.state.md_url_status ? 'red' : 'green'" text="行情" />
            <Badge :color="!$store.state.td_url_status ? 'red' : 'green'" text="交易" />
        </tq-layout-area>
    </div>
</template>
<script>
  import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
  import TqReplayCtrl from '@/components/TqReplayCtrl.vue'
  import moment from 'moment'
  export default {
    name: 'tq-header-view',
    components: {
      TqLayoutArea,
      TqReplayCtrl
    },
    props: {
      height: Number
    },
    methods: {
      formatDt(dt, format='YYYY-MM-DD HH:mm:ss') {
        return moment(dt / 1e6).format(format)
      }
    }
  }
</script>
<style lang="scss">
    .tq-header-view {
        width: 100%;
        .ivu-badge-status  {
            &:not(:last-child) {
                padding-right: 10px;
            }
            .ivu-badge-status-dot {
                width: 10px;
                height: 10px;
            }
            .ivu-badge-status-text {
                margin-left: 2px;
            }
        }
    }
</style>
