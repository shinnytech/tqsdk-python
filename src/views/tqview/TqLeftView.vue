<template>
    <div class="tq-left-view">
        <tq-layout-area :width="width" :height="width"
            :otherStyle="{backgroundColor: '#FEFEFE',borderBottom: '1px solid #E0E0E0'}">
                <img class="logo" alt="Tianqin" src="@/assets/logo.png"
                :style="{padding: '4px',
                          width: this.width + 'px',
                          height: this.width + 'px'}">
        </tq-layout-area>
        <tq-layout-area :width="width" :top="width" :height="bottomHeight"
                        :otherStyle="{backgroundColor: '#FEFEFE'}">
            <buttons-tool-bar ref="toolsBar" :size="width" :toolsList="toolsList" @on-click-tool="onClickTool">
            </buttons-tool-bar>
        </tq-layout-area>
    </div>
</template>
<script>
  import TqLayoutArea from '@/components/layouts/TqLayoutArea.vue'
  import ButtonsToolBar from '@/components/layouts/ButtonsToolBar.vue'
  export default {
    name: 'tq-left-view',
    components: {
      TqLayoutArea,
      ButtonsToolBar
    },
    props: {
      width: Number,
    },
    data () {
      return {
        bottomHeight: this.$root.windowHeight - this.width,
        toolsList: [{
          id: 'quotesList',
          type: 'icon',
          group: 'a',
          icon: 'md-arrow-round-up'
        }, {
          id: 'quoteInfo',
          type: 'icon',
          group: 'a',
          icon: 'md-add'
        }, {
          id: 'theme',
          type: 'icon',
          group: 'b',
          icon: 'md-contrast'
        }]
      }
    },
    methods: {
      computeLayouts () {
        this.bottomHeight = this.$root.windowHeight - this.width
      },
      onClickTool (tool_id) {
        if (tool_id === 'theme') {
            this.$eventHub.$emit('changeTheme')
        }
      }
    },
    created () {
      this.$eventHub.$on('window_resize', this.computeLayouts)
    }
  }
</script>
