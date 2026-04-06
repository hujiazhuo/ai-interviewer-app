<template>
  <view class="interview-container">
    <!-- 顶部进度 -->
    <view class="progress-bar">
      <view class="progress-info">
        <text class="position-name">{{ positionName }}</text>
        <text class="progress-text">第 {{ currentQuestion }} / 10 题</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: (currentQuestion / 10 * 100) + '%' }"></view>
      </view>
      <view class="end-btn" @click="confirmEndInterview" v-if="!showResult">
        <text>结束面试</text>
      </view>
    </view>

    <!-- 面试官头像 -->
    <view class="interviewer-section">
      <view class="interviewer-avatar">🤖</view>
      <view class="interviewer-bubble" v-if="currentMessage">
        <text class="message-text">{{ currentMessage }}</text>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view class="message-list" scroll-y :scroll-top="scrollTop">
      <!-- 开场白 -->
      <view class="message-item interviewer" v-if="openingShown && opening">
        <view class="message-avatar">🤖</view>
        <view class="message-content">
          <text class="message-text">{{ opening }}</text>
        </view>
      </view>

      <!-- 消息列表 -->
      <view
        v-for="(item, index) in messages"
        :key="index"
      >
        <!-- 面试官问题 -->
        <view class="message-item interviewer" v-if="item.question">
          <view class="message-avatar">🤖</view>
          <view class="message-content">
            <view class="question-header">
              <text class="question-source" :class="{ 'personalized': item.isPersonalized }">
                {{ item.isPersonalized ? '📝 个性化题目' : '📚 知识库题目' }}
              </text>
            </view>
            <text class="message-text">{{ item.question }}</text>
          </view>
        </view>

        <!-- 用户回答 -->
        <view class="message-item user" v-if="item.answer">
          <view class="message-content user-content">
            <text class="message-text">{{ item.answer }}</text>
          </view>
          <view class="message-avatar user-avatar">👤</view>
        </view>

        <!-- 面试官点评 -->
        <view class="message-item interviewer" v-if="item.comment">
          <view class="message-avatar">🤖</view>
          <view class="message-content">
            <text class="message-label">点评：</text>
            <text class="message-text">{{ item.comment }}</text>
            <view class="correct-answer" v-if="item.correctAnswer">
              <text class="label">参考答案：</text>
              <text class="answer-text">{{ item.correctAnswer }}</text>
            </view>
            <view class="score-badge" v-if="item.score">
              <text>得分：{{ item.score.toFixed(1) }}/10</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 滚动锚点 -->
      <view id="scrollBottom"></view>
    </scroll-view>

    <!-- 输入区域（固定在页面底部） -->
    <view class="input-section" v-if="!isFinished">
      <view class="input-wrapper">
        <textarea
          class="answer-input"
          v-model="answerText"
          placeholder="请输入你的回答..."
          placeholder-class="placeholder"
          :disabled="isSubmitting"
          :maxlength="3000"
        />
      </view>
      <button
        class="submit-btn"
        :disabled="!answerText.trim() || isSubmitting"
        :loading="isSubmitting"
        @click="submitAnswer"
      >
        {{ isSubmitting ? '提交中...' : '提交回答' }}
      </button>
    </view>

    <!-- 结束按钮 -->
    <view class="finish-section" v-if="isFinished && !showResult">
      <button class="finish-btn" @click="viewResult">
        查看面试结果
      </button>
    </view>

    <!-- 面试结果 -->
    <view class="result-section" v-if="showResult">
      <view class="result-card">
        <text class="result-title">面试完成</text>
        <view class="result-score">
          <text class="score-value">{{ finalScore?.toFixed(1) || '--' }}</text>
          <text class="score-label">综合得分（满分10分）</text>
        </view>
        <view class="result-dimensions">
          <view class="dimension-item" v-for="(value, key) in dimensionScores" :key="key">
            <text class="dim-name">{{ getDimensionName(key) }}</text>
            <view class="dim-bar">
              <view class="dim-fill" :style="{ width: (value * 10) + '%' }"></view>
            </view>
            <text class="dim-value">{{ value.toFixed(1) }}/10</text>
          </view>
        </view>
        <button class="back-btn" @click="backToHome">
          返回首页
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '@/common/api.js'

