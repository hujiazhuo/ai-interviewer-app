# AI面试官平台

基于 uni-app + FastAPI + MongoDB + ChromaDB 的智能面试系统

## 项目状态

- 后端服务端口: 3000
- 前端服务端口: 8080
- MongoDB/ChromaDB 连接正常

## 项目结构

```
AI-Interviewer-pro/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── knowledge_base/     # 面试题知识库(MD)
│   ├── uploads/            # 上传文件目录
│   ├── chroma_db/          # ChromaDB向量数据库
│   ├── main.py             # 应用入口
│   ├── .env                # 配置文件(已配置)
│   └── requirements.txt    # Python依赖
│
├── frontend/               # uni-app前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── static/         # 静态资源
│   │   └── common/         # 公共模块(API封装)
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## 快速启动

### 后端启动方法

```bash
# 1. 激活conda环境
conda activate ai-interviewer

# 2. 进入backend目录（重要！必须先cd到backend目录）
cd d:/hjz/cv/AI-Interviewer-pro/backend

# 3. 启动服务
uvicorn main:app --host 0.0.0.0 --port 3000
```

**关键说明**：
- 模块路径是 `main:app` 而不是 `app.main:app`（因为入口文件是 `backend/main.py`）
- 必须先 `cd` 到 `backend` 目录
- 端口是 **3000**（不是8000）

### 前端启动

```bash
cd frontend
npm run dev:h5
```

访问 http://localhost:8080

## API接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户 |
| POST | /api/interview/start | 开始面试 |
| POST | /api/interview/{id}/question | 获取下一题 |
| POST | /api/interview/{id}/answer | 提交回答 |
| POST | /api/interview/{id}/end | 结束面试 |
| GET | /api/score/radar | 获取雷达图数据 |
| GET | /api/score/position-avg | 各岗位平均分 |
| GET | /api/score/history | 评分历史 |
| GET | /api/project/list | 项目经历列表 |
| POST | /api/project/add | 添加项目 |
| PUT | /api/project/{index} | 更新项目 |
| DELETE | /api/project/{index} | 删除项目 |
| POST | /api/knowledge/rebuild | 重建知识库 |

## 功能特性

- 用户注册/登录（JWT认证）
- 项目经历管理（手动输入）
- 模拟面试（10题交互：前5个性化+后5知识库）
- AI点评（含参考答案）
- 评分雷达图（5维度独立评分，满分10分）
- RAG多路召回知识库
- 知识库自进化

## 技术栈

- **前端**: uni-app + Vue3 + TypeScript
- **后端**: FastAPI + Python3
- **数据库**: MongoDB (Sealos)
- **向量库**: ChromaDB
- **大模型**: DeepSeek API
- **框架**: LangChain

## 雷达图维度

每个维度独立评分（0-10分），最终总分 = 五维度平均值

1. 技术能力 (technical)
2. 沟通表达 (communication)
3. 问题解决 (problem_solving)
4. 项目经验 (experience)
5. 逻辑思维 (logical_thinking)

## 后续开发

- [ ] 视频语音交互功能
- [ ] 虚拟面试官头像
- [ ] faster-whisper (STT) + edge-tts (TTS) 语音对话
- [ ] 邮箱注册验证码

## 启动问题反思

### 本次启动耗时过长的原因

1. **模块路径错误**：错误地使用 `uvicorn app.main:app`，但入口文件是 `backend/main.py`，正确路径是 `main:app`
2. **工作目录问题**：未正确 `cd` 到 `backend` 目录，导致找不到 `main` 模块
3. **端口混淆**：之前用过的端口（8000、34570、34421）都是旧的，正确端口是 **3000**

### 关键教训

- FastAPI 项目的入口模块路径取决于 `main.py` 的位置，而不是 `app/` 目录
- 必须先确认当前工作目录，或使用绝对路径
- 启动前应检查 `main.py` 确认正确的模块引用方式
