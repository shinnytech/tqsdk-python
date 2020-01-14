<template>
    <div ref="toolBarContainer" class="tq-buttons-tool-bar-container"
         @mouseleave="onMouseleave"
         @mouseenter="onMouseenter"
         @scroll="onscroll">
        <div class="tq-buttons-tool-bar">
            <transition name="slide-top">
                <div class="scroll-helper top-scroll-helper" v-show="showTopScrollHelper"
                     :style="{height: iconSize - 4 + 'px', padding: '0px ' + (innerIconPadding + outterIconPadding + 2) + 'px'}"
                     @click="scrollTo('top')">
                    <Icon type="ios-arrow-up" :size="iconSize - 4"/>
                </div>
            </transition>
            <transition name="slide-bottom">
                <div class="scroll-helper bottom-scroll-helper" v-show="showBottomScrollHelper"
                     :style="{height: iconSize - 4 + 'px', padding: '0px ' + (innerIconPadding + outterIconPadding + 2) + 'px'}"
                     @click="scrollTo('bottom')">
                    <Icon type="ios-arrow-down" :size="iconSize - 4"/>
                </div>
            </transition>
            <template v-for="aToolsList in toolsListByGroup">
                <div class="button-tool"
                     v-for="tool in aToolsList"
                     :class="{selected: tool.id === selectedId}"
                     :style="{width: size + 'px',
                        height: size + 'px',
                        padding: outterIconPadding + 'px'
                    }"
                     v-bind:key="tool.id">
                    <div class="button-icon-container"
                         @click="clickHandler(tool.id)"
                         :style="{padding: innerIconPadding + 'px'}">
                        <Icon :type="tool.icon" :size="iconSize" :style="getIconStyle(tool)"/>
                    </div>
                </div>
                <div class="divider"></div>
            </template>
        </div>
    </div>
</template>
<script>
  /**
   * 垂直方向 button tool bar
   */
  export default {
    name: 'tq-layout-absolute',
    data () {
      return {
        selectedId: '',
        outterIconPadding: 6,
        innerIconPadding: 3,
        showTopScrollHelper: false,
        showBottomScrollHelper: false
      }
    },
    props: {
      toolsList: {
        type: Array,
        default: []
      },
      size: {
        type: Number,
        default: 34
      },
      selectedColor: {
        type: String,
        default: 'cornflowerblue'
      },
      selectedWeight: {
        type: String,
        default: 'normal'
      }
    },
    computed: {
      iconSize () {
        return this.size - this.outterIconPadding * 2 - this.innerIconPadding * 2
      },
      toolsListByGroup () {
        let groupList = []
        let _toolsListByGroup = []
        for (let i = 0; i < this.toolsList.length; i++) {
          let item = this.toolsList[i]
          let groupIndex = groupList.indexOf(item.group)
          if (groupIndex === -1) {
            groupList.push(item.group)
            _toolsListByGroup.push([])
            groupIndex = groupList.length -1
          }
          _toolsListByGroup[groupIndex].push(item)
        }
        return _toolsListByGroup
      }
    },
    methods: {
      getIconStyle (tool) {
        if (tool.id === this.selectedId) {
          return {
            color: this.selectedColor,
            fontWeight: this.selectedWeight
          }
        }
      },
      onscroll (e) {
        if (e.target.scrollTop === 0) {
          this.showTopScrollHelper = false
        } else {
          this.showTopScrollHelper = true
        }
        if (e.target.clientHeight + e.target.scrollTop === e.target.scrollHeight) {
          this.showBottomScrollHelper = false
        } else {
          this.showBottomScrollHelper = true
        }
      },
      scrollAnimation (ele, start, end, timeout) {
        let intervalTime = 16
        let pxSum = Math.abs(end - start)
        let pxMoveDir = (end - start) / pxSum
        let pxOneTime = 6 * pxMoveDir
        let interval = setInterval(function(){
          start = start + pxOneTime
          start = start * pxMoveDir > end ? end : start
          ele.scroll(0, start)
          if (start === end) clearInterval(interval)
        }, intervalTime)
      },
      scrollTo (to) {
        if (!['top', 'bottom'].includes(to)) return
        let target = this.$refs.toolBarContainer
        let start = target.scrollTop
        let end = to === 'top' ? 0 : target.scrollHeight - target.clientHeight
        this.scrollAnimation(target, start, end, 500)
      },
      onMouseleave() {
        this.showTopScrollHelper = false
        this.showBottomScrollHelper = false
      },
      onMouseenter() {
        this.onscroll({target: this.$refs.toolBarContainer})
      },
      clickHandler (tool_id) {
        this.selectedId = tool_id
        this.$emit("on-click-tool", this.selectedId)
      },
      clear () {
        this.selectedId = ''
      }
    }
  }
</script>
<style lang="scss">
    .tq-buttons-tool-bar-container {
        width: 100%;
        height: 100%;
        overflow-y: scroll;
        &::-webkit-scrollbar {
            display:none
        }
    }
    .tq-buttons-tool-bar {
        display: flex;
        flex-direction: column;
        .button-tool {
            display: flex;
            .button-icon-container {
                border-radius: 4px;
                width: 100%;
                height: 100%;
                &:hover {
                    background-color: rgba(220, 220, 220, 0.8);
                }
            }
            &.selected {
                background-color: #FFF;
                /*.button-icon-container {*/
                    /*&:hover {*/
                        /*background-color: transparent;*/
                    /*}*/
                /*}*/
            }
        }
        .divider:not(:last-child) {
            display: flex;
            height: 1px;
            background-color: #999;
        }
        .scroll-helper {
            position: absolute;
            width: 100%;
            background-color: rgba(33, 33, 33, 0.8);
            color: #FFF;
            padding: auto;
            &.top-scroll-helper {
                top: 0px;
            }
            &.bottom-scroll-helper {
                bottom: 0px;
            }
        }
    }

    .slide-top-enter-active, .slide-top-leave-active,
    .slide-bottom-enter-active, .slide-bottom-leave-active {
        transition: all .3s ease;
    }
    .slide-top-enter, .slide-top-leave-to {
        transform: translateY(-100%);
        opacity: 0;
    }
    .slide-bottom-enter, .slide-bottom-leave-to {
        transform: translateY(100%);
        opacity: 0;
    }
</style>
