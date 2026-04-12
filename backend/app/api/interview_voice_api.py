"""
语音面试API - WebSocket实时语音会话
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, Dict
import json
import asyncio
import os
import uuid
import time
from datetime import datetime
from bson import ObjectId

from app.models import InterviewCreate
from app.services.interview_service import InterviewService
from app.services.speech_service import speech_service
from app.services.emotion_service import emotion_service
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

# 音频文件保留时间（秒），1小时
AUDIO_FILE_MAX_AGE = 3600

# 持久化音频存储目录（Sealos DevBox 容器重启后不会丢失）
PERSISTENT_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "audio_files")
os.makedirs(PERSISTENT_AUDIO_DIR, exist_ok=True)

router = APIRouter(prefix="/api/interview/voice", tags=["语音面试"])


@router.on_event("startup")
async def startup_event():
    """启动时清理过期音频文件"""
    cleanup_old_audio_files()


def cleanup_old_audio_files():
    """清理过期的TTS音频文件"""
    try:
        now = time.time()
        cleaned = 0
        # 清理持久化目录中的过期文件
        if os.path.exists(PERSISTENT_AUDIO_DIR):
            for filename in os.listdir(PERSISTENT_AUDIO_DIR):
                if filename.endswith('.mp3'):
                    filepath = os.path.join(PERSISTENT_AUDIO_DIR, filename)
                    if os.path.isfile(filepath):
                        file_age = now - os.path.getmtime(filepath)
                        if file_age > AUDIO_FILE_MAX_AGE:
                            os.remove(filepath)
                            cleaned += 1
        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个过期音频文件")
    except Exception as e:
        logger.error(f"清理音频文件失败: {e}")


class VoiceInterviewSession:
    """语音面试会话管理器"""

    def __init__(self, websocket: WebSocket, interview_id: str, user_id: str):
        self.websocket = websocket
        self.interview_id = interview_id
        self.user_id = user_id
        self.current_question_id: Optional[str] = None
        self.is_active = True
        self.nervousness_history: list = []

    def add_nervousness(self, nervousness: float):
        """记录紧张度"""
        self.nervousness_history.append({
            "nervousness": nervousness,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_json(self, data: dict):
        """发送JSON消息"""
        await self.websocket.send_json(data)

    async def send_text(self, text: str):
        """发送文本消息"""
        await self.websocket.send_text(text)

    async def send_tts_audio_stream(self, text: str):
        """流式发送TTS音频"""
        try:
            # 生成唯一文件名
            audio_id = str(uuid.uuid4())
            audio_path = os.path.join(PERSISTENT_AUDIO_DIR, f"{audio_id}.mp3")

            # 生成TTS音频
            await speech_service.text_to_speech(text, audio_path)

            if os.path.exists(audio_path):
                # 发送音频URL
                await self.send_json({
                    "type": "tts_audio",
                    "audio_url": f"/api/interview/voice/audio/{audio_id}",
                    "text": text
                })

                # 如果是WebSocket传输二进制，直接发送
                # 这里简化处理，客户端通过URL下载
        except Exception as e:
            logger.error(f"TTS发送失败: {e}")

    async def process_voice_input(self, audio_path: str):
        """处理语音输入"""
        # 1. STT 转文字
        user_text = await speech_service.transcribe_audio(audio_path)

        if not user_text:
            await self.send_json({
                "type": "error",
                "message": "语音识别失败，请重试"
            })
            return

        await self.send_json({
            "type": "user_text",
            "text": user_text
        })

        # 2. 提交回答给面试服务
        result = InterviewService.submit_answer(
            interview_id=self.interview_id,
            user_id=self.user_id,
            question_id=self.current_question_id,
            answer=user_text,
        )

        # 3. 如果面试结束，发送简短点评+结果
        if result.get("is_finished"):
            # 发送简短点评
            brief_comment = "面试结束，感谢参与！"
            await self.send_json({
                "type": "comment",
                "comment": brief_comment,
                "score": result.get("score", 0),
                "is_finished": True,
            })
            await self.send_tts_audio_stream(brief_comment)
            await self.end_interview()
        else:
            # 3. 发送点评（下一题由前端通过HTTP API获取，避免重复）
            if result.get("comment"):
                await self.send_json({
                    "type": "comment",
                    "comment": result.get("comment"),
                    "score": result.get("score", 0),
                    "is_finished": False,
                })

    async def ask_next_question(self):
        """获取并提问下一题"""
        # 获取用户项目经历
        resume_content = InterviewService._get_user_resume_content(self.user_id)

        next_q = InterviewService.get_next_question(
            interview_id=self.interview_id,
            user_id=self.user_id,
            resume_content=resume_content,
        )

        if "error" in next_q:
            await self.send_json({"type": "error", "message": next_q["error"]})
            return

        self.current_question_id = next_q.get("question_id")

        question_text = next_q.get("question", "")

        # 发送问题
        await self.send_json({
            "type": "question",
            "question": question_text,
            "question_id": self.current_question_id,
            "opening": next_q.get("opening", ""),
            "is_first": next_q.get("is_first", False),
            "question_count": next_q.get("question_count", 1),
            "is_personalized": next_q.get("is_personalized", False),
        })

        # 同时发送语音
        await self.send_tts_audio_stream(question_text)

    async def end_interview(self):
        """结束面试"""
        self.is_active = False
        result = InterviewService.end_interview(
            interview_id=self.interview_id,
            user_id=self.user_id,
            nervousness_history=self.nervousness_history,
        )

        # 发送最终结果
        await self.send_json({
            "type": "finished",
            "total_score": result.get("total_score", 0),
            "dimension_scores": result.get("dimension_scores", {}),
            "nervousness_history": self.nervousness_history,
            "avg_nervousness": sum(h.get("nervousness", 0) for h in self.nervousness_history) / max(len(self.nervousness_history), 1),
        })


# WebSocket连接映射
sessions: Dict[str, VoiceInterviewSession] = {}


@router.websocket("/session")
async def voice_session(
    websocket: WebSocket,
    interview_id: str = Query(...),
    token: str = Query(...),
):
    """
    语音面试WebSocket会话

    客户端连接后:
    1. 验证token
    2. 建立会话
    3. 接收音频上传 -> 处理 -> 返回LLM回复

    消息类型:
    - server -> client: question, comment, tts_audio, finished, heartbeat
    - client -> server: ping (心跳)
    """
    # 验证token
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 验证面试是否存在且属于该用户
    interview = InterviewService.get_interview(interview_id)
    if not interview or interview.user_id != user_id:
        await websocket.close(code=4002, reason="Interview not found")
        return

    # 接受连接
    await websocket.accept()

    # 创建会话
    session = VoiceInterviewSession(websocket, interview_id, user_id)
    sessions[interview_id] = session

    try:
        # 检查是否已经有第一题了（start_voice_interview已创建）
        # 如果没有，才调用ask_next_question获取第一题
        interview = InterviewService.get_interview(interview_id)
        if not interview.questions:
            await session.ask_next_question()
        else:
            # 复用已创建的第一题
            session.current_question_id = interview.questions[0].question_id

        # 保持连接，直到面试结束
        while session.is_active:
            try:
                # 接收消息（心跳检测）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "end":
                    await session.end_interview()

            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        if interview_id in sessions:
            del sessions[interview_id]


@router.post("/upload/{interview_id}")
async def upload_voice(
    interview_id: str,
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    上传语音文件并处理

    客户端录音结束后调用此API，
    服务端完成STT->LLM->TTS流程后，返回结果给客户端
    """
    user_id = current_user.get("sub")

    # 兼容不同客户端上传字段名（file / audio）
    upload_file = file or audio
    if not upload_file:
        raise HTTPException(status_code=422, detail="缺少音频文件字段 file 或 audio")

    # 验证面试
    interview = InterviewService.get_interview(interview_id)
    if not interview or interview.user_id != user_id:
        raise HTTPException(status_code=404, detail="面试不存在")

    # 保存上传的音频（使用持久化目录）
    # 小程序常见格式: m4a/aac/mp3/wav，尽量保留真实后缀避免解码失败
    filename = (upload_file.filename or "").strip()
    lower_filename = filename.lower()
    content_type = (upload_file.content_type or "").lower()

    suffix = ".wav"
    for ext in [".m4a", ".aac", ".mp3", ".wav", ".webm", ".ogg"]:
        if lower_filename.endswith(ext):
            suffix = ext
            break

    if content_type and suffix == ".wav":
        if "mp4" in content_type or "m4a" in content_type:
            suffix = ".m4a"
        elif "aac" in content_type:
            suffix = ".aac"
        elif "mpeg" in content_type or "mp3" in content_type:
            suffix = ".mp3"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "webm" in content_type:
            suffix = ".webm"

    temp_path = os.path.join(PERSISTENT_AUDIO_DIR, f"voice_{uuid.uuid4()}{suffix}")

    with open(temp_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)

    try:
        # STT 转文字
        user_text = await speech_service.transcribe_audio(temp_path)
        if not user_text:
            return {"success": False, "error": "语音识别失败"}

        # 提交回答（复用文字面试的逻辑）
        current_question = interview.questions[-1] if interview.questions else None
        if not current_question:
            return {"success": False, "error": "没有问题"}

        result = InterviewService.submit_answer(
            interview_id=interview_id,
            user_id=user_id,
            question_id=current_question.question_id,
            answer=user_text,
        )

        # 如果面试结束，返回结束信息
        if result.get("is_finished"):
            return {
                "success": True,
                "user_text": user_text,
                "comment": result.get("comment", ""),
                "score": result.get("score", 0),
                "is_finished": True,
            }

        # 否则返回评论，让前端继续获取下一题
        return {
            "success": True,
            "user_text": user_text,
            "comment": result.get("comment", ""),
            "score": result.get("score", 0),
            "is_finished": False,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/analyze_emotion")
async def analyze_emotion(
    interview_id: str = Query(None),
    file: UploadFile = File(...),
):
    """
    分析表情情绪

    客户端定时截图调用此API，
    返回紧张度等情绪分析结果，并记录到面试记录
    """
    # 保存上传的图片（使用持久化目录）
    temp_path = os.path.join(PERSISTENT_AUDIO_DIR, f"frame_{uuid.uuid4()}.jpg")

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        result = emotion_service.analyze_frame(temp_path)

        # 如果提供了 interview_id，存储紧张度到 MongoDB
        if interview_id and result.get("success") is not False:
            try:
                from app.database import MongoDB
                nervousness_entry = {
                    "nervousness": result.get("nervousness", 0),
                    "emotion": result.get("emotion", "unknown"),
                    "timestamp": datetime.utcnow()
                }
                MongoDB.client["interviews"].update_one(
                    {"_id": ObjectId(interview_id)},
                    {"$push": {"nervousness_history": nervousness_entry}}
                )
            except Exception as e:
                logger.error(f"存储紧张度失败: {e}")

        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """
    获取TTS生成的音频文件
    """
    # 使用与 speech_service 相同的持久化存储目录
    audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "audio_files")
    audio_path = os.path.join(audio_dir, f"{audio_id}.mp3")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="音频不存在")

    return FileResponse(audio_path, media_type="audio/mpeg")


