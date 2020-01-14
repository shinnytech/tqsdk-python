<template>
    <div class="replay-control">
        复盘日期： {{currentDateTime ? currentDateTime : formatDt($store.state.replay_dt)}} ({{this.currentSpeed}})
        <ButtonGroup size="small">
            <Button @click="ctrl('play')">
                <Icon type="ios-play"></Icon>
            </Button>
            <Button @click="ctrl('pause')">
                <Icon type="ios-pause"></Icon>
            </Button>
            <Button @click="ctrl('rewind')">
                <Icon type="ios-rewind" />
            </Button>
            <Button @click="ctrl('fastforward')">
                <Icon type="ios-fastforward" />
            </Button>
        </ButtonGroup>
    </div>
</template>
<script>
  import moment from 'moment'
  export default {
    name: "tq-replay-control",
    data: function () {
      return {
        // todo: 初始值目前无法获取，等服务器添加接口后，改成获取当前复盘速度
        currentSpeed: '-',
        currentDateTime: ''
      }
    },
    props: {
      width: Number
    },
    computed: {
      replayUrl () {
        return this.$store.state.ctrl_url
      }
    },
    methods: {
      setSpeed(speed) {
        fetch(this.replayUrl, {
          method: 'POST',
          body: JSON.stringify({aid: "ratio", "speed": speed}) // body data type must match "Content-Type" header
        }).then(function(response){
          console.log(response)
        });
      },
      ctrl(action) {
        if (action === "play") {
          if (this.currentSpeed === '-') {
            this.currentSpeed = 1
          }
          this.setSpeed(this.currentSpeed)
        } else if (action === "pause") {
          this.setSpeed(0)
        } else if (action === "rewind") {
          if (this.currentSpeed === '-') {
            this.currentSpeed = 1
          } else if (this.currentSpeed <= 5) {
            this.currentSpeed = Math.max(1, this.currentSpeed - 1)
          } else if (this.currentSpeed <= 40){
            this.currentSpeed -= 5
          } else if (this.currentSpeed <= 100) {
            this.currentSpeed -= 10
          }
          this.setSpeed(this.currentSpeed)
        } else if (action === "fastforward") {
          if (this.currentSpeed === '-') {
            this.currentSpeed = 2
          } else if (this.currentSpeed < 5) {
            this.currentSpeed += 1
          } else if (this.currentSpeed < 40){
            this.currentSpeed += 5
          } else if (this.currentSpeed < 100) {
            this.currentSpeed += 10
          } else {
            this.currentSpeed = 100
          }
          this.setSpeed(this.currentSpeed)
        }
      },
      formatDt(dt, format='YYYY-MM-DD') {
        return moment(dt / 1e6).format(format)
      }
    },
    mounted () {
      let self = this
      // this.$tqsdk.subscribe_quote('')
      let quoteList = ['KQ.m@SHFE.au', 'KQ.m@SHFE.ag', 'KQ.m@CFFEX.T', 'KQ.m@CFFEX.TF']
      this.$tqsdk.on('rtn_data', function () {
        let ins_list = self.$tqsdk.getByPath(['ins_list'])
        ins_list = ins_list === undefined ? '' : ins_list
        if (ins_list === '' || ins_list.indexOf('KQ.m@SHFE.au') === -1
          || ins_list.indexOf('KQ.m@SHFE.ag') === -1
          || ins_list.indexOf('KQ.m@CFFEX.T') === -1
          || ins_list.indexOf('KQ.m@CFFEX.TF') === -1
        ) {
          ins_list += ((ins_list ? ',' : '') + quoteList.join(','))
          self.$tqsdk.subscribe_quote(ins_list)
        }

        for (let quote of quoteList) {
          let dt = self.$tqsdk.get_by_path(['quotes', quote, 'datetime'])
          self.currentDateTime = (dt && dt > self.currentDateTime) ? dt.slice(0, 19) : self.currentDateTime
        }
      })
    }
  }
</script>
<style lang="scss">
    .replay-control {

    }
</style>
