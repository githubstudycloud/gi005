"""
音色克隆 HTTP 客户端

用于调用 Voice Clone API 服务的 Python 客户端。
可作为工具类快速集成到其他服务中。

使用示例:

    from client import VoiceCloneClient

    client = VoiceCloneClient("http://localhost:8000")

    # 提取音色
    voice = client.extract_voice("reference.wav", voice_name="我的声音")
    print(f"音色ID: {voice['voice_id']}")

    # 合成语音
    audio_data = client.synthesize("你好世界", voice['voice_id'])
    with open("output.wav", "wb") as f:
        f.write(audio_data)

    # 或保存到文件
    client.synthesize_to_file("你好世界", voice['voice_id'], "output.wav")
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO


class VoiceCloneClient:
    """
    音色克隆 HTTP 客户端

    提供与 Voice Clone API 服务交互的便捷方法。
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 120
    ):
        """
        初始化客户端

        Args:
            base_url: API 服务地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            服务状态信息
        """
        resp = self.session.get(
            f"{self.base_url}/health",
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_info(self) -> Dict[str, Any]:
        """
        获取服务信息

        Returns:
            服务配置信息
        """
        resp = self.session.get(
            f"{self.base_url}/info",
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def extract_voice(
        self,
        audio_path: str,
        voice_id: str = None,
        voice_name: str = "",
        reference_text: str = ""
    ) -> Dict[str, Any]:
        """
        从音频提取音色

        Args:
            audio_path: 参考音频路径
            voice_id: 音色ID（可选）
            voice_name: 音色名称（可选）
            reference_text: 参考文本（GPT-SoVITS 需要）

        Returns:
            音色信息 {"voice_id": "...", "name": "...", "engine": "..."}
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        with open(audio_path, 'rb') as f:
            files = {'audio': (Path(audio_path).name, f)}
            data = {
                'voice_name': voice_name,
                'reference_text': reference_text
            }
            if voice_id:
                data['voice_id'] = voice_id

            resp = self.session.post(
                f"{self.base_url}/extract_voice",
                files=files,
                data=data,
                timeout=self.timeout
            )

        resp.raise_for_status()
        return resp.json()

    def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str = "zh"
    ) -> bytes:
        """
        使用音色合成语音

        Args:
            text: 文本内容
            voice_id: 音色ID
            language: 语言代码

        Returns:
            音频数据（bytes）
        """
        payload = {
            "text": text,
            "voice_id": voice_id,
            "language": language
        }

        resp = self.session.post(
            f"{self.base_url}/synthesize",
            json=payload,
            timeout=self.timeout
        )

        resp.raise_for_status()
        return resp.content

    def synthesize_to_file(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        language: str = "zh"
    ) -> str:
        """
        合成语音并保存到文件

        Args:
            text: 文本
            voice_id: 音色ID
            output_path: 输出路径
            language: 语言

        Returns:
            输出文件路径
        """
        audio_data = self.synthesize(text, voice_id, language)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(audio_data)

        return output_path

    def synthesize_direct(
        self,
        text: str,
        audio_path: str,
        language: str = "zh",
        reference_text: str = ""
    ) -> bytes:
        """
        直接使用参考音频合成（不保存音色）

        Args:
            text: 文本
            audio_path: 参考音频路径
            language: 语言
            reference_text: 参考文本

        Returns:
            音频数据
        """
        with open(audio_path, 'rb') as f:
            files = {'audio': (Path(audio_path).name, f)}
            data = {
                'text': text,
                'language': language,
                'reference_text': reference_text
            }

            resp = self.session.post(
                f"{self.base_url}/synthesize_direct",
                files=files,
                data=data,
                timeout=self.timeout
            )

        resp.raise_for_status()
        return resp.content

    def list_voices(self) -> List[Dict[str, Any]]:
        """
        列出所有音色

        Returns:
            音色列表
        """
        resp = self.session.get(
            f"{self.base_url}/voices",
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("voices", [])

    def get_voice(self, voice_id: str) -> Dict[str, Any]:
        """
        获取音色详情

        Args:
            voice_id: 音色ID

        Returns:
            音色信息
        """
        resp = self.session.get(
            f"{self.base_url}/voices/{voice_id}",
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def delete_voice(self, voice_id: str) -> bool:
        """
        删除音色

        Args:
            voice_id: 音色ID

        Returns:
            是否成功
        """
        resp = self.session.delete(
            f"{self.base_url}/voices/{voice_id}",
            timeout=30
        )
        return resp.status_code == 200


class VoiceCloneService:
    """
    音色克隆服务封装

    更高级的封装，提供便捷的工作流方法。
    可直接集成到其他服务中使用。
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        """初始化服务"""
        self.client = VoiceCloneClient(api_url)
        self._voices_cache = {}

    def clone_voice(
        self,
        text: str,
        reference_audio: str,
        output_path: str = None,
        voice_id: str = None,
        language: str = "zh"
    ) -> str:
        """
        一键克隆语音

        Args:
            text: 文本
            reference_audio: 参考音频
            output_path: 输出路径（可选）
            voice_id: 复用已有音色ID（可选）
            language: 语言

        Returns:
            输出文件路径 或 None（如果未指定输出路径）
        """
        # 如果没有指定 voice_id，先提取音色
        if not voice_id:
            result = self.client.extract_voice(reference_audio)
            voice_id = result['voice_id']
            self._voices_cache[voice_id] = result

        # 合成
        audio_data = self.client.synthesize(text, voice_id, language)

        # 保存或返回
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            return output_path
        else:
            return audio_data

    def batch_synthesize(
        self,
        texts: List[str],
        voice_id: str,
        output_dir: str,
        language: str = "zh"
    ) -> List[str]:
        """
        批量合成

        Args:
            texts: 文本列表
            voice_id: 音色ID
            output_dir: 输出目录
            language: 语言

        Returns:
            输出文件路径列表
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        outputs = []

        for i, text in enumerate(texts):
            output_path = Path(output_dir) / f"output_{i+1:03d}.wav"
            self.client.synthesize_to_file(
                text, voice_id, str(output_path), language
            )
            outputs.append(str(output_path))

        return outputs


# 示例用法
if __name__ == "__main__":
    # 简单示例
    client = VoiceCloneClient("http://localhost:8000")

    # 检查服务
    print("服务状态:", client.health_check())

    # 提取音色
    # voice = client.extract_voice("reference.wav", voice_name="测试音色")
    # print(f"提取的音色: {voice}")

    # 合成语音
    # audio = client.synthesize("你好世界", voice["voice_id"])
    # with open("output.wav", "wb") as f:
    #     f.write(audio)
