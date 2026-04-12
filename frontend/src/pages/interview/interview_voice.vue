<template>
  <view class="interview-container">
    <!-- 开始面试按钮（满足移动端自动播放策略） -->
    <view class="start-overlay" v-if="!interviewStarted">
      <view class="start-card">
        <text class="start-title">🎤 AI语音面试</text>
        <text class="start-desc">{{ positionName }}</text>
        <text class="start-tip">请确保麦克风和摄像头已授权</text>
        <button class="start-btn" @click="startInterview">开始面试</button>
      </view>
    </view>

    <!-- 顶部进度 -->
    <view class="progress-bar" v-if="interviewStarted">
      <view class="progress-info">
        <text class="position-name">{{ positionName }} 🔊</text>
        <text class="progress-text">第 {{ currentQuestion }} / 10 题</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: (currentQuestion / 10 * 100) + '%' }"></view>
      </view>
      <view class="end-btn" @click="confirmEndInterview" v-if="!isFinished">
        <text>结束面试</text>
      </view>
    </view>

    <!-- 表情分析区 -->
    <view class="emotion-section">
      <view class="emotion-card">
        <text class="emotion-emoji">{{ currentEmotion.emoji || '🙂' }}</text>
        <view class="emotion-info">
          <text class="emotion-level">{{ currentEmotion.level || '等待分析' }}</text>
          <text class="emotion-desc">面部表情</text>
        </view>
      </view>
      <view class="camera-preview">
        <!-- 拍照时短暂隐藏摄像头，用emoji占位避免闪屏感知 -->
        <view v-if="isCapturingEmotion" class="camera-placeholder">
          <text style="font-size: 60rpx;">📷</text>
        </view>
        <camera
          v-if="showCamera && !isCapturingEmotion"
          device-position="front"
          resolution="low"
          frame-size="low"
          :style="{ width: '120rpx', height: '120rpx' }"
          @initdone="onCameraInit"
        ></camera>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view class="message-list" scroll-y :scroll-top="scrollTop">
      <!-- 开场白 -->
      <view class="message-item interviewer" v-if="openingShown && opening">
        <view class="message-avatar">🤖</view>
        <view class="message-content">
          <text class="message-text">{{ opening }}</text>
          <view class="play-btn" @click="playAudio(openingAudioUrl)" v-if="openingAudioUrl">
            <text>🔊 播放</text>
          </view>
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
            <view class="audio-play-btn" @click="playAudio(item.audioUrl)" v-if="item.audioUrl">
              <text>🔊 播放语音</text>
            </view>
          </view>
        </view>

        <!-- 用户回答（语音） -->
        <view class="message-item user" v-if="item.userText">
          <view class="message-avatar user-avatar">👤</view>
          <view class="message-content user-content">
            <text class="message-text">{{ item.userText }}</text>
            <text class="audio-indicator">🎤 语音输入</text>
          </view>
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

    <!-- 录音区域 -->
    <view class="voice-section" v-if="!isFinished">
      <!-- 输入模式切换提示 -->
      <view class="mode-switch">
        <text :class="{ active: inputMode === 'voice' }" @click="inputMode = 'voice'">🎤 语音输入</text>
        <text class="divider">|</text>
        <text :class="{ active: inputMode === 'text' }" @click="inputMode = 'text'">⌨️ 文字输入</text>
      </view>

      <!-- 语音输入模式 -->
      <view v-if="inputMode === 'voice'">
        <view class="voice-hint">
          <text>{{ isRecording ? '🔴 录音中 ' + formatDuration(recordingDuration) : '🎤 点击按钮开始录音' }}</text>
        </view>
        <view class="voice-controls">
          <view
            class="record-btn"
            :class="{ recording: isRecording }"
            @click="toggleRecording"
          >
            <text class="record-icon">{{ isRecording ? '⏹' : '🎤' }}</text>
            <text class="record-text">{{ isRecording ? '结束录音' : '开始录音' }}</text>
          </view>
        </view>
      </view>

      <!-- 文字输入模式 -->
      <view v-if="inputMode === 'text'" class="text-input-section">
        <textarea
          class="text-input"
          v-model="answerText"
          placeholder="请输入你的回答..."
          :maxlength="3000"
        ></textarea>
        <button class="submit-btn" @click="submitTextAnswer">提交回答</button>
      </view>
    </view>

    <!-- 面试结束 -->
    <view class="result-section" v-if="isFinished && showResult">
      <view class="result-card">
        <text class="result-title">面试结束</text>
        <text class="result-score">总分：{{ finalScore.toFixed(1) }}（满分10分）</text>
        <view class="dimension-list">
          <view class="dimension-item" v-for="(score, key) in dimensionScores" :key="key">
            <text class="dim-name">{{ getDimensionName(key) }}</text>
            <text class="dim-score">{{ score.toFixed(1) }}/10</text>
          </view>
        </view>
        <button class="back-btn" @click="goBack">返回首页</button>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '@/common/api.js'

