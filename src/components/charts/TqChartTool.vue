<template>
    <div class="tq-chart-tool">
        <!--<tq-radio-group :options="optionsDay" @changeSelectId="changeSelectId"></tq-radio-group>-->
        <tq-radio-group :options="optionsDur" @changeSelectId="changeSelectId"></tq-radio-group>
    </div>
</template>
<script>
  import TqRadioGroup from './TqRadioGroup.vue'
  export default {
    name: 'tq-chart-tool',
    components: {
      TqRadioGroup
    },
    data () {
      return {
        optionsDay: [
          {
            id: '1day',
            name: '日内'
          }, {
            id: '3day',
            level: 'more',
            name: '3日'
          }, {
            id: '5day',
            level: 'more',
            name: '5日'
          }, {
            id: '8day',
            level: 'more',
            name: '8日'
          }],
        optionsDur: [
          {
            id: '1m',
            name: '1m'
          }, {
            id: '5m',
            name: '5m'
          }, {
            id: '10m',
            name: '10m'
          }, {
            id: '30m',
            name: '30m'
          }, {
            id: '1h',
            name: '1h'
          }, {
            id: '2h',
            name: '2h'
          }, {
            id: '1d',
            name: '1d'
          }]
      }
    },
    props: {
    },
    methods: {
      changeSelectId (id) {
        if (id.endsWith('day')) {
          this.$emit('on-change-duration', id)
        } else {
          this.$emit('on-change-duration', id)
        }
      }
    },
    created() {
    }
  }
</script>
<style>
    .tq-chart-tool, .tq-radio-group {
        display: inline-block;
    }
</style>