const interviewId = ref('')
const positionName = ref('')
const opening = ref('')
const currentQuestion = ref(1)
const answerText = ref('')
const isSubmitting = ref(false)
const isFinished = ref(false)
const showResult = ref(false)
const openingShown = ref(false)
const scrollTop = ref(0)

const messages = ref([])
const finalScore = ref(0)
const dimensionScores = ref({})

const currentMessage = computed(() => {
  if (!openingShown.value && opening.value) {
    return opening.value
  }
  return ''
})

const getDimensionName = (key) => {
  const names = {
    technical: '技术能力',
    communication: '沟通表达',
    problem_solving: '问题解决',
    experience: '项目经验',
    logical_thinking: '逻辑思维'
  }
  return names[key] || key
}

const scrollToBottom = () => {
  nextTick(() => {
    // 使用一个足够大的 scroll-top 值来滚动到底部
    scrollTop.value = 99999
  })
}

const submitAnswer = async () => {
  if (!answerText.value.trim()) return

  isSubmitting.value = true

  // 找到最后一个问题（当前要回答的问题）
  const lastQuestionIndex = messages.value.findLastIndex(m => m.question && !m.answer)
  const currentQuestionId = lastQuestionIndex >= 0 ? messages.value[lastQuestionIndex].questionId : ''

  // 添加用户回答
  messages.value.push({
    question: null,
    questionId: null,
    answer: answerText.value,
    comment: null,
    correctAnswer: null,
    score: null
  })

  const userAnswer = answerText.value
  answerText.value = ''

  scrollToBottom()

  try {
    // 提交回答
    const res = await api.submitAnswer(interviewId.value, userAnswer)
    console.log('submitAnswer response:', JSON.stringify(res))

    if (res.success) {
      // 更新最后一条消息的点评
      if (messages.value.length > 0) {
        const lastMsg = messages.value[messages.value.length - 1]
        lastMsg.comment = res.comment
        lastMsg.correctAnswer = res.correct_answer
        lastMsg.score = res.score
      }

      scrollToBottom()

      if (res.is_finished) {
        // 面试结束
        isFinished.value = true
        await endInterview()
      } else {
        // 获取下一题
        await getNextQuestion()
      }
    }
  } catch (e) {
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
}

const getNextQuestion = async () => {
  try {
    const res = await api.getNextQuestion(interviewId.value)
    console.log('getNextQuestion response:', JSON.stringify(res))
    if (res.success && res.question) {
      // 把新问题加到消息列表
      messages.value.push({
        question: res.question,
        questionId: res.question_id,
        answer: null,
        comment: null,
        correctAnswer: null,
        score: null,
        isPersonalized: res.is_personalized || false
      })
      currentQuestion.value = res.question_count || 1
      scrollToBottom()
    } else if (res.is_finished) {
      // 面试结束
      isFinished.value = true
      await endInterview()
    } else {
      console.warn('getNextQuestion returned no question:', res)
      uni.showToast({ title: '获取问题失败，请重试', icon: 'none' })
    }
  } catch (e) {
    console.error('getNextQuestion error:', e)
    uni.showToast({ title: e.message || '获取问题失败', icon: 'none' })
  }
}

const endInterview = async () => {
  try {
    const res = await api.endInterview(interviewId.value)
    if (res.success) {
      finalScore.value = res.total_score
      dimensionScores.value = res.dimension_scores
    }
  } catch (e) {
    console.error('结束面试失败', e)
  }
}

const confirmEndInterview = () => {
  uni.showModal({
    title: '确认结束面试',
    content: '你确定要退出此次面试吗？面试结果将会保存。',
    confirmText: '确定结束',
    cancelText: '继续面试',
    success: async (res) => {
      if (res.confirm) {
        isFinished.value = true
        await endInterview()
      }
    }
  })
}

const viewResult = () => {
  showResult.value = true
}

const backToHome = () => {
  uni.switchTab({ url: '/pages/index/index' })
}

onMounted(() => {
  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || {}

  interviewId.value = options.id || ''
  opening.value = decodeURIComponent(options.opening || '')

  // 把第一道题加到消息列表
  const firstQuestion = decodeURIComponent(options.firstQuestion || '')
  const firstQuestionId = options.questionId || ''
  const firstIsPersonalized = options.isPersonalized === 'true'
  if (firstQuestion) {
    messages.value.push({
      question: firstQuestion,
      questionId: firstQuestionId,
      answer: null,
      comment: null,
      correctAnswer: null,
      score: null,
      isPersonalized: firstIsPersonalized
    })
  }

  // 获取岗位名称
  const position = uni.getStorageSync('currentPosition') || ''
  const positionNames = {
    backend: '后端工程师',
    algorithm: '大模型应用开发',
    network: '网络工程师'
  }
  positionName.value = positionNames[position] || position

  // 显示开场白
  setTimeout(() => {
    openingShown.value = true
    scrollToBottom()
  }, 500)
})
</script>

<style scoped>
.interview-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 200rpx;
}

