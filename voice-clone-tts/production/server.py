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
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import io

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from common.base import VoiceClonerBase, VoiceEmbedding
from common.utils import ensure_dir
from common.audio_processor import AudioProcessor, preprocess_audio


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


class StreamSynthesizeRequest(BaseModel):
    """流式合成请求"""
    text: str
    voice_id: str
    language: str = "zh"
    chunk_size: int = 4096  # 每个chunk的大小（字节）


class BatchSynthesizeRequest(BaseModel):
    """批量合成请求"""
    texts: list[str]
    voice_id: str
    language: str = "zh"
    output_format: str = "wav"


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

# API 标签说明
tags_metadata = [
    {
        "name": "health",
        "description": "服务健康检查和信息查询",
    },
    {
        "name": "voice",
        "description": "音色管理：提取、列出、删除音色",
    },
    {
        "name": "synthesis",
        "description": "语音合成：普通合成、流式合成、批量合成",
    },
    {
        "name": "audio",
        "description": "音频处理：预处理、降噪、增强",
    },
]

app = FastAPI(
    title="Voice Clone TTS API",
    description="""
# 音色克隆 TTS 服务 API

支持多种 TTS 引擎的统一音色克隆服务。

## 功能特性

- **音色提取**: 从参考音频中提取说话人音色
- **语音合成**: 使用提取的音色合成新语音
- **流式合成**: 支持流式返回音频数据
- **批量合成**: 一次性合成多段文本
- **音频预处理**: 降噪、去静音、增强等

## 支持的引擎

- **XTTS-v2**: Coqui 的跨语言 TTS 模型
- **OpenVoice**: MyShell 的音色克隆模型
- **GPT-SoVITS**: 高质量少样本 TTS 模型

## 快速开始

1. 上传参考音频提取音色 (`POST /extract_voice`)
2. 使用音色ID合成语音 (`POST /synthesize`)
3. 或直接使用参考音频合成 (`POST /synthesize_direct`)
    """,
    version="2.1.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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


# ===================== 流式合成 =====================

@app.post("/synthesize_stream")
async def synthesize_stream(request: StreamSynthesizeRequest):
    """
    流式合成语音 - 边合成边返回音频数据

    适用于长文本或需要实时播放的场景。
    返回的是原始 PCM 音频流 (16kHz, 16bit, mono)。

    Args:
        text: 文本内容
        voice_id: 音色ID
        language: 语言代码
        chunk_size: 每个数据块大小

    Returns:
        流式音频数据 (audio/pcm)
    """
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    # 检查音色是否存在
    voice_dir = Path(config.VOICES_DIR) / request.voice_id
    if not voice_dir.exists():
        raise HTTPException(404, f"音色不存在: {request.voice_id}")

    async def audio_generator():
        """生成音频数据块"""
        # 先完整合成，然后分块返回
        # TODO: 未来可以支持真正的流式合成（需要引擎支持）
        output_path = Path(config.OUTPUT_DIR) / f"stream_{uuid.uuid4().hex}.wav"

        try:
            # 合成完整音频
            cloner.synthesize(
                text=request.text,
                voice=str(voice_dir),
                output_path=str(output_path),
                language=request.language
            )

            # 读取并分块返回
            with open(output_path, 'rb') as f:
                # 跳过 WAV 头（44字节）
                f.seek(44)
                while True:
                    chunk = f.read(request.chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    await asyncio.sleep(0)  # 让出控制权

        finally:
            # 清理临时文件
            if output_path.exists():
                output_path.unlink()

    return StreamingResponse(
        audio_generator(),
        media_type="audio/pcm",
        headers={
            "X-Audio-Sample-Rate": "24000",
            "X-Audio-Channels": "1",
            "X-Audio-Bit-Depth": "16"
        }
    )


# ===================== 批量合成 =====================

@app.post("/synthesize_batch")
async def synthesize_batch(request: BatchSynthesizeRequest, background_tasks: BackgroundTasks):
    """
    批量合成多段文本

    为每段文本生成独立的音频文件，返回任务ID供后续查询。

    Args:
        texts: 文本列表
        voice_id: 音色ID
        language: 语言代码
        output_format: 输出格式

    Returns:
        批量合成结果列表
    """
    if not cloner:
        raise HTTPException(500, "服务未初始化")

    # 检查音色是否存在
    voice_dir = Path(config.VOICES_DIR) / request.voice_id
    if not voice_dir.exists():
        raise HTTPException(404, f"音色不存在: {request.voice_id}")

    # 限制批量大小
    if len(request.texts) > 100:
        raise HTTPException(400, "批量合成最多支持100条文本")

    batch_id = uuid.uuid4().hex
    results = []

    for i, text in enumerate(request.texts):
        if not text.strip():
            results.append({
                "index": i,
                "success": False,
                "error": "文本为空"
            })
            continue

        output_filename = f"batch_{batch_id}_{i:03d}.{request.output_format}"
        output_path = Path(config.OUTPUT_DIR) / output_filename

        try:
            cloner.synthesize(
                text=text,
                voice=str(voice_dir),
                output_path=str(output_path),
                language=request.language
            )

            results.append({
                "index": i,
                "success": True,
                "filename": output_filename,
                "download_url": f"/outputs/{output_filename}"
            })

        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })

    return {
        "batch_id": batch_id,
        "total": len(request.texts),
        "success_count": sum(1 for r in results if r.get("success")),
        "results": results
    }


@app.get("/outputs/{filename}")
async def download_output(filename: str):
    """下载输出文件"""
    file_path = Path(config.OUTPUT_DIR) / filename

    if not file_path.exists():
        raise HTTPException(404, "文件不存在")

    # 安全检查：确保文件在输出目录内
    try:
        file_path.resolve().relative_to(Path(config.OUTPUT_DIR).resolve())
    except ValueError:
        raise HTTPException(403, "禁止访问")

    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=filename
    )


# ===================== 音频预处理 =====================

@app.post("/preprocess")
async def preprocess_audio_endpoint(
    audio: UploadFile = File(...),
    denoise: bool = Form(True),
    remove_silence: bool = Form(True),
    enhance: bool = Form(True),
    normalize: bool = Form(True),
    max_duration: float = Form(30.0)
):
    """
    音频预处理

    对上传的音频进行降噪、去静音、增强等处理。
    适合在提取音色前优化参考音频质量。

    Args:
        audio: 音频文件
        denoise: 是否降噪
        remove_silence: 是否移除静音
        enhance: 是否增强
        normalize: 是否归一化
        max_duration: 最大时长（秒）

    Returns:
        处理后的音频文件
    """
    # 保存上传的音频
    temp_input = tempfile.NamedTemporaryFile(
        suffix=Path(audio.filename).suffix,
        delete=False
    )

    try:
        content = await audio.read()
        temp_input.write(content)
        temp_input.close()

        # 处理音频
        processor = AudioProcessor()
        output_filename = f"processed_{uuid.uuid4().hex}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename

        processor.process(
            audio_path=temp_input.name,
            output_path=str(output_path),
            denoise=denoise,
            remove_silence=remove_silence,
            enhance=enhance,
            normalize=normalize,
            max_duration=max_duration
        )

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_filename
        )

    except Exception as e:
        raise HTTPException(500, f"处理失败: {str(e)}")

    finally:
        os.unlink(temp_input.name)


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