// 使用 api.js 中的 BASE_URL
const BASE_URL = 'https://ghphowliwsey.sealoshzh.site'

export default {
  data() {
    return {
      interviewId: '',
      positionName: '',
      opening: '',
      openingAudioUrl: '',
      currentQuestion: 1,
      answerText: '',
      isSubmitting: false,
      isFinished: false,
      showResult: false,
      openingShown: false,
      scrollTop: 0,
      messages: [],
      finalScore: 0,
      dimensionScores: {},
      currentEmotion: {
        emoji: '🙂',
        level: '等待分析',
        nervousness: 0
      },
      nervousnessHistory: [],
      pendingOpeningAudio: '',
      pendingQuestionAudio: '',
      isRecording: false,
      recordingDuration: 0,
      recordingTimer: null,
      inputMode: 'voice',  // 'voice' | 'text'
      recorderManager: null,
      cameraContext: null,
      emotionTimer: null,
      audioContext: null,
      currentPlayingUrl: '',
      answerText: '',
      showCamera: true,  // 显示摄像头用于表情分析
      isCapturingEmotion: false,  // 正在捕获表情中，用于隐藏摄像头避免闪屏
      interviewStarted: false,  // 面试是否已开始（用户点击开始按钮后）
      cameraInitialized: false  // 防止摄像头重复初始化
    }
  },

  onLoad(options) {
    this.interviewId = options.id || ''
    this.opening = decodeURIComponent(options.opening || '')

    const firstQuestion = decodeURIComponent(options.firstQuestion || '')
    const firstQuestionId = options.questionId || ''
    const firstIsPersonalized = options.isPersonalized === 'true'
    const openingAudioUrl = decodeURIComponent(options.openingAudioUrl || '')
    const questionAudioUrl = decodeURIComponent(options.questionAudioUrl || '')

    if (firstQuestion) {
      this.messages.push({
        question: firstQuestion,
        questionId: firstQuestionId,
        userText: null,
        comment: null,
        correctAnswer: null,
        score: null,
        isPersonalized: firstIsPersonalized,
        audioUrl: questionAudioUrl
      })
    }

    const position = uni.getStorageSync('currentPosition') || ''
    const positionNames = {
      backend: '后端工程师',
      algorithm: '大模型应用开发',
      network: '网络工程师'
    }
    this.positionName = positionNames[position] || position

    // 保存音频URL，等用户点击开始后再播放
    this.pendingOpeningAudio = openingAudioUrl ? BASE_URL + openingAudioUrl : ''
    this.pendingQuestionAudio = questionAudioUrl ? BASE_URL + questionAudioUrl : ''

    this.initRecorder()
    this.initAudio()
  },

  onUnload() {
    if (this.emotionTimer) {
      clearInterval(this.emotionTimer)
    }
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer)
    }
    if (this.cameraContext) {
      this.cameraContext.close()
    }
    if (this.audioContext) {
      this.audioContext.destroy()
    }
  },

  methods: {
    // 开始面试（用户点击按钮后调用，满足移动端自动播放策略）
    startInterview() {
      this.interviewStarted = true

      // 显示开场白
      this.$nextTick(() => {
        this.openingShown = true
        this.scrollToBottom()

        // 播放开场白音频
        if (this.pendingOpeningAudio) {
          this.playAudio(this.pendingOpeningAudio)
        }
      })
    },

    initRecorder() {
      try {
        this.recorderManager = uni.getRecorderManager()

        this.recorderManager.onStop((res) => {
          this.isRecording = false
          this.uploadAudio(res.tempFilePath)
        })

        this.recorderManager.onError((err) => {
          console.error('录音错误:', err)
          this.isRecording = false
          uni.showToast({ title: '录音失败', icon: 'none' })
        })
      } catch (e) {
        console.warn('录音功能初始化失败:', e)
        this.recorderManager = null
      }
    },

    initAudio() {
      try {
        this.audioContext = uni.createInnerAudioContext()
        this.audioContext.onEnded(() => {
          this.currentPlayingUrl = ''
          // 播完后如果有待播放的题目音频，继续播放
          if (this.pendingQuestionAudio) {
            const url = this.pendingQuestionAudio
            this.pendingQuestionAudio = ''
            setTimeout(() => {
              this.playAudio(url)
            }, 1000)
          }
        })
      } catch (e) {
        console.warn('音频播放功能初始化失败:', e)
        this.audioContext = null
      }
    },

    onCameraInit() {
      // 防止重复初始化
      if (this.cameraInitialized) {
        console.log('摄像头已初始化，跳过')
        return
      }
      this.cameraInitialized = true
      console.log('摄像头初始化完成，10秒/次')

      try {
        this.cameraContext = uni.createCameraContext()
        this.cameraContext.start()

        // 使用 setInterval 定时捕获，每10秒一次
        this.emotionTimer = setInterval(() => {
          console.log('定时捕获表情:', new Date().toLocaleTimeString())
          this.captureAndAnalyzeEmotion()
        }, 10000)

        // 首次捕获：延迟3秒后执行（让页面先稳定）
        setTimeout(() => {
          console.log('首次捕获表情:', new Date().toLocaleTimeString())
          this.captureAndAnalyzeEmotion()
        }, 3000)
      } catch (e) {
        console.warn('摄像头功能初始化失败:', e)
      }
    },

    captureAndAnalyzeEmotion() {
      if (!this.cameraContext || this.isCapturingEmotion) return

      // 先隐藏摄像头，避免闪屏
      this.isCapturingEmotion = true

      // 短暂延迟后再拍照（让摄像头先隐藏）
      setTimeout(() => {
        this.cameraContext.takePhoto({
          quality: 'low',
          success: (res) => {
            this.analyzeEmotionImage(res.tempImagePath)
          },
          complete: () => {
            // 恢复显示摄像头
            setTimeout(() => {
              this.isCapturingEmotion = false
            }, 100)
          }
        })
      }, 50)
    },

    analyzeEmotionImage(tempFilePath) {
      api.analyzeEmotion(tempFilePath, this.interviewId)
        .then(result => {
          if (result.success) {
            this.currentEmotion = {
              emoji: result.emoji || '🙂',
              level: result.level || '未知',
              nervousness: result.nervousness || 0
            }
            if (result.nervousness !== undefined) {
              this.nervousnessHistory.push({
                nervousness: result.nervousness,
                timestamp: new Date().toISOString()
              })
            }
          }
        })
        .catch(e => {
          console.error('表情分析失败:', e)
        })
    },

    toggleRecording() {
      if (this.isRecording) {
        this.stopRecording()
      } else {
        this.startRecording()
      }
    },

    submitTextAnswer() {
      if (!this.answerText.trim() || this.isSubmitting) return

      this.isSubmitting = true
      const text = this.answerText.trim()
      this.answerText = ''

      this.addUserText(text)

      api.submitAnswer(this.interviewId, text)
        .then(res => {
          if (res.success) {
            this.updateLastComment(res)
          }
        })
        .catch(e => {
          uni.showToast({ title: e.message || '提交失败', icon: 'none' })
        })
        .finally(() => {
          this.isSubmitting = false
        })
    },

    startRecording() {
      if (this.isRecording || this.isUploading || this.isSubmitting) return
      if (!this.recorderManager) {
        uni.showToast({ title: '录音功能不可用', icon: 'none' })
        return
      }

      this.isRecording = true
      this.recordingDuration = 0

      // 启动计时器
      this.recordingTimer = setInterval(() => {
        this.recordingDuration++
      }, 1000)

      this.recorderManager.start({
        format: 'mp3',
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        duration: 60000
      })
    },

    stopRecording() {
      if (!this.isRecording || !this.recorderManager) return

      this.isRecording = false
      // 停止计时器
      if (this.recordingTimer) {
        clearInterval(this.recordingTimer)
        this.recordingTimer = null
      }
      this.recorderManager.stop()
    },

    async uploadAudio(filePath) {
      if (!filePath) return

      this.isUploading = true

      try {
        const res = await api.uploadVoice(this.interviewId, filePath)
        console.log('uploadVoice response:', JSON.stringify(res))

        if (res.success) {
          if (res.user_text) {
            this.addUserText(res.user_text)
          }

          if (res.comment) {
            this.updateLastComment(res)
          }

          if (res.is_finished) {
            this.isFinished = true
            await this.endInterview()
          }
        } else if (res.user_text) {
          this.addUserText(res.user_text)
        } else {
          // success=false 且没有 user_text，显示错误信息
          uni.showToast({ title: res.error || '处理失败', icon: 'none' })
        }
      } catch (e) {
        console.error('上传音频失败:', e)
        uni.showToast({ title: '处理失败，请重试', icon: 'none' })
      } finally {
        this.isUploading = false
      }
    },

    addUserText(text) {
      const lastQuestion = this.messages.findLast(m => m.question && !m.userText)
      if (lastQuestion) {
        lastQuestion.userText = text
      } else {
        this.messages.push({
          question: null,
          questionId: null,
          userText: text,
          comment: null,
          correctAnswer: null,
          score: null,
          isPersonalized: false,
          audioUrl: ''
        })
      }
      this.scrollToBottom()
    },

    updateLastComment(data) {
      const lastMsg = this.messages[this.messages.length - 1]
      if (lastMsg) {
        lastMsg.comment = data.comment
        lastMsg.score = data.score
        lastMsg.correctAnswer = data.correct_answer || ''
      }
      this.scrollToBottom()

      if (data.is_finished) {
        this.isFinished = true
        this.endInterview()
      } else {
        this.getNextQuestion()
      }
    },

    async getNextQuestion() {
      try {
        const res = await api.getNextVoiceQuestion(this.interviewId)
        console.log('getNextVoiceQuestion response:', JSON.stringify(res))

        if (res.success && res.question) {
          this.messages.push({
            question: res.question,
            questionId: res.question_id,
            userText: null,
            comment: null,
            correctAnswer: null,
            score: null,
            isPersonalized: res.is_personalized || false,
            audioUrl: res.question_audio_url || ''
          })
          this.currentQuestion = res.question_count || 1
          this.scrollToBottom()

          // 自动播放问题音频
          if (res.question_audio_url) {
            setTimeout(() => {
              this.playAudio(BASE_URL + res.question_audio_url)
            }, 500)
          }
        } else if (res.is_finished) {
          this.isFinished = true
          await this.endInterview()
        }
      } catch (e) {
        console.error('获取问题失败:', e)
        uni.showToast({ title: '获取问题失败', icon: 'none' })
      }
    },

    async endInterview() {
      const that = this

      // 如果已经显示结果，不重复调用
      if (that.showResult) {
        return
      }

      try {
        const res = await api.endInterview(that.interviewId)
        if (res.success) {
          that.finalScore = res.total_score || 0
          that.dimensionScores = res.dimension_scores || {}
          that.showResult = true
          that.isFinished = true
        }
      } catch (e) {
        console.error('结束面试失败:', e)
        // 如果出错了，也尝试显示结果
        that.showResult = true
        that.isFinished = true
      }
    },

    confirmEndInterview() {
      const that = this
      uni.showModal({
        title: '确认结束面试',
        content: '你确定要退出此次面试吗？面试结果将会保存。',
        confirmText: '确定结束',
        cancelText: '继续面试',
        success: function(res) {
          if (res.confirm) {
            that.endInterview()
          }
        }
      })
    },

    goBack() {
      // 通知首页刷新面试记录
      uni.$emit('refreshInterviewHistory')
      uni.navigateBack()
    },

    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },

    getDimensionName(key) {
      const names = {
        technical: '技术能力',
        communication: '沟通表达',
        problem_solving: '问题解决',
        experience: '项目经验',
        logical_thinking: '逻辑思维'
      }
      return names[key] || key
    },

    scrollToBottom() {
      setTimeout(() => {
        this.scrollTop = 999999
      }, 100)
    },

    playAudio(url) {
      if (!url || !this.audioContext) return

      if (this.currentPlayingUrl === url) {
        this.audioContext.stop()
        this.currentPlayingUrl = ''
        return
      }

      this.audioContext.src = url
      this.audioContext.play()
      this.currentPlayingUrl = url
    }
  }
}
</script>

