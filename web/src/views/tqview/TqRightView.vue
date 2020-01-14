<template>
    <div class="tq-right-view">
        <div class="right-pane" :style="{width: width + 'px'}">
            <tq-layout-area class="right-pane-pages"
                            :height="height"
                            :width="pagesWidth"
                            :otherStyle="{backgroundColor: '#FEFEFE'}"
                            v-if="paneOpened">
                {{selectedBtnToolId}}
            </tq-layout-area>
            <tq-layout-area class="right-pane-tools"
                            horizontalAlign="right"
                            :right=0
                            :height="height"
                            :width="toolsBarWidth"
            :otherStyle="{backgroundColor: '#F0F0F0'}">
                <buttons-tool-bar ref="toolsBar"
                                  :size="toolsBarWidth"
                                  selectedColor="#7999E0"
                                  selectedWeight="bold"
                                  :toolsList="toolsList"
                                  @on-click-tool="onClickTool">
                </buttons-tool-bar>
            </tq-layout-area>
        </div>
        <div class="right-resize-tool" v-if="paneOpened" @click="toggleRightPane">
            <Icon v-if="paneOpened" type="ios-arrow-forward" />
            <Icon v-else type="ios-arrow-back" />
        </div>
    </div>
</template>
<script>
  import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
  import ButtonsToolBar from '@/components/layouts/ButtonsToolBar.vue'
  let icons = [
    'ios-alarm-outline',
    'ios-albums-outline',
    'ios-aperture-outline',
    'ios-apps-outline',
    'ios-backspace-outline',
    'ios-attach',
    'ios-bulb-outline',
    'ios-calculator-outline',
    'ios-card-outline',
    'ios-chatbubbles-outline',
    'ios-calendar-outline',
    'ios-add-circle-outline',
    'ios-checkmark-circle-outline',
    'ios-cloud-done-outline',
    'ios-color-palette-outline',
    'ios-download-outline',
    'ios-close-circle-outline',
    'ios-cloud-circle-outline',
    'ios-help-circle-outline',
    'ios-information-circle-outline',
    'ios-refresh-circle-outline',
    'ios-remove-circle-outline',

  ]
  export default {
    name: 'tq-right-view',
    components: {
      TqLayoutArea,
      ButtonsToolBar
    },
    props: {
      width: Number,
      pagesWidth: Number,
      toolsBarWidth: Number
    },
    data () {
      return {
        height: this.$root.windowHeight,
        paneOpened: false,
        selectedBtnToolId: '',
        toolsList: [{
          id: 'quotesList',
          type: 'icon',
          group: 'group_a',
          icon: 'ios-list-box-outline'
        }, {
          id: 'quoteInfo',
          type: 'icon',
          group: 'group_a',
          icon: 'ios-heart-outline'
        }]

      }
    },
    methods: {
      toggleRightPane () {
        this.paneOpened = !this.paneOpened
        if (!this.paneOpened) this.$refs.toolsBar.clear()
        if (this.paneOpened) this.$emit('onopen')
        else this.$emit('onclose')
      },
      computeLayouts () {
        this.height = this.$root.windowHeight
      },
      onClickTool (tool_id) {
        if (this.paneOpened) {
          if (this.selectedBtnToolId === tool_id) {
            this.toggleRightPane()
            this.selectedBtnToolId = ''
          } else {
            this.selectedBtnToolId = tool_id
          }
        } else {
          this.toggleRightPane()
          this.selectedBtnToolId = tool_id
        }
      }
    },
    created () {
      this.$eventHub.$on('window_resize', this.computeLayouts)
      // TODO 假设的 btnlist
      for (let icon of icons) {
        this.toolsList.push({
          id: icon,
          type: 'icon',
          icon: icon,
          group: 'test'
        })
      }
    }
  }
</script>
<style lang="scss">
    .right-resize-tool {
        position: absolute;
        bottom: 100px;
        left: -4px;
        height: 26px;
        width: 8px;
        color: #A0A0A0;
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        background-color: #FEFEFE;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 10px;
    }
    .tq-right-view, .right-pane {
        height: 100%;
    }
</style>
