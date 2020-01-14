<template>
    <div class="about-us">
        <a href="https://doc.shinnytech.com/tqsdk/latest/" target="_blank">
            <img class="logo" alt="Tianqin" src="@/assets/logo.png">
            天勤量化<span v-if="width>100">开发文档</span>
        </a>
        <a href="https://www.shinnytech.com/qa/" target="_blank">
            <Icon type="ios-chatbubbles" />
            天勤<span v-if="width>100">量化</span>论坛
        </a>
    </div>
</template>
<script>
    export default {
      props: {
        width: Number
      }
    }
</script>
<style lang="scss">
    .about-us {
        font-size: 12px;
        border-top: #d3d3d3 solid 2px;
        a {
            color: #222222;
            display: block;
            img.logo {
                width: 16px;
                height: 16px;
                vertical-align: text-bottom;
            }
        }
    }
</style>
