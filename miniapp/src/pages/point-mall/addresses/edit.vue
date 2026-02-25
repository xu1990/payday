<template>
  <view class="address-edit-page">
    <view class="header">
      <text class="title">{{ isEdit ? '编辑地址' : '新建地址' }}</text>
    </view>

    <view class="form">
      <!-- 联系人 -->
      <view class="form-item">
        <text class="label">联系人</text>
        <input
          v-model="form.contact_name"
          class="input"
          placeholder="请输入联系人姓名"
          maxlength="20"
        />
      </view>

      <!-- 联系电话 -->
      <view class="form-item">
        <text class="label">联系电话</text>
        <input
          v-model="form.contact_phone"
          type="number"
          class="input"
          placeholder="请输入手机号"
          maxlength="11"
        />
      </view>

      <!-- 省份 -->
      <view class="form-item" @tap="showRegionPicker('province')">
        <text class="label">省份</text>
        <view class="picker-value">
          <text :class="{ placeholder: !form.province_name }">
            {{ form.province_name || '请选择省份' }}
          </text>
          <text class="arrow">›</text>
        </view>
      </view>

      <!-- 城市 -->
      <view class="form-item" @tap="showRegionPicker('city')">
        <text class="label">城市</text>
        <view class="picker-value">
          <text :class="{ placeholder: !form.city_name }">
            {{ form.city_name || '请选择城市' }}
          </text>
          <text class="arrow">›</text>
        </view>
      </view>

      <!-- 区县 -->
      <view class="form-item" @tap="showRegionPicker('district')">
        <text class="label">区县</text>
        <view class="picker-value">
          <text :class="{ placeholder: !form.district_name }">
            {{ form.district_name || '请选择区县' }}
          </text>
          <text class="arrow">›</text>
        </view>
      </view>

      <!-- 详细地址 -->
      <view class="form-item textarea">
        <text class="label">详细地址</text>
        <textarea
          v-model="form.detailed_address"
          class="textarea"
          placeholder="街道、楼牌号等"
          maxlength="200"
          :rows="3"
        />
      </view>

      <!-- 邮政编码 -->
      <view class="form-item">
        <text class="label">邮政编码</text>
        <input
          v-model="form.postal_code"
          type="number"
          class="input"
          placeholder="选填"
          maxlength="6"
        />
      </view>

      <!-- 设为默认地址 -->
      <view class="form-item switch">
        <text class="label">设为默认地址</text>
        <switch
          :checked="form.is_default"
          @change="onDefaultChange"
          color="#667eea"
        />
      </view>
    </view>

    <!-- 保存按钮 -->
    <view class="footer">
      <button class="save-btn" :disabled="saving" @tap="save">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </view>

    <!-- 简单的地区选择器 -->
    <view v-if="showPicker" class="picker-modal" @tap="closePicker">
      <view class="picker-content" @tap.stop>
        <view class="picker-header">
          <text class="picker-title">选择{{ pickerTitle }}</text>
          <text class="picker-close" @tap="closePicker">✕</text>
        </view>
        <scroll-view class="picker-list" scroll-y>
          <view
            v-for="item in pickerOptions"
            :key="item.code"
            class="picker-option"
            @tap="selectOption(item)"
          >
            <text>{{ item.name }}</text>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getAddress,
  createAddress,
  updateAddress,
  type AddressCreate,
  type UserAddress,
} from '@/api/pointShop'

const isEdit = ref(false)
const addressId = ref('')
const saving = ref(false)

const form = ref<AddressCreate>({
  province_code: '',
  province_name: '',
  city_code: '',
  city_name: '',
  district_code: '',
  district_name: '',
  detailed_address: '',
  postal_code: '',
  contact_name: '',
  contact_phone: '',
  is_default: false,
})

// 地区选择器
const showPicker = ref(false)
const pickerType = ref<'province' | 'city' | 'district'>('province')
const pickerTitle = ref('')
const pickerOptions = ref<{ code: string; name: string }[]>([])

// 简化的地区数据（实际应用中应该从API获取）
const regionData = {
  province: [
    { code: '110000', name: '北京市' },
    { code: '310000', name: '上海市' },
    { code: '440000', name: '广东省' },
    { code: '330000', name: '浙江省' },
    { code: '320000', name: '江苏省' },
    { code: '510000', name: '四川省' },
    { code: '420000', name: '湖北省' },
    { code: '370000', name: '山东省' },
    { code: '410000', name: '河南省' },
  ],
  city: {
    '110000': [{ code: '110100', name: '市辖区' }],
    '310000': [{ code: '310100', name: '市辖区' }],
    '440000': [
      { code: '440100', name: '广州市' },
      { code: '440300', name: '深圳市' },
      { code: '440600', name: '佛山市' },
    ],
    '330000': [
      { code: '330100', name: '杭州市' },
      { code: '330200', name: '宁波市' },
    ],
    '320000': [
      { code: '320100', name: '南京市' },
      { code: '320200', name: '无锡市' },
      { code: '320500', name: '苏州市' },
    ],
  },
  district: {
    '440100': [
      { code: '440103', name: '荔湾区' },
      { code: '440106', name: '天河区' },
      { code: '440111', name: '白云区' },
    ],
    '440300': [
      { code: '440304', name: '福田区' },
      { code: '440305', name: '南山区' },
      { code: '440306', name: '宝安区' },
    ],
    '330100': [
      { code: '330102', name: '上城区' },
      { code: '330103', name: '下城区' },
      { code: '330106', name: '西湖区' },
    ],
  },
}

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || {}
  addressId.value = options.id || ''
  isEdit.value = !!addressId.value

  if (isEdit.value) {
    loadAddress()
  }
})

