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

### 正确的启动流程

```bash
# 1. 先检查服务是否已运行
curl http://localhost:3000/health

# 2. 如果需要重启，再按以下步骤
conda activate ai-interviewer
cd d:/hjz/cv/AI-Interviewer-pro/backend
uvicorn main:app --host 0.0.0.0 --port 3000
```

### 核心教训

**先读文档，先验证状态，再动手操作！**

1. **先检查再动手**：服务可能已经在运行了，先 `curl http://localhost:3000/health` 验证状态，不要盲目重启
2. **严格按照 README 步骤**：用户说"看文档"就要真的按文档步骤执行，不要自己想当然
3. **conda 环境**：必须先激活 conda 环境 `conda activate ai-interviewer`，不要跳过这一步
4. **工作目录**：必须先 `cd` 到 `backend` 目录，再启动服务
5. **模块路径**：`main:app` 是相对于 backend 目录的路径，不是 `app.main:app`
6. **端口正确**：本项目端口是 **3000**，不是 8000 或其他端口
