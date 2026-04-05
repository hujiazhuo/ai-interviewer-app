<template>
  <view class="score-container">
    <!-- 顶部卡片 -->
    <view class="top-card">
      <view class="card-header">
        <text class="title">能力评估</text>
        <text class="subtitle">基于多次面试综合分析</text>
      </view>

      <!-- 雷达图 -->
      <view class="radar-section">
        <canvas canvas-id="radarChart" id="radarChart" class="radar-canvas"></canvas>
      </view>

      <!-- 维度说明 -->
      <view class="dimension-list">
        <view class="dimension-item" v-for="(item, index) in dimensions" :key="index">
          <text class="dim-label">{{ item.label }}</text>
          <text class="dim-value">{{ item.value }}</text>
        </view>
      </view>
    </view>

    <!-- 各岗位平均分 -->
    <view class="section-card">
      <text class="section-title">各岗位表现 <text class="section-hint">满分10分</text></text>
      <view class="position-bars">
        <view class="position-item" v-for="(score, position) in positionScores" :key="position">
          <text class="position-name">{{ getPositionName(position) }}</text>
          <view class="position-bar">
            <view class="bar-fill" :style="{ width: (score / 10 * 100) + '%' }"></view>
          </view>
          <text class="position-score">{{ score.toFixed(1) }}</text>
        </view>
      </view>
    </view>

    <!-- 面试历史 -->
    <view class="section-card">
      <text class="section-title">最近面试</text>
      <view class="history-list">
        <view class="history-item" v-for="(item, index) in scoreHistory" :key="index">
          <view class="history-left">
            <text class="history-position">{{ getPositionName(item.position) }}</text>
            <text class="history-date">{{ formatDate(item.created_at) }}</text>
          </view>
          <view class="history-right">
            <text class="history-score">{{ item.total_score.toFixed(1) }}</text>
            <text class="history-label">分</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/common/api.js'

const radarData = ref({})
const positionScores = ref({})
const scoreHistory = ref([])

const dimensions = ref([
  { label: '技术能力', value: 0, key: 'technical' },
  { label: '沟通表达', value: 0, key: 'communication' },
  { label: '问题解决', value: 0, key: 'problem_solving' },
  { label: '项目经验', value: 0, key: 'experience' },
  { label: '逻辑思维', value: 0, key: 'logical_thinking' }
])