async function loadAddress() {
  try {
    const res = await getAddress(addressId.value)
    const address = res as UserAddress

    form.value = {
      province_code: address.province_code,
      province_name: address.province_name,
      city_code: address.city_code,
      city_name: address.city_name,
      district_code: address.district_code,
      district_name: address.district_name,
      detailed_address: address.detailed_address,
      postal_code: address.postal_code || '',
      contact_name: address.contact_name,
      contact_phone: address.contact_phone,
      is_default: address.is_default,
    }
  } catch (err) {
    console.error('Failed to load address:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  }
}

function onDefaultChange(e) {
  form.value.is_default = e.detail.value
}

function showRegionPicker(type: 'province' | 'city' | 'district') {
  pickerType.value = type

  if (type === 'province') {
    pickerTitle.value = '省份'
    pickerOptions.value = regionData.province
  } else if (type === 'city') {
    if (!form.value.province_code) {
      uni.showToast({
        title: '请先选择省份',
        icon: 'none',
      })
      return
    }
    pickerTitle.value = '城市'
    pickerOptions.value = regionData.city[form.value.province_code] || []
  } else if (type === 'district') {
    if (!form.value.city_code) {
      uni.showToast({
        title: '请先选择城市',
        icon: 'none',
      })
      return
    }
    pickerTitle.value = '区县'
    pickerOptions.value = regionData.district[form.value.city_code] || []
  }

  showPicker.value = true
}

function closePicker() {
  showPicker.value = false
}

function selectOption(item: { code: string; name: string }) {
  const type = pickerType.value

  if (type === 'province') {
    form.value.province_code = item.code
    form.value.province_name = item.name
    // 清空下级选择
    form.value.city_code = ''
    form.value.city_name = ''
    form.value.district_code = ''
    form.value.district_name = ''
  } else if (type === 'city') {
    form.value.city_code = item.code
    form.value.city_name = item.name
    // 清空下级选择
    form.value.district_code = ''
    form.value.district_name = ''
  } else if (type === 'district') {
    form.value.district_code = item.code
    form.value.district_name = item.name
  }

  showPicker.value = false
}

function validateForm() {
  if (!form.value.contact_name.trim()) {
    uni.showToast({ title: '请输入联系人', icon: 'none' })
    return false
  }

  if (!form.value.contact_phone.trim()) {
    uni.showToast({ title: '请输入联系电话', icon: 'none' })
    return false
  }

  if (!/^1\d{10}$/.test(form.value.contact_phone)) {
    uni.showToast({ title: '手机号格式不正确', icon: 'none' })
    return false
  }

  if (!form.value.province_code) {
    uni.showToast({ title: '请选择省份', icon: 'none' })
    return false
  }

  if (!form.value.city_code) {
    uni.showToast({ title: '请选择城市', icon: 'none' })
    return false
  }

  if (!form.value.district_code) {
    uni.showToast({ title: '请选择区县', icon: 'none' })
    return false
  }

  if (!form.value.detailed_address.trim()) {
    uni.showToast({ title: '请输入详细地址', icon: 'none' })
    return false
  }

  return true
}

async function save() {
  if (!validateForm()) return

  try {
    saving.value = true
    uni.showLoading({ title: '保存中...' })

    if (isEdit.value) {
      await updateAddress(addressId.value, form.value)
    } else {
      await createAddress(form.value)
    }

    uni.hideLoading()

    uni.showToast({
      title: isEdit.value ? '更新成功' : '添加成功',
      icon: 'success',
    })

    setTimeout(() => {
      uni.navigateBack()
    }, 500)
  } catch (err) {
    uni.hideLoading()
    uni.showToast({
      title: '保存失败',
      icon: 'none',
    })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.address-edit-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  padding: 30rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #eee;
  text-align: center;
}

.title {
  font-size: 32rpx;
  font-weight: 500;
}

.form {
  margin-top: 20rpx;
  background-color: #fff;
}

.form-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
}

.form-item.textarea {
  align-items: flex-start;
  flex-direction: column;
}

.form-item.switch {
  justify-content: space-between;
}

.label {
  width: 180rpx;
  font-size: 28rpx;
  color: #333;
  flex-shrink: 0;
}

.input {
  flex: 1;
  font-size: 28rpx;
}

.textarea {
  flex: 1;
  margin-top: 20rpx;
  padding: 20rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  font-size: 28rpx;
  min-height: 120rpx;
}

.picker-value {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.picker-value text {
  font-size: 28rpx;
}

.picker-value .placeholder {
  color: #999;
}

.picker-value .arrow {
  font-size: 40rpx;
  color: #999;
}

.footer {
  padding: 30rpx;
  margin-top: 40rpx;
}

.save-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  line-height: 88rpx;
  text-align: center;
}

.save-btn[disabled] {
  opacity: 0.6;
}

/* 地区选择器 */
.picker-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
}

.picker-content {
  width: 100%;
  max-height: 60vh;
  background-color: #fff;
  border-radius: 24rpx 24rpx 0 0;
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
}

.picker-title {
  font-size: 32rpx;
  font-weight: 500;
}

.picker-close {
  font-size: 40rpx;
  color: #999;
  padding: 10rpx;
}

.picker-list {
  max-height: 50vh;
}

.picker-option {
  padding: 30rpx;
  border-bottom: 1rpx solid #f5f5f5;
  font-size: 28rpx;
}
</style>
