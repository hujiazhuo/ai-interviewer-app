<template>
  <view class="login-container">
    <!-- 背景装饰 -->
    <view class="bg-decoration">
      <view class="circle circle-1"></view>
      <view class="circle circle-2"></view>
      <view class="circle circle-3"></view>
    </view>

    <!-- Logo区域 -->
    <view class="logo-section">
      <view class="logo-icon">AI</view>
      <text class="logo-title">AI面试官</text>
      <text class="logo-subtitle">智能面试 · 让面试更简单</text>
    </view>

    <!-- 登录表单 -->
    <view class="form-section">
      <view class="input-group">
        <view class="input-wrapper">
          <text class="input-icon">👤</text>
          <input
            class="input-field"
            type="text"
            v-model="formData.username"
            placeholder="请输入用户名"
            placeholder-class="placeholder"
          />
        </view>

        <view class="input-wrapper">
          <text class="input-icon">🔒</text>
          <input
            class="input-field"
            :type="showPassword ? 'text' : 'password'"
            v-model="formData.password"
            placeholder="请输入密码"
            placeholder-class="placeholder"
          />
          <text class="password-toggle" @click="showPassword = !showPassword">
            {{ showPassword ? '🙈' : '👁️' }}
          </text>
        </view>
      </view>

      <button class="login-btn" :loading="loading" @click="handleLogin">
        登 录
      </button>

      <view class="footer-links">
        <text class="link" @click="goToRegister">还没有账号？立即注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/common/api.js'

const formData = ref({
  username: '',
  password: ''
})

const showPassword = ref(false)
const loading = ref(false)

const handleLogin = async () => {
  if (!formData.value.username) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!formData.value.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const res = await api.login(formData.value)
    if (res.success) {
      // 保存token
      uni.setStorageSync('token', res.token)
      uni.setStorageSync('user', res.user)
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 1000)
    }
  } catch (e) {
    uni.showToast({ title: e.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 40rpx;
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 300rpx;
  height: 300rpx;
  top: -100rpx;
  right: -100rpx;
}

.circle-2 {
  width: 200rpx;
  height: 200rpx;
  top: 200rpx;
  left: -80rpx;
}

.circle-3 {
  width: 150rpx;
  height: 150rpx;
  bottom: 100rpx;
  right: 50rpx;
}

.logo-section {
  padding-top: 160rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-icon {
  width: 160rpx;
  height: 160rpx;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60rpx;
  font-weight: bold;
  color: #fff;
  box-shadow: 0 20rpx 40rpx rgba(0, 0, 0, 0.2);
}

.logo-title {
  margin-top: 30rpx;
  font-size: 48rpx;
  font-weight: 600;
  color: #fff;
}

.logo-subtitle {
  margin-top: 12rpx;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.form-section {
  margin-top: 80rpx;
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

.login-btn {
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

.login-btn:active {
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