<style scoped>
.interview-container {
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.progress-bar {
  background: #667eea;
  color: white;
  padding: 20rpx 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10rpx;
  flex: 1;
}

.position-name {
  font-size: 28rpx;
  font-weight: bold;
}

.progress-text {
  font-size: 24rpx;
}

.progress-track {
  height: 8rpx;
  background: rgba(255,255,255,0.3);
  border-radius: 4rpx;
  flex: 1;
  margin-right: 20rpx;
}

.end-btn {
  background: rgba(255,255,255,0.2);
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.progress-fill {
  height: 100%;
  background: white;
  border-radius: 4rpx;
  transition: width 0.3s;
}

.start-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.start-card {
  background: white;
  border-radius: 32rpx;
  padding: 60rpx 50rpx;
  width: 80%;
  max-width: 600rpx;
  text-align: center;
  box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.3);
}

.start-title {
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.start-desc {
  font-size: 32rpx;
  color: #667eea;
  display: block;
  margin-bottom: 20rpx;
}

.start-tip {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 40rpx;
}

.start-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50rpx;
  color: white;
  font-size: 36rpx;
  font-weight: 500;
  border: none;
  box-shadow: 0 10rpx 30rpx rgba(102, 126, 234, 0.4);
}

.emotion-section {
  background: white;
  padding: 20rpx 30rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.emotion-card {
  display: flex;
  align-items: center;
}

.emotion-emoji {
  font-size: 48rpx;
  margin-right: 16rpx;
}

.emotion-info {
  display: flex;
  flex-direction: column;
}

.emotion-level {
  font-size: 28rpx;
  color: #333;
  font-weight: bold;
}

.emotion-desc {
  font-size: 22rpx;
  color: #999;
}

.camera-preview {
  border-radius: 16rpx;
  overflow: hidden;
}

.camera-placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 16rpx;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-list {
  flex: 1;
  padding: 20rpx 30rpx;
  padding-bottom: 450rpx;
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
}

.message-item.interviewer {
  flex-direction: row;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #48bb78;
}

.message-content {
  max-width: 70%;
  margin: 0 20rpx;
  padding: 20rpx;
  border-radius: 16rpx;
  background: white;
}

.user-content {
  background: #48bb78;
  color: white;
}

.question-header {
  margin-bottom: 10rpx;
}

.question-source {
  font-size: 22rpx;
  color: #999;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
}

.question-source.personalized {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.message-text {
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
}

.user-content .message-text {
  color: white;
}

.audio-play-btn, .play-btn {
  margin-top: 16rpx;
  display: inline-block;
  padding: 8rpx 20rpx;
  background: #667eea;
  color: white;
  border-radius: 30rpx;
  font-size: 24rpx;
}

.message-label {
  font-size: 24rpx;
  color: #667eea;
  font-weight: bold;
  display: block;
  margin-bottom: 8rpx;
}

.correct-answer {
  margin-top: 16rpx;
  padding: 16rpx;
  background: #f0f9ff;
  border-radius: 8rpx;
}

.label {
  font-size: 22rpx;
  color: #0066cc;
}

.answer-text {
  font-size: 24rpx;
  color: #333;
  display: block;
  margin-top: 8rpx;
}

.score-badge {
  margin-top: 16rpx;
  display: inline-block;
  padding: 8rpx 20rpx;
  background: #ffd700;
  color: #333;
  border-radius: 30rpx;
  font-size: 24rpx;
  font-weight: bold;
}

.audio-indicator {
  font-size: 22rpx;
  opacity: 0.8;
}

.voice-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 30rpx;
  box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.1);
}

.voice-hint {
  text-align: center;
  margin-bottom: 20rpx;
  font-size: 26rpx;
  color: #666;
}

.voice-controls {
  display: flex;
  justify-content: center;
}

.record-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: #667eea;
  color: white;
  transition: all 0.3s;
}