@router.post("/start", response_model=dict)
async def start_voice_interview(
    interview_data: InterviewCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    开始语音面试 (HTTP入口)

    与文字面试共享 InterviewService，
    只是返回时额外返回 WebSocket 连接信息
    """
    user_id = current_user["sub"]
    position = interview_data.position

    # 验证岗位
    valid_positions = ["backend", "algorithm", "network"]
    if position not in valid_positions:
        raise HTTPException(
            status_code=400,
            detail=f"无效的岗位类型，仅支持: {', '.join(valid_positions)}"
        )

    # 创建面试 (复用现有服务)
    interview = InterviewService.start_interview(user_id, position)

    # 获取第一题
    resume_content = InterviewService._get_user_resume_content(user_id)
    first_question = InterviewService.get_next_question(
        interview_id=interview.id,
        user_id=user_id,
        resume_content=resume_content,
    )

    # 生成开场白音频
    opening_audio_url = ""
    if first_question.get("opening"):
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(PERSISTENT_AUDIO_DIR, f"{audio_id}.mp3")
        await speech_service.text_to_speech(first_question["opening"], audio_path)
        opening_audio_url = f"/api/interview/voice/audio/{audio_id}"

    # 生成第一题音频
    question_audio_url = ""
    if first_question.get("question"):
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(PERSISTENT_AUDIO_DIR, f"{audio_id}.mp3")
        await speech_service.text_to_speech(first_question["question"], audio_path)
        question_audio_url = f"/api/interview/voice/audio/{audio_id}"

    # 返回WebSocket连接信息
    return {
        "success": True,
        "interview_id": interview.id,
        "position": position,
        "opening": first_question.get("opening", ""),
        "opening_audio_url": opening_audio_url,
        "question": first_question.get("question", ""),
        "question_id": first_question.get("question_id", ""),
        "question_count": 1,
        "is_personalized": first_question.get("is_personalized", False),
        "question_audio_url": question_audio_url,
        "websocket_url": "/api/interview/voice/session",
    }


@router.post("/{interview_id}/next-question", response_model=dict)
async def get_next_voice_question(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    获取语音面试的下一题（带TTS音频）

    与文字面试的 /interview/{id}/question 类似，但额外返回TTS音频URL
    """
    user_id = current_user["sub"]

    # 验证面试
    interview = InterviewService.get_interview(interview_id)
    if not interview or interview.user_id != user_id:
        raise HTTPException(status_code=404, detail="面试不存在")

    if interview.status.value == "completed":
        return {"success": True, "is_finished": True}

    # 获取用户项目经历
    resume_content = InterviewService._get_user_resume_content(user_id)

    # 获取下一题
    result = InterviewService.get_next_question(
        interview_id=interview_id,
        user_id=user_id,
        resume_content=resume_content,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # 生成TTS音频
    question_audio_url = ""
    if result.get("question"):
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(PERSISTENT_AUDIO_DIR, f"{audio_id}.mp3")
        await speech_service.text_to_speech(result["question"], audio_path)
        question_audio_url = f"/api/interview/voice/audio/{audio_id}"

    return {
        "success": True,
        "question": result.get("question"),
        "question_id": result.get("question_id"),
        "opening": result.get("opening", ""),
        "is_first": result.get("is_first", False),
        "is_finished": result.get("is_finished", False),
        "question_count": result.get("question_count", 0),
        "is_personalized": result.get("is_personalized", False),
        "question_audio_url": question_audio_url,
    }