const getPositionName = (position) => {
  const names = {
    frontend: '前端开发',
    backend: '后端开发',
    algorithm: '大模型应用开发'
  }
  return names[position] || position
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const loadRadarData = async () => {
  try {
    const res = await api.getRadarData()
    if (res.success) {
      radarData.value = res.radar
      // 更新维度数据
      const data = res.radar.data
      dimensions.value.forEach((dim, index) => {
        dim.value = data[index] || 0
      })
      // 绘制雷达图
      setTimeout(() => {
        drawRadarChart()
      }, 100)
    }
  } catch (e) {
    console.error('获取雷达图数据失败', e)
  }
}

const loadPositionScores = async () => {
  try {
    const res = await api.getPositionAvg()
    if (res.success) {
      positionScores.value = res.position_scores || {}
    }
  } catch (e) {
    console.error('获取岗位分数失败', e)
  }
}

const loadScoreHistory = async () => {
  try {
    const res = await api.getScoreHistory()
    if (res.success) {
      scoreHistory.value = res.scores || []
    }
  } catch (e) {
    console.error('获取评分历史失败', e)
  }
}

const drawRadarChart = () => {
  const ctx = uni.createCanvasContext('radarChart')
  const canvasWidth = 320
  const canvasHeight = 420
  const centerX = canvasWidth / 2
  const centerY = canvasHeight / 2 + 20
  const radius = 90

  // 清空画布
  ctx.clearRect(0, 0, canvasWidth, canvasHeight)

  // 绘制背景网格
  const levels = 5
  for (let i = 1; i <= levels; i++) {
    const r = (radius / levels) * i
    ctx.beginPath()
    for (let j = 0; j < 5; j++) {
      const angle = (Math.PI * 2 / 5) * j - Math.PI / 2
      const x = centerX + r * Math.cos(angle)
      const y = centerY + r * Math.sin(angle)
      if (j === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }
    ctx.closePath()
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // 绘制轴线
  for (let i = 0; i < 5; i++) {
    const angle = (Math.PI * 2 / 5) * i - Math.PI / 2
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.lineTo(centerX + radius * Math.cos(angle), centerY + radius * Math.sin(angle))
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)'
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // 绘制数据区域
  const data = radarData.value.data || [0, 0, 0, 0, 0]
  ctx.beginPath()
  for (let i = 0; i < 5; i++) {
    const angle = (Math.PI * 2 / 5) * i - Math.PI / 2
    const value = (data[i] / 10) * radius  // 分数是0-10
    const x = centerX + value * Math.cos(angle)
    const y = centerY + value * Math.sin(angle)
    if (i === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  }
  ctx.closePath()
  ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
  ctx.fill()
  ctx.strokeStyle = '#fff'
  ctx.lineWidth = 2
  ctx.stroke()

  // 绘制数据点
  for (let i = 0; i < 5; i++) {
    const angle = (Math.PI * 2 / 5) * i - Math.PI / 2
    const value = (data[i] / 10) * radius  // 分数是0-10
    const x = centerX + value * Math.cos(angle)
    const y = centerY + value * Math.sin(angle)
    ctx.beginPath()
    ctx.arc(x, y, 5, 0, Math.PI * 2)
    ctx.fillStyle = '#fff'
    ctx.fill()
  }

  // 绘制标签 - 5个角的文字紧贴雷达图
  ctx.setFontSize(12)
  ctx.setFillStyle('#fff')
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  // 各维度标签位置（紧贴雷达图顶点）
  // i=0: 技术能力 (顶部)
  // i=1: 沟通表达 (右上)
  // i=2: 问题解决 (右下)
  // i=3: 项目经验 (左下)
  // i=4: 逻辑思维 (左上)

  const labelPositions = [
    { i: 0, offsetX: 0, offsetY: -15 },   // 技术能力 - 顶部
    { i: 1, offsetX: 30, offsetY: -8 },   // 沟通表达 - 右上
    { i: 2, offsetX: 25, offsetY: 20 },   // 问题解决 - 右下
    { i: 3, offsetX: -25, offsetY: 20 },  // 项目经验 - 左下
    { i: 4, offsetX: -30, offsetY: -8 }, // 逻辑思维 - 左上
  ]

  for (const pos of labelPositions) {
    const angle = (Math.PI * 2 / 5) * pos.i - Math.PI / 2
    const x = centerX + (radius + 10) * Math.cos(angle) + pos.offsetX
    const y = centerY + (radius + 10) * Math.sin(angle) + pos.offsetY
    ctx.fillText(dimensions.value[pos.i].label, x, y)
  }

  ctx.draw()
}

onMounted(() => {
  // 检查登录状态
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.redirectTo({ url: '/pages/login/login' })
    return
  }

  loadRadarData()
  loadPositionScores()
  loadScoreHistory()
})
</script>

<style scoped>
.score-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
}

.top-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 32rpx;
  padding: 20rpx 30rpx 30rpx;
  margin-bottom: 30rpx;
}

.card-header {
  text-align: center;
  margin-bottom: 10rpx;
}

.title {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}

.subtitle {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.8);
  display: block;
  margin-top: 4rpx;
}

.radar-section {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 420rpx;
}

.radar-canvas {
  width: 320px;
  height: 420px;
}

.dimension-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-top: 30rpx;
}

.dimension-item {
  width: 33%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20rpx;
}

.dim-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.dim-value {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.section-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 24rpx;
}

.section-hint {
  font-size: 22rpx;
  color: #999;
  font-weight: 400;
  margin-left: 12rpx;
}

.position-bars {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.position-item {
  display: flex;
  align-items: center;
}

.position-name {
  width: 100rpx;
  font-size: 26rpx;
  color: #666;
}

.position-bar {
  flex: 1;
  height: 16rpx;
  background: #eee;
  border-radius: 8rpx;
  margin: 0 20rpx;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8rpx;
}

.position-score {
  width: 80rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #667eea;
  text-align: right;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  background: #f9f9f9;
  border-radius: 16rpx;
}

.history-left {
  display: flex;
  flex-direction: column;
}

.history-position {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.history-date {
  font-size: 24rpx;
  color: #999;
  margin-top: 6rpx;
}

.history-right {
  display: flex;
  align-items: baseline;
}

.history-score {
  font-size: 40rpx;
  font-weight: 600;
  color: #667eea;
}

.history-label {
  font-size: 24rpx;
  color: #999;
  margin-left: 4rpx;
}
</style>
