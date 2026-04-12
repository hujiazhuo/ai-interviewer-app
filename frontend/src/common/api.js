/**
 * API 封装
 */
const BASE_URL = 'http://localhost:3000'

// 获取token
const getToken = () => uni.getStorageSync('token')

// 请求封装
const request = async (options) => {
  const {
    url,
    method = 'GET',
    data,
    header = {}
  } = options

  // 添加Authorization header
  const token = getToken()
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  // 显示加载提示
  if (options.showLoading !== false) {
    uni.showLoading({ title: '加载中...', mask: true })
  }

  try {
    const response = await new Promise((resolve, reject) => {
      uni.request({
        url: BASE_URL + url,
        method,
        data,
        header: {
          'Content-Type': 'application/json',
          ...header
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            // token过期，跳转登录
            uni.removeStorageSync('token')
            uni.removeStorageSync('user')
            uni.showToast({ title: '请先登录', icon: 'none' })
            setTimeout(() => {
              uni.navigateTo({ url: '/pages/login/login' })
            }, 1500)
            reject(new Error('未授权'))
          } else {
            reject(new Error(res.data.detail || '请求失败'))
          }
        },
        fail: (err) => {
          reject(new Error(err.errMsg || '网络错误'))
        }
      })
    })

    return response
  } finally {
    if (options.showLoading !== false) {
      uni.hideLoading()
    }
  }
}

export const api = {
  // ========== 认证相关 ==========
  login: (data) => request({
    url: '/api/auth/login',
    method: 'POST',
    data
  }),

  register: (data) => request({
    url: '/api/auth/register',
    method: 'POST',
    data
  }),

  getCurrentUser: () => request({
    url: '/api/auth/me',
    method: 'GET'
  }),

  // ========== 简历相关 ==========
  uploadResume: (filePath) => {
    return new Promise((resolve, reject) => {
      const token = getToken()
      uni.uploadFile({
        url: BASE_URL + '/api/resume/upload',
        filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(res.data))
          } else {
            reject(new Error('上传失败'))
          }
        },
        fail: reject
      })
    })
  },

  getResumes: () => request({
    url: '/api/resume/list',
    method: 'GET'
  }),

  deleteResume: (resumeId) => request({
    url: `/api/resume/${resumeId}`,
    method: 'DELETE'
  }),

  // ========== 项目经历相关 ==========
  getProjects: () => request({
    url: '/api/project/list',
    method: 'GET'
  }),

  addProject: (project) => request({
    url: '/api/project/add',
    method: 'POST',
    data: project
  }),

  deleteProject: (index) => request({
    url: `/api/project/${index}`,
    method: 'DELETE'
  }),

  updateProject: (index, project) => request({
    url: `/api/project/${index}`,
    method: 'PUT',
    data: project
  }),

  // ========== 面试相关 ==========
  startInterview: (position) => request({
    url: '/api/interview/start',
    method: 'POST',
    data: { position }
  }),

  getNextQuestion: (interviewId) => request({
    url: `/api/interview/${interviewId}/question`,
    method: 'POST'
  }),

  submitAnswer: (interviewId, answer) => request({
    url: `/api/interview/${interviewId}/answer`,
    method: 'POST',
    data: { answer }
  }),

  getInterviewStatus: (interviewId) => request({
    url: `/api/interview/${interviewId}`,
    method: 'GET'
  }),

  endInterview: (interviewId) => request({
    url: `/api/interview/${interviewId}/end`,
    method: 'POST'
  }),

  deleteInterview: (interviewId) => request({
    url: `/api/interview/${interviewId}`,
    method: 'DELETE'
  }),

  // ========== 评分相关 ==========
  getScoreHistory: (position) => request({
    url: '/api/score/history',
    method: 'GET',
    data: position ? { position } : {}
  }),

  getRadarData: () => request({
    url: '/api/score/radar',
    method: 'GET'
  }),

  getScoreTrend: (position) => request({
    url: '/api/score/trend',
    method: 'GET',
    data: { position }
  }),

  getPositionAvg: () => request({
    url: '/api/score/position-avg',
    method: 'GET'
  }),

  // ========== 语音面试相关 ==========
  startVoiceInterview: (position) => request({
    url: '/api/interview/voice/start',
    method: 'POST',
    data: { position }
  }),

  getNextVoiceQuestion: (interviewId) => request({
    url: `/api/interview/voice/${interviewId}/next-question`,
    method: 'POST'
  }),

  uploadVoice: (interviewId, filePath) => {
    return new Promise((resolve, reject) => {
      const token = getToken()
      uni.uploadFile({
        url: BASE_URL + `/api/interview/voice/upload/${interviewId}`,
        filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(res.data))
          } else {
            reject(new Error('上传失败'))
          }
        },
        fail: reject
      })
    })
  },

  analyzeEmotion: (filePath, interviewId) => {
    return new Promise((resolve, reject) => {
      const token = getToken()
      const url = interviewId
        ? BASE_URL + '/api/interview/voice/analyze_emotion?interview_id=' + interviewId
        : BASE_URL + '/api/interview/voice/analyze_emotion'
      uni.uploadFile({
        url,
        filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(res.data))
          } else {
            reject(new Error('表情分析失败'))
          }
        },
        fail: reject
      })
    })
  },

  getVoiceAudio: (audioId) => {
    return BASE_URL + `/api/interview/voice/audio/${audioId}`
  }
}

export default api
