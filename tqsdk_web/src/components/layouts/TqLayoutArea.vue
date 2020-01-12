<template>
    <div class="tq-layout-absolute" :style="computedStyle">
        <slot></slot>
    </div>
</template>
<script>
  export default {
    name: 'tq-layout-absolute',
    data () {
      return {}
    },
    props: {
      horizontalAlign: {
        type: String,
        default: 'left'
      },
      verticalAlign: {
        type: String,
        default: 'top'
      },
      top: {
        type: Number,
        default: 0
      },
      left: {
        type: Number,
        default: 0
      },
      bottom: {
        type: Number,
        default: 0
      },
      right: {
        type: Number,
        default: 0
      },
      width: {
        type: Number,
        default: 0
      },
      height: {
        type: Number,
        default: 0
      },
      otherStyle: {
        type: Object,
        default: () => {}
      }
    },
    computed: {
      computedStyle () {
        let styleObject = {
          width: this.width + 'px',
          height: this.height + 'px',
        }
        styleObject[this.horizontalAlign] = this[this.horizontalAlign] + 'px'
        styleObject[this.verticalAlign] = this[this.verticalAlign] + 'px'
        return Object.assign(styleObject, this.otherStyle)
      }
    }
  }
</script>
<style>
    .tq-layout-absolute {
        position: absolute;
    }
</style>
