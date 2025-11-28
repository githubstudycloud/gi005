"""
统一 HTTP API 服务

提供 RESTful 接口用于音色克隆操作。

启动方式:
    python server.py --engine xtts --port 8000
    python server.py --engine openvoice --port 8000
    python server.py --engine gpt-sovits --port 8000

API 端点:
    POST /extract_voice     - 提取音色
    POST /synthesize        - 合成语音
    GET  /voices            - 列出音色
    GET  /voices/{voice_id} - 获取音色信息
    DELETE /voices/{voice_id} - 删除音色
    GET  /health            - 健康检查
"""

import os
import sys
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

# FastAPI
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from common.base import VoiceClonerBase, VoiceEmbedding
from common.utils import ensure_dir


# ===================== 配置 =====================

class Config:
    """服务配置"""
    ENGINE: str = os.getenv("VOICE_ENGINE", "xtts")
    HOST: str = os.getenv("VOICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("VOICE_PORT", "8000"))
    VOICES_DIR: str = os.getenv("VOICES_DIR", "./voices")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "")
    DEVICE: str = os.getenv("DEVICE", "")

    # GPT-SoVITS 特定配置
    GPT_SOVITS_HOST: str = os.getenv("GPT_SOVITS_HOST", "127.0.0.1")
    GPT_SOVITS_PORT: int = int(os.getenv("GPT_SOVITS_PORT", "9880"))


config = Config()

# 全局克隆器实例
cloner: Optional[VoiceClonerBase] = None


# ===================== 数据模型 =====================

class ExtractVoiceRequest(BaseModel):
    """提取音色请求"""
    voice_id: Optional[str] = None
    voice_name: Optional[str] = ""
    reference_text: Optional[str] = ""  # GPT-SoVITS 需要


class SynthesizeRequest(BaseModel):
    """合成语音请求"""
    text: str
    voice_id: str
    language: str = "zh"
    output_format: str = "wav"


class SynthesizeDirectRequest(BaseModel):
    """直接合成（不保存音色）"""
    text: str
    language: str = "zh"
    reference_text: str = ""  # GPT-SoVITS 需要


class VoiceInfo(BaseModel):
    """音色信息"""
    voice_id: str
    name: str
    engine: str
    created_at: float
    source_audio: str


# ===================== 初始化 =====================

def create_cloner(engine: str) -> VoiceClonerBase:
    """创建克隆器实例"""
    device = config.DEVICE or None

    if engine == "xtts":
        from xtts import XTTSCloner
        cloner = XTTSCloner(device=device)

    elif engine == "openvoice":
        from openvoice import OpenVoiceCloner
        model_path = config.MODEL_PATH or None
        cloner = OpenVoiceCloner(model_path=model_path, device=device)

    elif engine == "gpt-sovits":
        from gpt_sovits_wrapper import GPTSoVITSCloner
        cloner = GPTSoVITSCloner(
            api_host=config.GPT_SOVITS_HOST,
            api_port=config.GPT_SOVITS_PORT
        )

    else:
        raise ValueError(f"不支持的引擎: {engine}")

    cloner.load_model()
    return cloner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global cloner

    # 启动时加载模型
    print(f"[Server] 初始化引擎: {config.ENGINE}")
    cloner = create_cloner(config.ENGINE)

    # 确保目录存在
    ensure_dir(config.VOICES_DIR)
    ensure_dir(config.OUTPUT_DIR)

    yield

    # 关闭时清理
    print("[Server] 服务关闭")


# ===================== FastAPI 应用 =====================

app = FastAPI(
    title="Voice Clone API",
    description="音色克隆 HTTP 服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== API 端点 =====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "engine": config.ENGINE,
        "model_loaded": cloner.is_loaded if cloner else False
    }


@app.get("/info")
async def get_info():
    """获取服务信息"""
    return {
        "engine": config.ENGINE,
        "supported_languages": cloner.SUPPORTED_LANGUAGES if cloner else [],
        "voices_dir": config.VOICES_DIR,
        "model_loaded": cloner.is_loaded if cloner else False
    }