.progress-bar {
  background: #fff;
  padding: 30rpx;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
  flex: 1;
}

.position-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.progress-text {
  font-size: 26rpx;
  color: #667eea;
}

.progress-track {
  height: 8rpx;
  background: #eee;
  border-radius: 4rpx;
  flex: 1;
  margin-right: 20rpx;
}

.end-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 8rpx 24rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4rpx;
  transition: width 0.3s;
}

.interviewer-section {
  padding: 30rpx;
  display: flex;
  align-items: flex-start;
}

.interviewer-avatar {
  width: 80rpx;
  height: 80rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  flex-shrink: 0;
}

.interviewer-bubble {
  margin-left: 20rpx;
  background: #fff;
  padding: 24rpx;
  border-radius: 16rpx;
  border-top-left-radius: 4rpx;
  max-width: 500rpx;
}

.message-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.6;
  user-select: text;
  -webkit-user-select: text;
}

.question-header {
  margin-bottom: 12rpx;
}

.question-source {
  font-size: 22rpx;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

.question-source.personalized {
  color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
}

.message-list {
  padding: 0 30rpx;
  padding-bottom: 280rpx;
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
}

.message-item.interviewer {
  justify-content: flex-start;
}

.message-item.user {
  justify-content: flex-end;
}

.message-avatar {
  width: 70rpx;
  height: 70rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  flex-shrink: 0;
}

.interviewer .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.user-avatar {
  background: #ddd;
}

.message-content {
  max-width: 500rpx;
  padding: 24rpx;
  border-radius: 16rpx;
  margin: 0 16rpx;
}

.interviewer .message-content {
  background: #fff;
  border-top-left-radius: 4rpx;
}

.user-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-top-right-radius: 4rpx;
}

.message-label {
  font-size: 26rpx;
  color: #667eea;
  font-weight: 600;
  display: block;
  margin-bottom: 8rpx;
}

.correct-answer {
  margin-top: 16rpx;
  padding: 16rpx;
  background: #f5f7fa;
  border-radius: 8rpx;
}

.correct-answer .label {
  font-size: 24rpx;
  color: #4CAF50;
  font-weight: 600;
}

.answer-text {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  display: block;
  margin-top: 8rpx;
}

.score-badge {
  margin-top: 16rpx;
  display: inline-block;
  padding: 8rpx 20rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
  color: #fff;
  font-size: 26rpx;
  font-weight: 600;
}

.input-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.input-wrapper {
  background: #f5f7fa;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}

.answer-input {
  width: 100%;
  min-height: 120rpx;
  font-size: 30rpx;
  color: #333;
  line-height: 1.5;
}

.placeholder {
  color: #999;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.submit-btn[disabled] {
  background: #ccc;
}

.finish-section,
.result-section {
  padding: 30rpx;
}

.finish-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.result-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
}

.result-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
  display: block;
}

.result-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 40rpx 0;
}

.result-score .score-value {
  font-size: 100rpx;
  font-weight: 700;
  color: #667eea;
}

.result-score .score-label {
  font-size: 28rpx;
  color: #999;
}

.result-dimensions {
  margin-bottom: 40rpx;
}

.dimension-item {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.dim-name {
  width: 140rpx;
  font-size: 26rpx;
  color: #666;
}

.dim-bar {
  flex: 1;
  height: 16rpx;
  background: #eee;
  border-radius: 8rpx;
  margin: 0 20rpx;
}

.dim-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8rpx;
}

.dim-value {
  width: 80rpx;
  font-size: 26rpx;
  color: #667eea;
  text-align: right;
}

.back-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}
</style>
