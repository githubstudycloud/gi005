"""
GPT-SoVITS 语音克隆实现

通过 API 调用 GPT-SoVITS 服务进行语音合成。

使用前需要先启动 GPT-SoVITS 服务:
  cd GPT-SoVITS
  python api_v2.py -a 127.0.0.1 -p 9880

安装 GPT-SoVITS:
  git clone https://github.com/RVC-Boss/GPT-SoVITS.git
  cd GPT-SoVITS && pip install -r requirements.txt
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False


class GPTSoVITSClient:
    """
    GPT-SoVITS API 客户端

    功能:
    1. 零样本语音合成（使用参考音频）
    2. 微调模型语音合成
    3. 多语言支持（中英日）
    """

    def __init__(
        self,
        api_host: str = "127.0.0.1",
        api_port: int = 9880
    ):
        """
        初始化 API 客户端

        Args:
            api_host: API 服务器地址
            api_port: API 服务器端口
        """
        self.base_url = f"http://{api_host}:{api_port}"
        self.session = requests.Session()

        # 检查服务是否可用
        self._check_service()

    def _check_service(self):
        """检查 API 服务是否运行"""
        try:
            resp = self.session.get(f"{self.base_url}/", timeout=5)
            print(f"[GPT-SoVITS] 服务已连接: {self.base_url}")
        except requests.exceptions.ConnectionError:
            print(f"[GPT-SoVITS] 警告: 无法连接到服务 {self.base_url}")
            print("[GPT-SoVITS] 请先启动 GPT-SoVITS API 服务:")
            print("  cd GPT-SoVITS")
            print("  python api_v2.py -a 127.0.0.1 -p 9880")

    def synthesize(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = "",
        language: str = "zh",
        output_path: str = "output.wav",
        speed: float = 1.0,
        **kwargs
    ) -> str:
        """
        使用参考音频进行零样本语音合成

        Args:
            text: 要合成的文本
            reference_audio: 参考音频路径（3-10秒）
            reference_text: 参考音频对应的文本（可选）
            language: 语言 (zh/en/ja)
            output_path: 输出路径
            speed: 语速 (0.5-2.0)

        Returns:
            输出音频路径
        """
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"参考音频不存在: {reference_audio}")

        print(f"[GPT-SoVITS] 合成文本: {text[:50]}...")

        # 读取参考音频
        with open(reference_audio, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode()

        # 构建请求
        payload = {
            "text": text,
            "text_lang": language,
            "ref_audio_path": reference_audio,  # 或使用 base64
            "prompt_text": reference_text,
            "prompt_lang": language,
            "speed_factor": speed,
            **kwargs
        }

        try:
            # 发送请求
            resp = self.session.post(
                f"{self.base_url}/tts",
                json=payload,
                timeout=120
            )

            if resp.status_code == 200:
                # 保存音频
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(resp.content)
                print(f"[GPT-SoVITS] 合成完成: {output_path}")
                return output_path
            else:
                raise Exception(f"API 错误: {resp.status_code} - {resp.text}")

        except requests.exceptions.ConnectionError:
            raise ConnectionError("无法连接到 GPT-SoVITS 服务")

    def synthesize_stream(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = "",
        language: str = "zh",
        output_path: str = "output.wav"
    ) -> str:
        """
        流式合成（适用于长文本）

        Args:
            text: 要合成的文本
            reference_audio: 参考音频路径
            reference_text: 参考音频文本
            language: 语言
            output_path: 输出路径

        Returns:
            输出音频路径
        """
        print(f"[GPT-SoVITS] 流式合成: {text[:50]}...")

        payload = {
            "text": text,
            "text_lang": language,
            "ref_audio_path": reference_audio,
            "prompt_text": reference_text,
            "prompt_lang": language,
            "streaming_mode": True
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/tts",
                json=payload,
                stream=True,
                timeout=300
            )

            if resp.status_code == 200:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"[GPT-SoVITS] 流式合成完成: {output_path}")
                return output_path
            else:
                raise Exception(f"API 错误: {resp.status_code}")

        except requests.exceptions.ConnectionError:
            raise ConnectionError("无法连接到 GPT-SoVITS 服务")

    def set_model(
        self,
        gpt_model_path: str = None,
        sovits_model_path: str = None
    ):
        """
        切换模型（用于加载微调后的模型）

        Args:
            gpt_model_path: GPT 模型路径
            sovits_model_path: SoVITS 模型路径
        """
        payload = {}
        if gpt_model_path:
            payload["gpt_model_path"] = gpt_model_path
        if sovits_model_path:
            payload["sovits_model_path"] = sovits_model_path

        resp = self.session.post(
            f"{self.base_url}/set_model",
            json=payload,
            timeout=60
        )

        if resp.status_code == 200:
            print(f"[GPT-SoVITS] 模型切换成功")
        else:
            raise Exception(f"模型切换失败: {resp.text}")


class GPTSoVITSLocal:
    """
    GPT-SoVITS 本地调用（需要安装完整 GPT-SoVITS）

    这个类用于直接在 Python 中调用 GPT-SoVITS，
    而不是通过 API 服务器。
    """

    def __init__(self, gpt_sovits_path: str = None):
        """
        初始化本地调用

        Args:
            gpt_sovits_path: GPT-SoVITS 安装路径
        """
        self.gpt_sovits_path = gpt_sovits_path
        self._setup_path()
        self._load_models()

    def _setup_path(self):
        """设置 Python 路径"""
        if self.gpt_sovits_path and os.path.exists(self.gpt_sovits_path):
            sys.path.insert(0, self.gpt_sovits_path)
            print(f"[GPT-SoVITS] 添加路径: {self.gpt_sovits_path}")

    def _load_models(self):
        """加载模型"""
        try:
            # 尝试导入 GPT-SoVITS 模块
            from GPT_SoVITS.inference.inference_webui import (
                get_tts_wav,
                change_gpt_weights,
                change_sovits_weights
            )
            self.get_tts_wav = get_tts_wav
            self.change_gpt_weights = change_gpt_weights
            self.change_sovits_weights = change_sovits_weights
            self.available = True
            print("[GPT-SoVITS] 本地模块加载成功")
        except ImportError as e:
            print(f"[GPT-SoVITS] 本地模块不可用: {e}")
            print("[GPT-SoVITS] 请使用 API 模式或安装完整 GPT-SoVITS")
            self.available = False

    def synthesize(
        self,
        text: str,
        reference_audio: str,
        reference_text: str,
        language: str = "zh",
        output_path: str = "output.wav"
    ) -> str:
        """
        本地合成语音

        Args:
            text: 合成文本
            reference_audio: 参考音频
            reference_text: 参考文本
            language: 语言
            output_path: 输出路径

        Returns:
            输出路径
        """
        if not self.available:
            raise RuntimeError("本地模块不可用")

        print(f"[GPT-SoVITS] 本地合成: {text[:50]}...")

        # 调用 GPT-SoVITS 合成
        audio_generator = self.get_tts_wav(
            ref_wav_path=reference_audio,
            prompt_text=reference_text,
            prompt_language=language,
            text=text,
            text_language=language
        )

        # 收集音频数据
        audio_chunks = []
        for sr, chunk in audio_generator:
            audio_chunks.append(chunk)

        # 合并并保存
        if audio_chunks:
            audio = np.concatenate(audio_chunks)
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            sf.write(output_path, audio, sr)
            print(f"[GPT-SoVITS] 本地合成完成: {output_path}")
            return output_path
        else:
            raise RuntimeError("合成失败：无音频输出")


def demo():
    """演示示例"""
    print("="*60)
    print("GPT-SoVITS 语音克隆演示")
    print("="*60)

    print("\n使用方式:")
    print("1. 启动 GPT-SoVITS API 服务:")
    print("   cd GPT-SoVITS")
    print("   python api_v2.py -a 127.0.0.1 -p 9880")
    print("")
    print("2. 运行此脚本进行测试")

    # 尝试连接 API
    try:
        client = GPTSoVITSClient()

        reference_audio = "samples/reference.wav"
        if not os.path.exists(reference_audio):
            print(f"\n请提供参考音频: {reference_audio}")
            print("要求: 3-10秒清晰人声")
            return

        text = "你好，这是使用 GPT-SoVITS 合成的语音。"
        output_path = "samples/output_gpt_sovits.wav"

        client.synthesize(
            text=text,
            reference_audio=reference_audio,
            reference_text="这是参考音频的文本内容。",  # 可选
            language="zh",
            output_path=output_path
        )

        print(f"\n完成！输出: {output_path}")

    except ConnectionError as e:
        print(f"\n{e}")


if __name__ == "__main__":
    demo()
