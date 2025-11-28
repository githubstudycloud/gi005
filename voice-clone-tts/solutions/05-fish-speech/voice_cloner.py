"""
Fish-Speech 语音克隆实现

Fish-Speech 是一个 SOTA 开源 TTS 系统，使用 LLM 技术实现语音克隆。

安装:
  git clone https://github.com/fishaudio/fish-speech.git
  cd fish-speech && pip install -e .

模型下载:
  huggingface-cli download fishaudio/fish-speech-1.5 --local-dir checkpoints/fish-speech-1.5
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Union
import numpy as np

try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 检查 Fish-Speech 是否安装
FISH_SPEECH_AVAILABLE = False
try:
    from fish_speech.inference import inference
    FISH_SPEECH_AVAILABLE = True
except ImportError:
    pass


class FishSpeechCloner:
    """
    Fish-Speech 语音克隆器

    功能:
    1. 零样本语音克隆
    2. 跨语言合成
    3. 情感控制
    """

    # 支持的语言
    SUPPORTED_LANGUAGES = ["en", "zh", "ja", "ko", "fr", "de", "ar", "es"]

    def __init__(
        self,
        model_path: str = "checkpoints/fish-speech-1.5",
        device: str = None
    ):
        """
        初始化 Fish-Speech

        Args:
            model_path: 模型路径
            device: 计算设备
        """
        if not FISH_SPEECH_AVAILABLE:
            raise ImportError(
                "Fish-Speech 未安装。安装方法:\n"
                "  git clone https://github.com/fishaudio/fish-speech.git\n"
                "  cd fish-speech && pip install -e ."
            )

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Fish-Speech] 使用设备: {self.device}")

        self.model_path = model_path
        print(f"[Fish-Speech] 加载模型: {model_path}")

        # 加载模型
        self._load_model()
        print("[Fish-Speech] 模型加载完成")

    def _load_model(self):
        """加载模型"""
        # Fish-Speech 的模型加载逻辑
        # 实际实现需要根据 fish-speech 的 API
        pass

    def clone(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "zh",
        emotion: str = None
    ) -> str:
        """
        语音克隆

        Args:
            text: 合成文本
            reference_audio: 参考音频（10-30秒）
            output_path: 输出路径
            language: 语言代码
            emotion: 情感控制（可选）

        Returns:
            输出路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"[Fish-Speech] 克隆语音")
        print(f"[Fish-Speech] 参考: {reference_audio}")
        print(f"[Fish-Speech] 文本: {text[:50]}...")

        # 调用 Fish-Speech 推理
        # 实际实现需要根据 fish-speech 的 API
        audio = self._inference(text, reference_audio, language, emotion)

        # 保存
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        torchaudio.save(output_path, audio.cpu(), 44100)

        print(f"[Fish-Speech] 合成完成: {output_path}")
        return output_path

    def _inference(
        self,
        text: str,
        reference_audio: str,
        language: str,
        emotion: str = None
    ):
        """推理"""
        # Fish-Speech 推理逻辑
        # 需要根据实际 API 实现
        raise NotImplementedError("请使用 FishSpeechAPI 或安装完整 fish-speech")


