<template>
  <view class="legal-page">
    <view class="container">
      <view class="header">
        <text class="title">用户协议</text>
        <text class="update-date">更新日期：2024年1月1日</text>
      </view>

      <view class="content">
        <view class="section">
          <text class="section-title">1. 服务条款</text>
          <text class="section-text">
            欢迎使用薪日PayDay小程序！本协议是您与薪日PayDay之间就使用小程序服务所订立的协议。
            请您在注册成为用户前，仔细阅读本协议，尤其是免除或限制责任的条款。
          </text>
        </view>

        <view class="section">
          <text class="section-title">2. 账户注册</text>
          <text class="section-text">
            2.1 您需要通过微信授权登录使用本小程序服务。您确认并承诺，您提供的注册信息真实、准确、完整。
            2.2 您应对您的账户和密码安全负全部责任，因您保管不善可能导致账户被盗用。
            2.3 您不得将账户出售、赠与、借用、租用、转让或以其他方式许可他人使用。
          </text>
        </view>

        <view class="section">
          <text class="section-title">3. 用户行为规范</text>
          <text class="section-text">
            3.1 您在使用本服务时须遵守法律法规，不得利用本服务从事违法活动。
            3.2 禁止发布以下内容：
            (1) 反对宪法所确定的基本原则的；
            (2) 危害国家安全，泄露国家秘密，颠覆国家政权，破坏国家统一的；
            (3) 损害国家荣誉和利益的；
            (4) 煽动民族仇恨、民族歧视，破坏民族团结的；
            (5) 破坏国家宗教政策，宣扬邪教和封建迷信的；
            (6) 散布谣言，扰乱社会秩序，破坏社会稳定的；
            (7) 散布淫秽、色情、赌博、暴力、凶杀、恐怖或者教唆犯罪的；
            (8) 侮辱或者诽谤他人，侵害他人合法权益的。
          </text>
        </view>

        <view class="section">
          <text class="section-title">4. 知识产权</text>
          <text class="section-text">
            4.1 本小程序中的所有内容，包括但不限于文字、图片、音频、视频、软件、程序、版面设计等，
            均由薪日PayDay或相关权利人依法享有知识产权。
            4.2 用户在使用本服务时发布的内容，您保证对该内容享有合法权利或已获得相应授权。
          </text>
        </view>

        <view class="section">
          <text class="section-title">5. 免责声明</text>
          <text class="section-text">
            5.1 本小程序仅提供信息分享平台，用户发布的内容仅代表其个人观点。
            5.2 薪日PayDay不对用户发布内容的真实性、准确性、完整性负责。
            5.3 因不可抗力、网络故障、系统维护等原因导致服务中断或延迟，我们不承担相应责任。
          </text>
        </view>

        <view class="section">
          <text class="section-title">6. 隐私保护</text>
          <text class="section-text">
            我们重视您的隐私保护。关于我们如何收集、使用、存储您的个人信息，请参见《隐私政策》。
          </text>
        </view>

        <view class="section">
          <text class="section-title">7. 协议修改</text>
          <text class="section-text">
            我们有权根据需要修改本协议条款。修改后的协议一旦公布即代替原协议。
            您可随时查阅最新协议。如您不同意修改后的协议，可停止使用本服务。
            继续使用则视为接受修改后的协议。
          </text>
        </view>

        <view class="section">
          <text class="section-title">8. 法律适用</text>
          <text class="section-text">
            本协议的订立、执行和解释均适用中华人民共和国法律。
            如发生纠纷，双方应友好协商解决；协商不成的，任何一方可向我们所在地人民法院提起诉讼。
          </text>
        </view>

        <view class="section">
          <text class="section-title">9. 联系我们</text>
          <text class="section-text">
            如您对本协议有任何疑问，请通过小程序内的反馈功能或客服联系方式与我们联系。
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
// 用户协议页面
</script>

<style scoped lang="scss">
.legal-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.container {
  padding: 40rpx;
}

.header {
  text-align: center;
  margin-bottom: 60rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 16rpx;
}

.update-date {
  display: block;
  font-size: 28rpx;
  color: #999;
}

.content {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 40rpx;
}

.section {
  margin-bottom: 50rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.section-text {
  display: block;
  font-size: 28rpx;
  line-height: 1.8;
  color: #666;
  text-align: justify;
}
</style>
