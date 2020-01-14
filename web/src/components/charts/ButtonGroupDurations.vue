<template>
    <div class="tq-button-group-durations">
        <RadioGroup v-model="selectedPeriod" type="button" size="small">
            <Radio v-for="item in periods" :label="item" :key="item"></Radio>
        </RadioGroup>
    </div>
</template>

<script>
  const Periods = {
    '分时': 60 * 1e9,
    '1m': 60 * 1e9,
    '5m': 60 * 5 * 1e9,
    '15m': 60 * 15 * 1e9,
    '30m': 60 * 30 * 1e9,
    '1h': 60 * 60 * 1e9,
    '1d': 60 * 60 * 24 * 1e9
  }
  export default {
    data: function () {
      return {
        periods: Object.keys(Periods),
        selectedPeriod: '',
        selectedDuration: null,
      }
    },
    props: {
        duration: Number
    },
    watch: {
      duration () {
        if (this.duration === this.selectedDuration) return
        let periodsIndex = Object.values(Periods).indexOf(this.duration)
        if (periodsIndex > -1) {
          this.selectedPeriod = Periods[periodsIndex]
          this.selectedDuration = this.duration
        } else {
          this.selectedPeriod = ''
          this.selectedDuration = null
        }
      },
      selectedPeriod () {
        document.querySelectorAll('.tq-button-group-durations input[type=radio]').forEach(item => item.blur())
        this.selectedDuration = Periods[this.selectedPeriod]
        if (this.selectedPeriod && this.selectedDuration) {
          this.$emit('onChangeDuration', this.selectedDuration, this.selectedPeriod)
        }
      }
    }
  }
</script>
<style lang="scss">
    .ivu-row.toolsbar {
        background-color: var(--vscode-editor-background, #fff);
        color: var(--vscode-editor-foreground, #000);
    }
</style>