class FishSpeechAPI:
    """
    Fish-Speech API 客户端

    使用 Fish Audio 云服务或本地 API 服务器
    """

    def __init__(
        self,
        api_url: str = "https://api.fish.audio",
        api_key: str = None
    ):
        """
        初始化 API 客户端

        Args:
            api_url: API 服务地址
            api_key: API 密钥（使用云服务时需要）
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key

        try:
            import httpx
            self.client = httpx.Client(timeout=120)
        except ImportError:
            import requests
            self.client = requests.Session()

        print(f"[Fish-Speech API] 连接: {api_url}")

    def clone(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "zh"
    ) -> str:
        """
        使用 API 进行语音克隆

        Args:
            text: 合成文本
            reference_audio: 参考音频路径
            output_path: 输出路径
            language: 语言

        Returns:
            输出路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"[Fish-Speech API] 克隆语音...")

        # 读取参考音频
        with open(reference_audio, 'rb') as f:
            audio_data = f.read()

        # 构建请求
        files = {
            'audio': ('reference.wav', audio_data, 'audio/wav')
        }
        data = {
            'text': text,
            'language': language
        }
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        # 发送请求
        try:
            response = self.client.post(
                f"{self.api_url}/v1/tts",
                files=files,
                data=data,
                headers=headers
            )

            if response.status_code == 200:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"[Fish-Speech API] 合成完成: {output_path}")
                return output_path
            else:
                raise Exception(f"API 错误: {response.status_code} - {response.text}")

        except Exception as e:
            raise RuntimeError(f"API 请求失败: {e}")

    def list_voices(self) -> List[dict]:
        """获取可用的预设音色"""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        response = self.client.get(
            f"{self.api_url}/v1/voices",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        return []

    def clone_with_preset(
        self,
        text: str,
        voice_id: str,
        output_path: str
    ) -> str:
        """
        使用预设音色合成

        Args:
            text: 文本
            voice_id: 预设音色 ID
            output_path: 输出路径

        Returns:
            输出路径
        """
        print(f"[Fish-Speech API] 使用预设音色: {voice_id}")

        data = {
            'text': text,
            'voice_id': voice_id
        }
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        response = self.client.post(
            f"{self.api_url}/v1/tts",
            json=data,
            headers=headers
        )

        if response.status_code == 200:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[Fish-Speech API] 合成完成: {output_path}")
            return output_path
        else:
            raise Exception(f"API 错误: {response.status_code}")


class FishSpeechLocal:
    """
    Fish-Speech 本地推理

    使用 WebUI 或命令行进行本地推理
    """

    def __init__(self, fish_speech_path: str = None):
        """
        初始化本地推理

        Args:
            fish_speech_path: Fish-Speech 安装路径
        """
        self.fish_speech_path = fish_speech_path or os.environ.get(
            'FISH_SPEECH_PATH', 'fish-speech'
        )

        if not os.path.exists(self.fish_speech_path):
            print(f"[Fish-Speech] 警告: 路径不存在 {self.fish_speech_path}")

    def clone(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "zh"
    ) -> str:
        """
        本地克隆

        Args:
            text: 文本
            reference_audio: 参考音频
            output_path: 输出路径
            language: 语言

        Returns:
            输出路径
        """
        import subprocess

        print(f"[Fish-Speech] 本地推理...")

        # 使用命令行调用
        cmd = [
            sys.executable,
            os.path.join(self.fish_speech_path, "tools", "inference.py"),
            "--text", text,
            "--reference", reference_audio,
            "--output", output_path,
            "--language", language
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[Fish-Speech] 合成完成: {output_path}")
            return output_path
        else:
            raise RuntimeError(f"推理失败: {result.stderr}")


def demo():
    """演示示例"""
    print("="*60)
    print("Fish-Speech 语音克隆演示")
    print("="*60)

    print("\n使用方式:")
    print("1. 本地安装:")
    print("   git clone https://github.com/fishaudio/fish-speech.git")
    print("   cd fish-speech && pip install -e .")
    print("")
    print("2. 使用 API:")
    print("   注册 https://fish.audio 获取 API key")

    # 检查本地安装
    if FISH_SPEECH_AVAILABLE:
        print("\n检测到本地安装，使用本地推理...")

        reference_audio = "samples/reference.wav"
        if not os.path.exists(reference_audio):
            print(f"请提供参考音频: {reference_audio}")
            return

        try:
            cloner = FishSpeechCloner()
            cloner.clone(
                text="你好，这是 Fish-Speech 合成的语音。",
                reference_audio=reference_audio,
                output_path="samples/output_fish_speech.wav"
            )
        except Exception as e:
            print(f"本地推理失败: {e}")
    else:
        print("\n本地未安装，请使用 API 模式")
        print("示例:")
        print("  api = FishSpeechAPI(api_key='your-key')")
        print("  api.clone(text, reference_audio, output_path)")


if __name__ == "__main__":
    demo()