.record-btn.recording {
  background: #f56565;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.record-icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
}

.record-text {
  font-size: 24rpx;
}

.mode-switch {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20rpx;
  padding: 10rpx 0;
  background: #f5f5f5;
  border-radius: 30rpx;
}

.mode-switch text {
  font-size: 26rpx;
  color: #999;
  padding: 8rpx 24rpx;
}

.mode-switch text.active {
  color: #667eea;
  font-weight: bold;
}

.mode-switch .divider {
  color: #ddd;
}

.text-input-section {
  padding: 20rpx;
  background: #fff;
  border-radius: 16rpx;
}

.text-input {
  width: 100%;
  height: 160rpx;
  padding: 20rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.submit-btn {
  margin-top: 20rpx;
  width: 100%;
  height: 80rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 40rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-section {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.result-card {
  background: white;
  border-radius: 24rpx;
  padding: 50rpx;
  width: 80%;
  max-width: 600rpx;
  text-align: center;
}

.result-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 30rpx;
}

.result-score {
  font-size: 48rpx;
  font-weight: bold;
  color: #667eea;
  display: block;
  margin-bottom: 40rpx;
}

.dimension-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20rpx;
  margin-bottom: 40rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 24rpx;
  background: #f5f5f5;
  border-radius: 12rpx;
}

.dim-name {
  font-size: 22rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.dim-score {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.back-btn {
  background: #667eea;
  color: white;
  border: none;
  border-radius: 50rpx;
  padding: 20rpx 60rpx;
  font-size: 28rpx;
}
</style>
