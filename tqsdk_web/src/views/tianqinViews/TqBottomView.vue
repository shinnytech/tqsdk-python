<template>
    <div class="tq-bottom-view">
        <template v-if="$store.state.mode === 'backtest'">
            <tq-layout-area :width="width / 2" :height="height">
                <Tabs :animated="false">
                    <TabPane label="回测指标">
                        <backtest-info :width="width" :height="height - 27"></backtest-info>
                    </TabPane>
                    <TabPane label="成交记录">
                        <trades-table :width="width" :height="height - 27"></trades-table>
                    </TabPane>
                </Tabs>
            </tq-layout-area>
            <tq-layout-area horizontalAlign="right" :width="width / 2" :height="height"
                            :otherStyle="{borderLeft: '2px solid #E0E0E0'}">
                <backtest-chart></backtest-chart>
            </tq-layout-area>
        </template>
        <template v-else-if="$store.state.mode === 'run' || $store.state.mode === 'replay'">
            <tq-layout-area :height="26" :width="width">
                <account-info :height="26"></account-info>
            </tq-layout-area>
            <tq-layout-area :height="height - 26" :top="26" :width="width">
                <Tabs>
                    <TabPane label="持仓">
                        <positions-table :width="width" :height="height - 53"></positions-table>
                    </TabPane>
                    <TabPane label="成交记录">
                        <trades-table :width="width" :height="height - 53"></trades-table>
                    </TabPane>
                    <TabPane label="委托单记录">
                        <orders-table :width="width" :height="height - 53"></orders-table>
                    </TabPane>
                </Tabs>
            </tq-layout-area>
        </template>
    </div>
</template>
<script>
  import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
  import TradesTable from '@/components/TradesTable.vue'
  import OrdersTable from '@/components/OrdersTable.vue'
  import PositionsTable from '@/components/PositionsTable.vue'
  import AccountInfo from '@/components/AccountInfo.vue'
  import BacktestInfo from '@/components/BacktestInfo.vue'
  import BacktestChart from '@/components/BacktestChart.vue'
  export default {
    name: 'tq-bottom-view',
    components: {
      TqLayoutArea,
      TradesTable,
      OrdersTable,
      PositionsTable,
      AccountInfo,
      BacktestInfo,
      BacktestChart
    },
    props: {
      height: Number,
      width: Number
    },
    data () {
      return {}
    },
    methods: {},
    created () {}
  }
</script>
<style lang="scss">
    .tq-bottom-view {
        font-size: 12px;
        .ivu-tabs-bar {
            margin-bottom: 0px;
        }
        .ivu-tabs-nav .ivu-tabs-tab {
            padding: 3px 16px;
        }
    }

    $red: #F44336;
    $green: #4CAF50;
    $blue: #2196F3;

    /*.strategy-log {*/
        /*height: 100%;*/
        /*font-size: 12px;*/
    /*}*/

    .reports {
        overflow-y: scroll;
        width: 100%;
        background-color: #fff;

        table {
            border-collapse: collapse;
            table-layout: fixed;
            width: 100%;
        }

        table, th, td {
            background-color: #fff ;
            border-bottom: 1px solid lightgrey;
        }
        th {
            background-color: lightgrey;
            color: #333333;
            position: sticky;
            top: 0;
        }
        td {
            color: #000000;
        }
        th, td {
            padding: 4px;
            text-align: left;
        }
        tbody {
            tr:hover td {
                background-color: #f5f5f5;
            }
            tr.selected td {
                background-color: #90CAF9;
                color: #000000;
            }
        }

        .ivu-icon {
            font-size: 16px;
            &.type-success { color: $green; }
            &.type-error { color: $red; }
            &.type-info { color: $blue; }
        }
    }
</style>
