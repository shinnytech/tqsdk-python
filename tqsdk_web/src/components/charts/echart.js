import _object from 'lodash/object'
import ECharts from 'echarts'

(function () {
  const throttle = function (type, name, obj) {
    obj = obj || window
    let running = false
    let func = function () {
      if (running) { return }
      running = true
      requestAnimationFrame(function () {
        obj.dispatchEvent(new CustomEvent(name))
        running = false
      })
    }
    obj.addEventListener(type, func)
  }
  /* init - you can init any event */
  throttle('resize', 'optimizedResize')
})()

export default {
  name: 'v-echart',

  render (h) {
    const data = {
      staticClass: 'v-chart',
      style: this.canvasStyle,
      ref: 'canvas',
      on: this.$listeners
    }
    return h('div', data)
  },

  props: {
    // args of  ECharts.init(dom, theme, opts)
    width: { type: String, default: 'auto' },
    height: { type: String, default: '400px' },
    // instace.setOption
    pathOption: [Object, Array], // defaultOption
    // resize delay
    widthChangeDelay: {
      type: Number,
      default: 450
    }
  },

  data: () => ({
    chartInstance: null,
    _defaultOption: {
      animation: false,
      tooltip: {
        show: true
      },
      title: {
        show: true,
        textStyle: {
          fontSize: '16px',
          color: 'rgba(0, 0, 0 , .87)',
          fontFamily: 'sans-serif'
        }
      },
      grid: {
        containLabel: true
      },
      xAxis: {
        show: true,
        type: 'category',
        axisLine: {
          lineStyle: {
            color: 'rgba(0, 0, 0 , .24)'
          }
        },
        axisTick: {
          show: true,
          alignWithLabel: true,
          lineStyle: {
            show: true,
            color: 'rgba(0, 0, 0 , .24)'
          }
        },
        axisLabel: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(0, 0, 0 , .24)'
          }
        }
      },
      yAxis: {
        show: true,
        type: 'value',
        max: 'dataMax',
        min: 'dataMin',
        axisLine: {
          lineStyle: {
            color: 'rgba(0, 0, 0 , .24)'
          }
        },
        axisLabel: {
          show: false,
          color: 'rgba(0, 0, 0 , .24)'
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(0, 0, 0 , .24)'
          }
        },
        axisTick: {
          show: true,
          lineStyle: {
            show: true,
            color: 'rgba(0, 0, 0 , .54)'
          }
        }
      },
      series: [{
        type: 'line'
      }]
    }
  }),

  computed: {
    canvasStyle () {
      return {
        width: this.width,
        height: this.height
      }
    }
  },

  methods: {
    init () {
      // set
      if (this.pathOption) {
        this.pathOption.forEach((p) => {
          _object.set(this.$data._defaultOption, p[0], p[1])
        })
      }
      this.chartInstance = ECharts.init(this.$refs.canvas)
      this.chartInstance.setOption(this.$data._defaultOption)
      window.addEventListener('optimizedResize', (e) => {
        setTimeout(_ => {
          this.chartInstance.resize()
        }, this.widthChangeDelay)
      })
    },
    showLoadPercent (int = 0, isShow = true) {
      if (isShow && int < 100) {
        int = Math.max(int, 0)
        this.chartInstance.showLoading('default', {
          text: '数据已加载 ' + int + '%',
          color: '#c23531',
          textColor: '#000',
          maskColor: 'rgba(255, 255, 255, 0.8)',
          zlevel: 0
        })
      } else {
        this.chartInstance.hideLoading()
      }
    },
    update (option) {
      this.chartInstance.setOption(option)
    },
    resize () {
      this.chartInstance.resize()
    },
    clean () {
      window.removeEventListener('resize', this.chartInstance.resize)
      this.chartInstance.clear()
      // this.chartInstance.dispose();
    }
  },

  mounted () {
    this.init()
  },

  beforeDestroy () {
    this.clean()
  }
}