@app.post("/extract_voice")
async def extract_voice(
    audio: UploadFile = File(...),
    voice_id: Optional[str] = Form(None),
    voice_name: Optional[str] = Form(""),
    reference_text: Optional[str] = Form("")
):
    """
    从音频提取音色

    Args:
        audio: 参考音频文件
        voice_id: 音色ID（可选）
        voice_name: 音色名称（可选）
        reference_text: 参考文本（GPT-SoVITS 需要）

    Returns:
        音色信息
    """
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    # 保存上传的音频
    temp_audio = tempfile.NamedTemporaryFile(
        suffix=Path(audio.filename).suffix,
        delete=False
    )
    try:
        content = await audio.read()
        temp_audio.write(content)
        temp_audio.close()

        # 提取音色
        if config.ENGINE == "gpt-sovits":
            voice = cloner.extract_voice(
                audio_path=temp_audio.name,
                voice_id=voice_id,
                voice_name=voice_name,
                save_dir=config.VOICES_DIR,
                reference_text=reference_text
            )
        else:
            voice = cloner.extract_voice(
                audio_path=temp_audio.name,
                voice_id=voice_id,
                voice_name=voice_name,
                save_dir=config.VOICES_DIR
            )

        return {
            "success": True,
            "voice_id": voice.voice_id,
            "name": voice.name,
            "engine": voice.engine
        }

    finally:
        os.unlink(temp_audio.name)


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    使用已保存的音色合成语音

    Args:
        text: 文本内容
        voice_id: 音色ID
        language: 语言代码
        output_format: 输出格式

    Returns:
        音频文件
    """
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    # 检查音色是否存在
    voice_dir = Path(config.VOICES_DIR) / request.voice_id
    if not voice_dir.exists():
        raise HTTPException(404, f"音色不存在: {request.voice_id}")

    # 生成输出路径
    output_filename = f"{uuid.uuid4().hex}.{request.output_format}"
    output_path = Path(config.OUTPUT_DIR) / output_filename

    try:
        # 合成
        cloner.synthesize(
            text=request.text,
            voice=str(voice_dir),
            output_path=str(output_path),
            language=request.language
        )

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_filename
        )

    except Exception as e:
        raise HTTPException(500, f"合成失败: {str(e)}")


@app.post("/synthesize_direct")
async def synthesize_direct(
    audio: UploadFile = File(...),
    text: str = Form(...),
    language: str = Form("zh"),
    reference_text: str = Form("")
):
    """
    直接使用参考音频合成（不保存音色）

    Args:
        audio: 参考音频
        text: 文本内容
        language: 语言
        reference_text: 参考文本

    Returns:
        音频文件
    """
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    # 保存上传的音频
    temp_audio = tempfile.NamedTemporaryFile(
        suffix=Path(audio.filename).suffix,
        delete=False
    )

    output_path = Path(config.OUTPUT_DIR) / f"{uuid.uuid4().hex}.wav"

    try:
        content = await audio.read()
        temp_audio.write(content)
        temp_audio.close()

        # 根据引擎选择合成方式
        if config.ENGINE == "xtts" and hasattr(cloner, 'synthesize_simple'):
            cloner.synthesize_simple(
                text=text,
                reference_audio=temp_audio.name,
                output_path=str(output_path),
                language=language
            )
        elif config.ENGINE == "gpt-sovits" and hasattr(cloner, 'synthesize_with_audio'):
            cloner.synthesize_with_audio(
                text=text,
                reference_audio=temp_audio.name,
                reference_text=reference_text,
                output_path=str(output_path),
                language=language
            )
        else:
            # 通用方式：先提取再合成
            voice = cloner.extract_voice(
                temp_audio.name,
                save_dir=tempfile.mkdtemp()
            )
            cloner.synthesize(text, voice, str(output_path), language)

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_path.name
        )

    finally:
        os.unlink(temp_audio.name)


@app.get("/voices")
async def list_voices():
    """列出所有已保存的音色"""
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    voices = cloner.list_voices(config.VOICES_DIR)

    return {
        "voices": [
            {
                "voice_id": v.voice_id,
                "name": v.name,
                "engine": v.engine,
                "created_at": v.created_at
            }
            for v in voices
        ]
    }


@app.get("/voices/{voice_id}")
async def get_voice(voice_id: str):
    """获取音色详情"""
    voice_dir = Path(config.VOICES_DIR) / voice_id

    if not voice_dir.exists():
        raise HTTPException(404, f"音色不存在: {voice_id}")

    try:
        voice = VoiceEmbedding.load_meta(voice_dir / "voice.json")
        return voice.to_dict()
    except Exception as e:
        raise HTTPException(500, f"读取音色失败: {str(e)}")


@app.delete("/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """删除音色"""
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    if cloner.delete_voice(voice_id, config.VOICES_DIR):
        return {"success": True, "message": f"音色 {voice_id} 已删除"}
    else:
        raise HTTPException(404, f"音色不存在: {voice_id}")


# ===================== 入口 =====================

def main():
    """主入口"""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Voice Clone API Server")
    parser.add_argument("--engine", type=str, default="xtts",
                        choices=["xtts", "openvoice", "gpt-sovits"],
                        help="TTS 引擎")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="服务地址")
    parser.add_argument("--port", type=int, default=8000,
                        help="服务端口")
    parser.add_argument("--voices-dir", type=str, default="./voices",
                        help="音色存储目录")
    parser.add_argument("--model-path", type=str, default="",
                        help="模型路径（OpenVoice 需要）")
    parser.add_argument("--device", type=str, default="",
                        help="计算设备 (cuda/cpu)")

    args = parser.parse_args()

    # 更新配置
    config.ENGINE = args.engine
    config.HOST = args.host
    config.PORT = args.port
    config.VOICES_DIR = args.voices_dir
    config.MODEL_PATH = args.model_path
    config.DEVICE = args.device

    print(f"启动 Voice Clone API 服务")
    print(f"  引擎: {config.ENGINE}")
    print(f"  地址: http://{config.HOST}:{config.PORT}")
    print(f"  音色目录: {config.VOICES_DIR}")

    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
