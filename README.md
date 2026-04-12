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

### 启动前检查（建议先做）

```bash
# 1) 检查后端是否已运行
curl http://localhost:3000/health

# 2) 检查前端端口是否已占用（Windows PowerShell）
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

如果后端返回 healthy，或前端端口已监听，说明服务可能已经在运行，不要重复启动。

### 后端启动方法（FastAPI）

```bash
# 1. 激活conda环境
conda activate ai-interviewer

# 2. 进入backend目录（重要！必须先cd到backend目录）
cd d:/hjz/cv/AI-Interviewer-pro/backend

# 3. 启动服务
uvicorn main:app --host 0.0.0.0 --port 3000
```

如果在 Windows 终端里出现“uvicorn 不是内部或外部命令”，可使用下面的兜底命令（等价启动）：

```bash
cd d:/hjz/cv/AI-Interviewer-pro/backend
conda run -n ai-interviewer python -m uvicorn main:app --host 0.0.0.0 --port 3000
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

### 前端连接后端配置（本地开发必看）

当前项目本地开发应使用后端 3000 端口：

- `frontend/src/common/api.js` 中 `BASE_URL` 应为 `http://localhost:3000`
- `frontend/src/manifest.json` 中 `/api` 代理 `target` 应为 `http://localhost:3000`

若这里仍是线上域名或 8000 端口，前端会表现为“页面能打开但登录失败/后端无效”。

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
# 1. 先检查服务是否已运行（不要盲目重启）
curl http://localhost:3000/health

# 2. 如果后端没启动，再按以下步骤启动
conda activate ai-interviewer
cd d:/hjz/cv/AI-Interviewer-pro/backend
uvicorn main:app --host 0.0.0.0 --port 3000

# 3. 启动前端
cd d:/hjz/cv/AI-Interviewer-pro/frontend
npm run dev:h5
```

### 为什么这次启动花了很久

1. 先入为主地认为“服务没启动”，没有第一时间做健康检查，导致重复尝试。
2. 前端 API 地址配置与本地后端不一致（线上域名/错误端口），表现为“前端打开但登录失败”，误导为后端故障。
3. 终端环境差异导致 `conda activate` 后命令可见性不稳定，出现 `uvicorn` 命令不可用，需要用 `conda run -n ...` 兜底。
4. 端口认知不一致：项目后端固定为 3000，而不是常见的 8000。

### 核心教训

**先读文档，先验证状态，再动手操作！**

1. **先检查再动手**：先看后端健康接口、前端端口监听状态，再决定是否重启。
2. **严格按文档执行**：环境名、目录、模块路径、端口必须一致。
3. **前后端配置要对齐**：前端 `BASE_URL` 与代理 `target` 必须指向本地后端 `http://localhost:3000`。
4. **准备兜底启动命令**：当 `uvicorn` 不可见时，使用 `conda run -n ai-interviewer python -m uvicorn ...`。
5. **统一端口认知**：后端 3000，前端 8080；先确认占用再操作。
