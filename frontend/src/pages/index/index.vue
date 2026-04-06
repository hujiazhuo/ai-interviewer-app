<template>
  <view class="index-container">
    <!-- 顶部欢迎区域 -->
    <view class="header-section">
      <view class="welcome">
        <text class="greeting">{{ greeting }}</text>
        <text class="username">{{ userInfo.username || '面试者' }}</text>
      </view>
      <text class="date">{{ currentDate }}</text>
    </view>

    <!-- 文字面试入口 -->
    <view class="section-title">
      <text>文字面试</text>
    </view>

    <view class="position-grid">
      <view
        class="position-card"
        :class="{ selected: selectedPosition === 'backend' && interviewMode === 'text' }"
        @click="selectPosition('backend', 'text')"
      >
        <view class="card-icon">⚙️</view>
        <text class="card-title">后端工程师</text>
        <text class="card-desc">Java/Python/Go</text>
        <view class="card-tags">
          <text class="tag">Java</text>
          <text class="tag">Spring</text>
          <text class="tag">微服务</text>
        </view>
      </view>

      <view
        class="position-card"
        :class="{ selected: selectedPosition === 'algorithm' && interviewMode === 'text' }"
        @click="selectPosition('algorithm', 'text')"
      >
        <view class="card-icon">🧮</view>
        <text class="card-title">大模型应用开发</text>
        <text class="card-desc">LLM/RAG/Agent</text>
        <view class="card-tags">
          <text class="tag">LangChain</text>
          <text class="tag">RAG</text>
          <text class="tag">LLM</text>
        </view>
      </view>

      <view
        class="position-card"
        :class="{ selected: selectedPosition === 'network' && interviewMode === 'text' }"
        @click="selectPosition('network', 'text')"
      >
        <view class="card-icon">🌐</view>
        <text class="card-title">网络工程师</text>
        <text class="card-desc">网络/安全/运维</text>
        <view class="card-tags">
          <text class="tag">TCP/IP</text>
          <text class="tag">网络安全</text>
          <text class="tag">Linux</text>
        </view>
      </view>
    </view>

    <!-- 开始文字面试按钮 -->
    <view class="action-section">
      <button
        class="start-btn text-btn"
        :disabled="!selectedPosition || interviewMode !== 'text' || starting"
        :loading="starting"
        @click="startInterview"
      >
        {{ starting ? '准备中...' : '开始文字面试' }}
      </button>
      <text class="tip">每次面试包含10道题目</text>
    </view>

    <!-- 语音面试入口 -->
    <view class="section-title" style="margin-top: 60rpx;">
      <text>🎤 语音面试（AI面试官语音提问）</text>
    </view>

    <view class="position-grid">
      <view
        class="position-card voice-card"
        :class="{ selected: selectedPosition === 'backend' && interviewMode === 'voice' }"
        @click="selectPosition('backend', 'voice')"
      >
        <view class="card-icon">🎤</view>
        <text class="card-title">后端工程师</text>
        <text class="card-desc">语音+表情分析</text>
        <view class="card-tags">
          <text class="tag voice-tag">Java</text>
          <text class="tag voice-tag">Spring</text>
          <text class="tag voice-tag">微服务</text>
        </view>
      </view>

      <view
        class="position-card voice-card"
        :class="{ selected: selectedPosition === 'algorithm' && interviewMode === 'voice' }"
        @click="selectPosition('algorithm', 'voice')"
      >
        <view class="card-icon">🎤</view>
        <text class="card-title">大模型应用开发</text>
        <text class="card-desc">语音+表情分析</text>
        <view class="card-tags">
          <text class="tag voice-tag">LangChain</text>
          <text class="tag voice-tag">RAG</text>
          <text class="tag voice-tag">LLM</text>
        </view>
      </view>

      <view
        class="position-card voice-card"
        :class="{ selected: selectedPosition === 'network' && interviewMode === 'voice' }"
        @click="selectPosition('network', 'voice')"
      >
        <view class="card-icon">🎤</view>
        <text class="card-title">网络工程师</text>
        <text class="card-desc">语音+表情分析</text>
        <view class="card-tags">
          <text class="tag voice-tag">TCP/IP</text>
          <text class="tag voice-tag">网络安全</text>
          <text class="tag voice-tag">Linux</text>
        </view>
      </view>
    </view>

    <!-- 开始语音面试按钮 -->
    <view class="action-section" style="margin-top: 30rpx;">
      <button
        class="start-btn voice-btn"
        :disabled="!selectedPosition || interviewMode !== 'voice' || starting"
        :loading="starting"
        @click="startVoiceInterview(selectedPosition)"
      >
        {{ starting ? '准备中...' : '🎤 开始语音面试' }}
      </button>
      <text class="tip">AI面试官语音提问+表情分析</text>
      <text class="switch-hint" @click="switchToText">点击临时改为文字输入</text>
    </view>

    <!-- 最近面试记录 -->
    <view class="section-title" v-if="recentInterviews.length > 0">
      <text>最近面试</text>
    </view>

    <view class="recent-list" v-if="recentInterviews.length > 0">
      <view
        class="recent-item"
        v-for="item in recentInterviews"
        :key="item.interview_id"
      >
        <view class="recent-left">
          <text class="recent-position">{{ getPositionName(item.position) }}</text>
          <text class="recent-date">{{ formatDate(item.created_at) }}</text>
        </view>
        <view class="recent-right">
          <view class="recent-score">
            <text class="score-value">{{ item.total_score?.toFixed(1) || '--' }}</text>
            <text class="score-label">分</text>
          </view>
          <view class="delete-btn" @click.stop="deleteInterview(item.interview_id)">
            <text>删除</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/common/api.js'

