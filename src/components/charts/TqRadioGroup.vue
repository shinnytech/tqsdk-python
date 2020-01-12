<template>
    <div class="tq-radio-group">

        <Button v-for="radio in baseRadioList"
                v-bind:key="radio.id"
                size="small"
                :type="selectedId === radio.id ? 'primary' : 'text'"
                @click="clickBtn(radio.id)">
            {{radio.name}}
        </Button>
        <Dropdown v-if="moreRadioList.length > 0" @on-click="clickMoreItem">
            <a href="javascript:void(0)">
                {{moreRadioText}}
                <Icon type="ios-arrow-down"></Icon>
            </a>
            <DropdownMenu slot="list">
                <DropdownItem v-for="mRadio in moreRadioList" v-bind:key="mRadio.id" :name="mRadio.id">{{mRadio.name}}</DropdownItem>
            </DropdownMenu>
        </Dropdown>
    </div>
</template>
<script>
  export default {
    name: 'tq-radio-group',
    data () {
      return {
        baseRadioList: [],
        moreRadioList: [],
        moreRadioText: '更多',
        selectedId: ''
      }
    },
    props: {
      options: Array
      // level : 'base' 'more'
      // id
      // name
      // selected
    },
    methods: {
      clickBtn (itemId) {
        this.selectedId = itemId
        this.$emit('changeSelectId', itemId)
      },
      clickMoreItem (itemId) {
        this.moreRadioText = itemId
        this.selectedId = itemId
        this.$emit('changeSelectId', itemId)
      }
    },
    created() {
      for (let i = 0; i < this.options.length; i++ ){
        let radio = this.options[i]
        if (radio.level === 'more') {
          this.moreRadioList.push({
            id: radio.id,
            name: radio.name,
            selected: false
          })
        } else {
          this.baseRadioList.push({
            id: radio.id,
            name: radio.name,
            selected: false
          })
        }
      }
    }
  }
</script>
<style lang="scss">
    .tq-radio-group {
        a {
            color: inherit;
        }
    }
</style>
