"""
方案四示例：使用 SpeechBrain 提取说话人嵌入

SpeechBrain 提供高质量的说话人编码器，可以提取音色特征用于分析和匹配。

安装步骤：
pip install speechbrain
"""

import os
import torch
import numpy as np

# 检查是否安装了 SpeechBrain
try:
    from speechbrain.inference.speaker import EncoderClassifier
except ImportError:
    print("请先安装 SpeechBrain:")
    print("  pip install speechbrain")
    exit(1)


class SpeakerEmbeddingExtractor:
    """说话人嵌入提取器"""

    def __init__(self,
                 model_source: str = "speechbrain/spkrec-ecapa-voxceleb",
                 save_dir: str = "pretrained_models/spkrec-ecapa-voxceleb"):
        """
        初始化说话人编码器

        Args:
            model_source: 预训练模型来源
            save_dir: 模型保存目录
        """
        print(f"正在加载说话人编码器: {model_source}")

        self.classifier = EncoderClassifier.from_hparams(
            source=model_source,
            savedir=save_dir
        )

        print("说话人编码器加载完成")

    def extract_embedding(self, audio_path: str) -> torch.Tensor:
        """
        从音频文件提取说话人嵌入

        Args:
            audio_path: 音频文件路径

        Returns:
            说话人嵌入张量 [1, embedding_dim]
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        print(f"正在从 {audio_path} 提取说话人嵌入...")

        embedding = self.classifier.encode_file(audio_path)

        print(f"嵌入提取完成，shape: {embedding.shape}")
        return embedding

    def extract_embedding_from_waveform(self,
                                        waveform: torch.Tensor,
                                        sample_rate: int = 16000) -> torch.Tensor:
        """
        从波形数据提取说话人嵌入

        Args:
            waveform: 音频波形 [batch, time] 或 [time]
            sample_rate: 采样率

        Returns:
            说话人嵌入张量
        """
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)

        # SpeechBrain 期望 16kHz
        if sample_rate != 16000:
            import torchaudio
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)

        embedding = self.classifier.encode_batch(waveform)
        return embedding

    def compute_similarity(self,
                           embedding1: torch.Tensor,
                           embedding2: torch.Tensor) -> float:
        """
        计算两个说话人嵌入的相似度

        Args:
            embedding1: 第一个嵌入
            embedding2: 第二个嵌入

        Returns:
            余弦相似度 [-1, 1]
        """
        similarity = torch.nn.functional.cosine_similarity(
            embedding1.squeeze(),
            embedding2.squeeze(),
            dim=0
        )
        return similarity.item()

    def save_embedding(self, embedding: torch.Tensor, save_path: str):
        """保存说话人嵌入"""
        torch.save(embedding, save_path)
        print(f"嵌入已保存到: {save_path}")

    def load_embedding(self, load_path: str) -> torch.Tensor:
        """加载说话人嵌入"""
        embedding = torch.load(load_path)
        print(f"已加载嵌入: {load_path}")
        return embedding


class VoiceMatcher:
    """音色匹配器 - 在音色库中找到最相似的音色"""

    def __init__(self, extractor: SpeakerEmbeddingExtractor):
        """
        初始化音色匹配器

        Args:
            extractor: 说话人嵌入提取器
        """
        self.extractor = extractor
        self.voice_library = {}  # {name: embedding}

    def add_voice(self, name: str, audio_path: str):
        """
        添加音色到库

        Args:
            name: 音色名称
            audio_path: 音频文件路径
        """
        embedding = self.extractor.extract_embedding(audio_path)
        self.voice_library[name] = embedding
        print(f"已添加音色: {name}")

    def add_voice_from_embedding(self, name: str, embedding: torch.Tensor):
        """从嵌入添加音色"""
        self.voice_library[name] = embedding
        print(f"已添加音色: {name}")

    def find_similar(self,
                     query_audio: str,
                     top_k: int = 3) -> list[tuple[str, float]]:
        """
        找到最相似的音色

        Args:
            query_audio: 查询音频路径
            top_k: 返回最相似的 k 个

        Returns:
            [(音色名, 相似度), ...] 按相似度降序排列
        """
        query_embedding = self.extractor.extract_embedding(query_audio)

        similarities = []
        for name, embedding in self.voice_library.items():
            sim = self.extractor.compute_similarity(query_embedding, embedding)
            similarities.append((name, sim))

        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def save_library(self, save_path: str):
        """保存音色库"""
        torch.save(self.voice_library, save_path)
        print(f"音色库已保存到: {save_path}")

    def load_library(self, load_path: str):
        """加载音色库"""
        self.voice_library = torch.load(load_path)
        print(f"已加载音色库，共 {len(self.voice_library)} 个音色")


def demo_extract_embedding():
    """提取说话人嵌入示例"""
    print("\n=== 提取说话人嵌入示例 ===\n")

    extractor = SpeakerEmbeddingExtractor()

    # 检查音频文件
    audio_path = "reference_speaker.wav"
    if not os.path.exists(audio_path):
        print(f"请提供音频文件: {audio_path}")
        return

    # 提取嵌入
    embedding = extractor.extract_embedding(audio_path)
    print(f"嵌入维度: {embedding.shape}")

    # 保存嵌入
    extractor.save_embedding(embedding, "speaker_embedding_speechbrain.pt")


def demo_voice_similarity():
    """音色相似度比较示例"""
    print("\n=== 音色相似度比较示例 ===\n")

    extractor = SpeakerEmbeddingExtractor()

    # 检查音频文件
    audio1 = "speaker1.wav"
    audio2 = "speaker2.wav"

    if not os.path.exists(audio1) or not os.path.exists(audio2):
        print("请提供两个音频文件进行比较:")
        print(f"  - {audio1}")
        print(f"  - {audio2}")
        return

    # 提取嵌入
    emb1 = extractor.extract_embedding(audio1)
    emb2 = extractor.extract_embedding(audio2)

    # 计算相似度
    similarity = extractor.compute_similarity(emb1, emb2)

    print(f"\n音色相似度: {similarity:.4f}")
    if similarity > 0.8:
        print("判断: 很可能是同一说话人")
    elif similarity > 0.5:
        print("判断: 可能是同一说话人")
    else:
        print("判断: 很可能是不同说话人")


def demo_voice_library():
    """音色库匹配示例"""
    print("\n=== 音色库匹配示例 ===\n")

    extractor = SpeakerEmbeddingExtractor()
    matcher = VoiceMatcher(extractor)

    # 检查音色库目录
    voice_lib_dir = "voice_library"
    if not os.path.exists(voice_lib_dir):
        print(f"请创建音色库目录并添加音频文件: {voice_lib_dir}/")
        print("示例结构:")
        print("  voice_library/")
        print("    speaker_alice.wav")
        print("    speaker_bob.wav")
        print("    speaker_charlie.wav")
        return

    # 添加音色到库
    for filename in os.listdir(voice_lib_dir):
        if filename.endswith(('.wav', '.mp3', '.flac')):
            name = os.path.splitext(filename)[0]
            audio_path = os.path.join(voice_lib_dir, filename)
            matcher.add_voice(name, audio_path)

    if len(matcher.voice_library) == 0:
        print("音色库为空，请添加音频文件")
        return

    # 保存音色库
    matcher.save_library("voice_library.pt")

    # 查询最相似的音色
    query_audio = "query_speaker.wav"
    if os.path.exists(query_audio):
        print(f"\n查找与 {query_audio} 最相似的音色...")
        results = matcher.find_similar(query_audio, top_k=3)

        print("\n匹配结果:")
        for name, sim in results:
            print(f"  {name}: {sim:.4f}")
    else:
        print(f"\n请提供查询音频: {query_audio}")


def demo_combine_with_chattts():
    """结合 ChatTTS 使用的示例"""
    print("\n=== 结合 ChatTTS 使用示例 ===\n")

    print("思路说明:")
    print("1. 使用 SpeechBrain 提取参考音频的说话人嵌入")
    print("2. 在 ChatTTS 音色库中找到最相似的音色")
    print("3. 使用匹配的 ChatTTS 音色生成语音")
    print()

    # 检查依赖
    try:
        import ChatTTS
    except ImportError:
        print("此示例需要安装 ChatTTS:")
        print("  pip install chattts")
        return

    extractor = SpeakerEmbeddingExtractor()

    # 假设我们有一个 ChatTTS 音色库
    # 每个音色都预先提取了 SpeechBrain 嵌入用于匹配
    chattts_voice_library_path = "chattts_voice_library.pt"

    if not os.path.exists(chattts_voice_library_path):
        print(f"请准备 ChatTTS 音色库: {chattts_voice_library_path}")
        print("\n音色库格式 (使用 torch.save 保存的字典):")
        print("  {")
        print('    "voice_001": {')
        print('      "speechbrain_embedding": tensor(...),  # SpeechBrain 嵌入')
        print('      "chattts_speaker_emb": "...",          # ChatTTS speaker embedding')
        print("    },")
        print("    ...")
        print("  }")
        return

    # 加载音色库
    voice_lib = torch.load(chattts_voice_library_path)

    # 提取查询音频的嵌入
    query_audio = "reference_speaker.wav"
    if not os.path.exists(query_audio):
        print(f"请提供参考音频: {query_audio}")
        return

    query_emb = extractor.extract_embedding(query_audio)

    # 找到最相似的 ChatTTS 音色
    best_match = None
    best_sim = -1

    for name, data in voice_lib.items():
        lib_emb = data["speechbrain_embedding"]
        sim = extractor.compute_similarity(query_emb, lib_emb)
        if sim > best_sim:
            best_sim = sim
            best_match = name

    print(f"最匹配的 ChatTTS 音色: {best_match} (相似度: {best_sim:.4f})")

    # 使用匹配的音色生成语音
    chat = ChatTTS.Chat()
    chat.load(compile=False)

    matched_spk = voice_lib[best_match]["chattts_speaker_emb"]

    params = ChatTTS.Chat.InferCodeParams(
        spk_emb=matched_spk,
        temperature=0.3,
    )

    wavs = chat.infer(
        ["这是使用匹配音色生成的语音。"],
        params_infer_code=params
    )

    # 保存音频
    import torchaudio
    audio_tensor = torch.from_numpy(wavs[0]).unsqueeze(0)
    torchaudio.save("output_matched_voice.wav", audio_tensor, 24000)
    print("已保存到: output_matched_voice.wav")


def main():
    """主函数"""
    print("=" * 60)
    print("SpeechBrain 说话人嵌入提取示例")
    print("=" * 60)

    demo_extract_embedding()
    demo_voice_similarity()
    demo_voice_library()
    # demo_combine_with_chattts()  # 需要额外准备音色库

    print("\n" + "=" * 60)
    print("所有示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
