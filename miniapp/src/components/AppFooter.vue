<script setup lang="ts">
function handleClickGithub() {
  // #ifdef H5
  // H5环境可以直接打开链接
  window.open('https://github.com/uni-helper/create-uni', '_blank')
  // #endif

  // #ifdef MP-WEIXIN
  // 微信小程序环境：复制链接到剪贴板
  uni.setClipboardData({
    data: 'https://github.com/uni-helper/create-uni',
    success: () => {
      uni.showToast({
        icon: 'none',
        title: '链接已复制，请在浏览器打开',
      })
    },
  })
  // #endif
}
</script>

<template>
  <view class="footer" @click="handleClickGithub">
    <image class="uni-helper-github__image" src="/static/github.svg" />
  </view>
</template>

<style>
.footer {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  color: #888;
}
.uni-helper-github__image {
  display: inline-block;
  height: 1em;
  width: 1em;
}
</style>
