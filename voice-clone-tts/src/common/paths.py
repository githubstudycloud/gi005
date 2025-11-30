"""
路径配置模块

集中管理项目中所有模型、工具、资源的路径配置。
所有路径都相对于项目根目录 (github004/)。
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    # voice-clone-tts/src/common/paths.py -> github004/
    return Path(__file__).parent.parent.parent.parent


# 项目根目录
PROJECT_ROOT = get_project_root()


# ===================== 模型路径 =====================

# XTTS-v2 模型
XTTS_MODEL_PATH = PROJECT_ROOT / "packages" / "models" / "xtts_v2" / "extracted"

# OpenVoice 模型
OPENVOICE_MODEL_PATH = PROJECT_ROOT / "packages" / "models" / "openvoice" / "extracted"

# Whisper 模型
WHISPER_MODEL_PATH = PROJECT_ROOT / "packages" / "models" / "whisper" / "extracted"

# GPT-SoVITS 仓库 (从 packages/repos 克隆)
GPT_SOVITS_REPO_PATH = PROJECT_ROOT / "packages" / "repos" / "GPT-SoVITS"


# ===================== 工具路径 =====================

# FFmpeg
FFMPEG_PATH = PROJECT_ROOT / "packages" / "tools" / "extracted" / "ffmpeg.exe"
FFPROBE_PATH = PROJECT_ROOT / "packages" / "tools" / "extracted" / "ffprobe.exe"


# ===================== 数据路径 =====================

# 音色存储目录
VOICES_DIR = PROJECT_ROOT / "voice-clone-tts" / "voices"

# 测试音频目录
TEST_AUDIO_DIR = PROJECT_ROOT / "test_audio"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"


# ===================== 辅助函数 =====================

def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_path(engine: str) -> Path:
    """获取指定引擎的模型路径"""
    paths = {
        "xtts": XTTS_MODEL_PATH,
        "openvoice": OPENVOICE_MODEL_PATH,
        "whisper": WHISPER_MODEL_PATH,
        "gpt-sovits": GPT_SOVITS_REPO_PATH,
    }
    return paths.get(engine.lower(), PROJECT_ROOT)


def verify_model_paths() -> dict:
    """验证所有模型路径是否存在"""
    results = {}

    # 检查 XTTS 模型
    xtts_config = XTTS_MODEL_PATH / "config.json"
    results["xtts"] = {
        "path": str(XTTS_MODEL_PATH),
        "exists": XTTS_MODEL_PATH.exists(),
        "config_exists": xtts_config.exists() if XTTS_MODEL_PATH.exists() else False,
    }

    # 检查 OpenVoice 模型
    openvoice_converter = OPENVOICE_MODEL_PATH / "converter"
    results["openvoice"] = {
        "path": str(OPENVOICE_MODEL_PATH),
        "exists": OPENVOICE_MODEL_PATH.exists(),
        "converter_exists": openvoice_converter.exists() if OPENVOICE_MODEL_PATH.exists() else False,
    }

    # 检查 Whisper 模型
    results["whisper"] = {
        "path": str(WHISPER_MODEL_PATH),
        "exists": WHISPER_MODEL_PATH.exists(),
    }

    # 检查 GPT-SoVITS 仓库
    gpt_sovits_api = GPT_SOVITS_REPO_PATH / "api_v2.py"
    results["gpt-sovits"] = {
        "path": str(GPT_SOVITS_REPO_PATH),
        "exists": GPT_SOVITS_REPO_PATH.exists(),
        "api_exists": gpt_sovits_api.exists() if GPT_SOVITS_REPO_PATH.exists() else False,
    }

    # 检查 FFmpeg
    results["ffmpeg"] = {
        "path": str(FFMPEG_PATH),
        "exists": FFMPEG_PATH.exists(),
    }

    return results


def print_path_status():
    """打印路径状态"""
    results = verify_model_paths()

    print("=" * 50)
    print("路径配置状态")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")
    print()

    for name, info in results.items():
        status = "[OK]" if info["exists"] else "[MISSING]"
        print(f"{status} {name}: {info['path']}")

        # 显示额外检查
        for key, value in info.items():
            if key not in ["path", "exists"] and isinstance(value, bool):
                sub_status = "[OK]" if value else "[MISSING]"
                print(f"    {sub_status} {key}")

    print("=" * 50)


if __name__ == "__main__":
    print_path_status()
