"""
NeMo MSDD 代码结构测试（不依赖 NeMo 安装）
验证代码结构、导入和方法签名的正确性
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestNeMoMSDDStructure(unittest.TestCase):
    """测试 NeMo MSDD 代码结构"""

    def test_module_import(self):
        """测试模块导入"""
        try:
            from diarization import nemo_msdd_diarizer
            self.assertTrue(hasattr(nemo_msdd_diarizer, 'NeMoMSDDDiarizer'))
        except ImportError as e:
            self.fail(f"Failed to import module: {e}")

    def test_class_initialization(self):
        """测试类初始化"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer

        diarizer = NeMoMSDDDiarizer(
            device="cpu",
            output_dir="./test_outputs",
            cache_dir="./test_cache"
        )

        self.assertEqual(diarizer.device, "cpu")
        self.assertEqual(str(diarizer.output_dir), "test_outputs")
        self.assertEqual(str(diarizer.cache_dir), "test_cache")
        self.assertIsNone(diarizer.model)
        self.assertIsNone(diarizer.config)

    def test_methods_exist(self):
        """测试必要的方法存在"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer

        required_methods = [
            '_check_dependencies',
            '_create_config',
            '_create_manifest',
            'load_model',
            'diarize',
            '_parse_rttm',
            'format_output'
        ]

        for method in required_methods:
            self.assertTrue(
                hasattr(NeMoMSDDDiarizer, method),
                f"Missing method: {method}"
            )

    def test_create_config(self):
        """测试配置创建"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer

        diarizer = NeMoMSDDDiarizer()
        config = diarizer._create_config(
            manifest_path="test_manifest.json",
            num_speakers=3,
            oracle_vad=False
        )

        # 验证配置结构
        self.assertIn('diarizer', config)
        self.assertEqual(config.diarizer.manifest_filepath, "test_manifest.json")
        self.assertEqual(config.diarizer.oracle_vad, False)

        # 验证多尺度配置
        self.assertEqual(
            config.diarizer.speaker_embeddings.parameters.window_length_in_sec,
            [1.5, 1.25, 1.0, 0.75, 0.5]
        )
        self.assertEqual(
            len(config.diarizer.speaker_embeddings.parameters.shift_length_in_sec),
            5
        )

    @patch('torchaudio.load')
    def test_create_manifest(self, mock_load):
        """测试清单文件创建"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer
        import torch

        # Mock torchaudio.load
        mock_waveform = torch.randn(1, 16000 * 10)  # 10秒音频
        mock_load.return_value = (mock_waveform, 16000)

        diarizer = NeMoMSDDDiarizer(output_dir="./test_output")

        # 创建临时目录
        diarizer.output_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = diarizer._create_manifest(
            audio_path="test_audio.wav",
            num_speakers=3
        )

        # 验证文件创建
        self.assertTrue(Path(manifest_path).exists())

        # 读取并验证内容
        import json
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        self.assertIn('audio_filepath', manifest)
        self.assertIn('duration', manifest)
        self.assertEqual(manifest['num_speakers'], 3)

        # 清理
        Path(manifest_path).unlink()

    def test_parse_rttm(self):
        """测试 RTTM 解析"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer
        import tempfile

        # 创建测试 RTTM 文件
        rttm_content = """SPEAKER test_audio 1 0.00 2.50 <NA> <NA> SPEAKER_00 <NA>
SPEAKER test_audio 1 2.50 1.80 <NA> <NA> SPEAKER_01 <NA>
SPEAKER test_audio 1 4.30 3.20 <NA> <NA> SPEAKER_00 <NA>
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.rttm', delete=False) as f:
            f.write(rttm_content)
            rttm_path = Path(f.name)

        try:
            diarizer = NeMoMSDDDiarizer()
            segments = diarizer._parse_rttm(rttm_path)

            # 验证解析结果
            self.assertEqual(len(segments), 3)

            # 验证第一个片段
            self.assertEqual(segments[0]['start'], 0.0)
            self.assertEqual(segments[0]['end'], 2.5)
            self.assertEqual(segments[0]['duration'], 2.5)
            self.assertEqual(segments[0]['speaker'], 'SPEAKER_00')

            # 验证第二个片段
            self.assertEqual(segments[1]['start'], 2.5)
            self.assertEqual(segments[1]['speaker'], 'SPEAKER_01')

        finally:
            rttm_path.unlink()

    def test_format_output(self):
        """测试结果格式化"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer

        diarizer = NeMoMSDDDiarizer()

        test_result = {
            "audio_path": "test_audio.wav",
            "num_speakers": 2,
            "segments": [
                {"start": 0.0, "end": 2.5, "duration": 2.5, "speaker": "SPEAKER_00"},
                {"start": 2.5, "end": 4.3, "duration": 1.8, "speaker": "SPEAKER_01"}
            ],
            "rttm_path": "test.rttm"
        }

        # 测试不同格式
        simple_output = diarizer.format_output(test_result, format_type="simple")
        self.assertIn("Detected 2 speakers", simple_output)
        self.assertIn("SPEAKER_00", simple_output)

        detailed_output = diarizer.format_output(test_result, format_type="detailed")
        self.assertIn("NeMo MSDD Speaker Diarization Results", detailed_output)
        self.assertIn("test_audio.wav", detailed_output)

        json_output = diarizer.format_output(test_result, format_type="json")
        import json
        parsed = json.loads(json_output)
        self.assertEqual(parsed['num_speakers'], 2)
        self.assertEqual(len(parsed['segments']), 2)

    def test_directory_creation(self):
        """测试目录自动创建"""
        from diarization.nemo_msdd_diarizer import NeMoMSDDDiarizer
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()

        try:
            output_dir = Path(temp_dir) / "output" / "nested"
            cache_dir = Path(temp_dir) / "cache" / "nested"

            diarizer = NeMoMSDDDiarizer(
                output_dir=str(output_dir),
                cache_dir=str(cache_dir)
            )

            # 验证目录创建
            self.assertTrue(output_dir.exists())
            self.assertTrue(cache_dir.exists())

        finally:
            shutil.rmtree(temp_dir)


class TestNeMoMSDDIntegration(unittest.TestCase):
    """集成测试（需要 NeMo 安装）"""

    def test_nemo_import(self):
        """测试 NeMo 导入（如果已安装）"""
        try:
            import nemo.collections.asr as nemo_asr
            print("\n✓ NeMo is installed")
            print(f"  Location: {nemo_asr.__file__}")
            self.assertTrue(True)
        except ImportError:
            self.skipTest("NeMo not installed - skipping integration tests")


def run_tests():
    """运行测试"""
    print("=" * 70)
    print("NeMo MSDD Structure Tests")
    print("=" * 70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestNeMoMSDDStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestNeMoMSDDIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
