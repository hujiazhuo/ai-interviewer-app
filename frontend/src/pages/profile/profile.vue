<template>
  <view class="profile-container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-avatar">
        <text class="avatar-text">{{ userInfo.username?.charAt(0)?.toUpperCase() || 'U' }}</text>
      </view>
      <view class="user-info">
        <text class="username">{{ userInfo.username || '用户' }}</text>
        <text class="join-date">加入于 {{ formatDate(userInfo.created_at) }}</text>
      </view>
    </view>

    <!-- 项目经历区域 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">我的项目经历</text>
        <text class="section-action" @click="showAddProject">添加项目</text>
      </view>

      <view class="project-list" v-if="projects.length > 0">
        <view class="project-item" v-for="(project, index) in projects" :key="index">
          <view class="project-header">
            <text class="project-name">{{ project.name }}</text>
            <view class="project-actions">
              <text class="project-edit" @click="editProject(index)">编辑</text>
              <text class="project-delete" @click="deleteProject(index)">删除</text>
            </view>
          </view>
          <text class="project-desc">{{ project.description }}</text>
          <view class="project-tech">
            <text class="tech-tag" v-for="(tech, i) in project.techs" :key="i">{{ tech }}</text>
          </view>
        </view>
      </view>

      <view class="empty-resume" v-else>
        <text class="empty-icon">💼</text>
        <text class="empty-text">暂无项目经历</text>
        <text class="empty-hint">添加项目经历可以获得个性化面试题目</text>
      </view>
    </view>

    <!-- 设置区域 -->
    <view class="section-card">
      <text class="section-title">设置</text>

      <view class="setting-list">
        <view class="setting-item" @click="logout">
          <text class="setting-label logout">退出登录</text>
          <text class="setting-arrow">→</text>
        </view>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version-info">
      <text>AI面试官 v1.0.0</text>
    </view>

    <!-- 添加项目弹窗 -->
    <view class="modal-overlay" v-if="showModal">
      <view class="modal-content" @click.stop>
        <text class="modal-title">{{ editingIndex >= 0 ? '编辑项目' : '添加项目' }}</text>

        <view class="form-item">
          <text class="form-label">项目名称</text>
          <input class="form-input" v-model="newProject.name" placeholder="例如：电商平台后台系统" />
        </view>

        <view class="form-item">
          <text class="form-label">项目描述</text>
          <textarea class="form-textarea" v-model="newProject.description" placeholder="简要描述项目背景、职责和技术栈..." :maxlength="2000" />
        </view>

        <view class="form-item">
          <text class="form-label">技术栈（用逗号分隔）</text>
          <input class="form-input" v-model="newProject.techsStr" placeholder="例如：Python, FastAPI, Redis, MongoDB" />
        </view>

        <view class="modal-actions">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-confirm" @click="saveProject">保存</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/common/api.js'

const projects = ref([])
const showModal = ref(false)
const editingIndex = ref(-1)
const newProject = ref({
  name: '',
  description: '',
  techsStr: ''
})

const userInfo = computed(() => {
  return uni.getStorageSync('user') || {}
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月`
}

const loadProjects = async () => {
  try {
    const res = await api.getProjects()
    if (res.success) {
      projects.value = res.projects || []
    }
  } catch (e) {
    console.error('获取项目失败', e)
  }
}

const showAddProject = () => {
  editingIndex.value = -1
  newProject.value = { name: '', description: '', techsStr: '' }
  showModal.value = true
}

const editProject = (index) => {
  editingIndex.value = index
  const project = projects.value[index]
  newProject.value = {
    name: project.name,
    description: project.description,
    techsStr: project.techs.join(', ')
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingIndex.value = -1
}

const saveProject = async () => {
  if (!newProject.value.name.trim()) {
    uni.showToast({ title: '请输入项目名称', icon: 'none' })
    return
  }

  const techs = newProject.value.techsStr
    .split(/[,，]/)
    .map(t => t.trim())
    .filter(t => t.length > 0)

  try {
    if (editingIndex.value >= 0) {
      const res = await api.updateProject(editingIndex.value, {
        name: newProject.value.name,
        description: newProject.value.description,
        techs: techs
      })
      if (res.success) {
        uni.showToast({ title: '更新成功', icon: 'success' })
        showModal.value = false
        loadProjects()
      }
    } else {
      const res = await api.addProject({
        name: newProject.value.name,
        description: newProject.value.description,
        techs: techs
      })
      if (res.success) {
        uni.showToast({ title: '添加成功', icon: 'success' })
        showModal.value = false
        loadProjects()
      }
    }
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}

const deleteProject = (index) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个项目吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await api.deleteProject(index)
          uni.showToast({ title: '删除成功', icon: 'success' })
          loadProjects()
        } catch (e) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const logout = () => {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('token')
        uni.removeStorageSync('user')
        uni.removeStorageSync('currentInterviewId')
        uni.removeStorageSync('currentPosition')
        uni.redirectTo({ url: '/pages/login/login' })
      }
    }
  })
}

onMounted(() => {
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.redirectTo({ url: '/pages/login/login' })
    return
  }

  loadProjects()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
}

.user-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 32rpx;
  padding: 50rpx 40rpx;
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 30rpx;
}

.avatar-text {
  font-size: 60rpx;
  font-weight: 600;
  color: #fff;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
}

.join-date {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8rpx;
}

.section-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.section-action {
  font-size: 28rpx;
  color: #667eea;
}

.resume-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.resume-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f9f9f9;
  border-radius: 16rpx;
}

.resume-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.resume-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.resume-name {
  font-size: 28rpx;
  color: #333;
}

.resume-date {
  font-size: 24rpx;
  color: #999;
  margin-top: 6rpx;
}

.resume-delete {
  font-size: 26rpx;
  color: #ff5a5a;
}

.empty-resume {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #666;
}

.empty-hint {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.project-item {
  padding: 24rpx;
  background: #f9f9f9;
  border-radius: 16rpx;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.project-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.project-actions {
  display: flex;
  gap: 24rpx;
}

.project-edit {
  font-size: 26rpx;
  color: #667eea;
}

.project-delete {
  font-size: 26rpx;
  color: #ff5a5a;
}

.project-desc {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12rpx;
}

.project-tech {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.tech-tag {
  font-size: 22rpx;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  padding: 4rpx 16rpx;
  border-radius: 16rpx;
}

.setting-list {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 30rpx;
  color: #333;
}

.setting-label.logout {
  color: #ff5a5a;
}

.setting-arrow {
  font-size: 28rpx;
  color: #ccc;
}

.version-info {
  text-align: center;
  padding: 40rpx 0;
}

.version-info text {
  font-size: 24rpx;
  color: #ccc;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 700rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 40rpx;
  text-align: center;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 12rpx;
  display: block;
}

.form-input {
  width: 100%;
  height: 80rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  height: 600rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.modal-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}

.btn-cancel {
  flex: 1;
  height: 88rpx;
  background: #f5f5f5;
  border-radius: 44rpx;
  font-size: 30rpx;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.btn-confirm {
  flex: 1;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 44rpx;
  font-size: 30rpx;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}
</style>