const selectedPosition = ref('')
const interviewMode = ref('text')  // 'text' | 'voice'
const starting = ref(false)
const recentInterviews = ref([])

const userInfo = computed(() => {
  return uni.getStorageSync('user') || {}
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好，'
  if (hour < 18) return '下午好，'
  return '晚上好，'
})

const currentDate = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`
})

const getPositionName = (position) => {
  const names = {
    backend: '后端工程师',
    algorithm: '大模型应用开发',
    network: '网络工程师'
  }
  return names[position] || position
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const selectPosition = (position, mode) => {
  selectedPosition.value = position
  interviewMode.value = mode
}

const startInterview = async () => {
  if (!selectedPosition.value || interviewMode.value !== 'text') return

  starting.value = true
  try {
    const res = await api.startInterview(selectedPosition.value)
    if (res.success) {
      uni.setStorageSync('currentInterviewId', res.interview_id)
      uni.setStorageSync('currentPosition', selectedPosition.value)
      uni.setStorageSync('interviewMode', 'text')

      // 跳转到文字面试页面
      uni.navigateTo({
        url: `/pages/interview/interview?id=${res.interview_id}&opening=${encodeURIComponent(res.opening)}&firstQuestion=${encodeURIComponent(res.question)}&questionId=${res.question_id}&isPersonalized=${res.is_personalized || false}`
      })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '启动失败', icon: 'none' })
  } finally {
    starting.value = false
  }
}

const startVoiceInterview = async (position) => {
  starting.value = true
  try {
    const res = await api.startVoiceInterview(position)
    if (res.success) {
      uni.setStorageSync('currentInterviewId', res.interview_id)
      uni.setStorageSync('currentPosition', position)
      uni.setStorageSync('interviewMode', 'voice')

      // 跳转到语音面试页面
      uni.navigateTo({
        url: `/pages/interview/interview_voice?id=${res.interview_id}&opening=${encodeURIComponent(res.opening || '')}&openingAudioUrl=${encodeURIComponent(res.opening_audio_url || '')}&firstQuestion=${encodeURIComponent(res.question || '')}&questionId=${res.question_id || ''}&isPersonalized=${res.is_personalized || false}&questionAudioUrl=${encodeURIComponent(res.question_audio_url || '')}`
      })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '启动失败', icon: 'none' })
  } finally {
    starting.value = false
  }
}

const switchToText = () => {
  // 切换到文字面试模式
  interviewMode.value = 'text'
  // 切换到文字面试区域
  uni.pageScrollTo({ scrollTop: 0, duration: 300 })
}

const loadRecentInterviews = async () => {
  try {
    const res = await api.getScoreHistory()
    if (res.success) {
      // 只显示已完成的面试，且限制显示10条
      recentInterviews.value = (res.scores || [])
        .filter(item => item.total_score !== null)
        .slice(0, 10)
    }
  } catch (e) {
    console.error('获取面试记录失败', e)
  }
}

const deleteInterview = async (interviewId) => {
  try {
    await uni.showModal({
      title: '确认删除',
      content: '确定要删除这条面试记录吗？',
      success: async (res) => {
        if (res.confirm) {
          const result = await api.deleteInterview(interviewId)
          if (result.success) {
            uni.showToast({ title: '删除成功', icon: 'success' })
            // 刷新列表
            loadRecentInterviews()
          }
        }
      }
    })
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}

onMounted(() => {
  // 检查登录状态
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.redirectTo({ url: '/pages/login/login' })
    return
  }

  loadRecentInterviews()
})
</script>

<style scoped>
.index-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0 30rpx;
}

.header-section {
  padding: 40rpx 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.welcome {
  display: flex;
  flex-direction: column;
}

.greeting {
  font-size: 28rpx;
  color: #666;
}

.username {
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
  margin-top: 8rpx;
}

.date {
  font-size: 26rpx;
  color: #999;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 30rpx;
}

.position-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20rpx;
}

.position-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 4rpx solid transparent;
  transition: all 0.3s;
}

.position-card.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.card-icon {
  font-size: 60rpx;
  margin-bottom: 16rpx;
}

.card-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.card-desc {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
}

.card-tags {
  display: flex;
  gap: 8rpx;
  margin-top: 16rpx;
  flex-wrap: wrap;
  justify-content: center;
}

.tag {
  font-size: 20rpx;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

.voice-card {
  background: linear-gradient(135deg, #fff 0%, #f0f7ff 100%);
  border: 2rpx solid #48bb78;
}

.voice-card.selected {
  border-color: #48bb78;
  background: linear-gradient(135deg, rgba(72, 187, 120, 0.1), rgba(72, 187, 120, 0.05));
}

.voice-tag {
  color: #48bb78;
  background: rgba(72, 187, 120, 0.1);
}

.voice-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.switch-hint {
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #667eea;
  text-decoration: underline;
}

.text-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-section {
  margin-top: 50rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.start-btn {
  width: 500rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50rpx;
  color: #fff;
  font-size: 36rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 10rpx 30rpx rgba(102, 126, 234, 0.4);
}

.start-btn[disabled] {
  background: #ccc;
  box-shadow: none;
}

.tip {
  font-size: 24rpx;
  color: #999;
  margin-top: 20rpx;
}

.recent-list {
  margin-top: 40rpx;
}

.recent-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-left {
  display: flex;
  flex-direction: column;
}

.recent-position {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
}

.recent-date {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.recent-right {
  display: flex;
  align-items: center;
}

.recent-score {
  display: flex;
  align-items: baseline;
}

.delete-btn {
  margin-left: 20rpx;
  padding: 8rpx 20rpx;
  background: #ff5252;
  border-radius: 20rpx;
  color: #fff;
  font-size: 24rpx;
}

.score-value {
  font-size: 48rpx;
  font-weight: 600;
  color: #667eea;
}

.score-label {
  font-size: 24rpx;
  color: #999;
  margin-left: 4rpx;
}
</style>
