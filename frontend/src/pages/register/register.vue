<template>
  <view class="register-container">
    <view class="header">
      <text class="back-btn" @click="goBack">←</text>
      <text class="title">注册账号</text>
    </view>

    <view class="form-section">
      <view class="input-group">
        <view class="input-wrapper">
          <text class="input-icon">👤</text>
          <input
            class="input-field"
            type="text"
            v-model="formData.username"
            placeholder="请输入用户名（6-20位）"
            placeholder-class="placeholder"
          />
        </view>

        <view class="input-wrapper">
          <text class="input-icon">🔒</text>
          <input
            class="input-field"
            :type="showPassword ? 'text' : 'password'"
            v-model="formData.password"
            placeholder="请输入密码（6位以上）"
            placeholder-class="placeholder"
          />
          <text class="password-toggle" @click="showPassword = !showPassword">
            {{ showPassword ? '🙈' : '👁️' }}
          </text>
        </view>

        <view class="input-wrapper">
          <text class="input-icon">🔒</text>
          <input
            class="input-field"
            :type="showPassword ? 'text' : 'password'"
            v-model="formData.confirmPassword"
            placeholder="请确认密码"
            placeholder-class="placeholder"
          />
        </view>
      </view>

      <button class="register-btn" :loading="loading" @click="handleRegister">
        注 册
      </button>

      <view class="footer-links">
        <text class="link" @click="goToLogin">已有账号？立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/common/api.js'

const formData = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const showPassword = ref(false)
const loading = ref(false)

const handleRegister = async () => {
  if (!formData.value.username) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (formData.value.username.length < 6 || formData.value.username.length > 20) {
    uni.showToast({ title: '用户名需6-20位', icon: 'none' })
    return
  }
  if (!formData.value.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }
  if (formData.value.password.length < 6) {
    uni.showToast({ title: '密码需6位以上', icon: 'none' })
    return
  }
  if (formData.value.password !== formData.value.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const res = await api.register({
      username: formData.value.username,
      password: formData.value.password
    })
    if (res.success) {
      uni.showToast({ title: '注册成功', icon: 'success' })
      setTimeout(() => {
        uni.navigateBack()
      }, 1500)
    }
  } catch (e) {
    uni.showToast({ title: e.message || '注册失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  uni.navigateBack()
}

const goToLogin = () => {
  uni.navigateBack()
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 40rpx;
}

.header {
  padding-top: 80rpx;
  padding-bottom: 40rpx;
  display: flex;
  align-items: center;
}

.back-btn {
  font-size: 50rpx;
  color: #fff;
  padding: 20rpx;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 40rpx;
  font-weight: 600;
  color: #fff;
  margin-right: 80rpx;
}

.form-section {
  background: #fff;
  border-radius: 32rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 16rpx;
  padding: 0 30rpx;
  height: 100rpx;
  border: 2rpx solid transparent;
  transition: all 0.3s;
}

.input-wrapper:focus-within {
  border-color: #667eea;
  background: #fff;
}

.input-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.input-field {
  flex: 1;
  font-size: 30rpx;
  color: #333;
}

.placeholder {
  color: #999;
}

.password-toggle {
  font-size: 36rpx;
  padding: 10rpx;
}

.register-btn {
  margin-top: 50rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50rpx;
  color: #fff;
  font-size: 34rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 10rpx 30rpx rgba(102, 126, 234, 0.4);
}

.register-btn:active {
  transform: scale(0.98);
}

.footer-links {
  margin-top: 40rpx;
  text-align: center;
}

.link {
  color: #667eea;
  font-size: 28rpx;
}
</style>
