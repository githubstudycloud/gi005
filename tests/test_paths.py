"""
路径配置测试
"""
import pytest
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProjectRoot:
    """测试项目根目录"""

    def test_get_project_root(self):
        """测试获取项目根目录"""
        from src.common.paths import get_project_root, PROJECT_ROOT

        root = get_project_root()
        assert root == PROJECT_ROOT
        assert root.exists()
        assert root.is_dir()

    def test_project_root_structure(self):
        """测试项目根目录结构"""
        from src.common.paths import PROJECT_ROOT

        # 检查关键目录是否存在
        assert (PROJECT_ROOT / "voice-clone-tts").exists()
        assert (PROJECT_ROOT / "packages").exists()


class TestModelPaths:
    """测试模型路径配置"""

    def test_xtts_model_path(self):
        """测试 XTTS 模型路径"""
        from src.common.paths import XTTS_MODEL_PATH

        assert "xtts_v2" in str(XTTS_MODEL_PATH)
        assert "packages" in str(XTTS_MODEL_PATH)
        assert "models" in str(XTTS_MODEL_PATH)

    def test_openvoice_model_path(self):
        """测试 OpenVoice 模型路径"""
        from src.common.paths import OPENVOICE_MODEL_PATH

        assert "openvoice" in str(OPENVOICE_MODEL_PATH)
        assert "packages" in str(OPENVOICE_MODEL_PATH)
        assert "models" in str(OPENVOICE_MODEL_PATH)

    def test_whisper_model_path(self):
        """测试 Whisper 模型路径"""
        from src.common.paths import WHISPER_MODEL_PATH

        assert "whisper" in str(WHISPER_MODEL_PATH)
        assert "packages" in str(WHISPER_MODEL_PATH)
        assert "models" in str(WHISPER_MODEL_PATH)

    def test_gpt_sovits_repo_path(self):
        """测试 GPT-SoVITS 仓库路径"""
        from src.common.paths import GPT_SOVITS_REPO_PATH

        assert "GPT-SoVITS" in str(GPT_SOVITS_REPO_PATH)
        assert "packages" in str(GPT_SOVITS_REPO_PATH)
        assert "repos" in str(GPT_SOVITS_REPO_PATH)


class TestToolPaths:
    """测试工具路径配置"""

    def test_ffmpeg_path(self):
        """测试 FFmpeg 路径"""
        from src.common.paths import FFMPEG_PATH

        assert "ffmpeg.exe" in str(FFMPEG_PATH)
        assert "packages" in str(FFMPEG_PATH)
        assert "tools" in str(FFMPEG_PATH)

    def test_ffprobe_path(self):
        """测试 FFprobe 路径"""
        from src.common.paths import FFPROBE_PATH

        assert "ffprobe.exe" in str(FFPROBE_PATH)
        assert "packages" in str(FFPROBE_PATH)
        assert "tools" in str(FFPROBE_PATH)


class TestDataPaths:
    """测试数据路径配置"""

    def test_voices_dir(self):
        """测试音色目录路径"""
        from src.common.paths import VOICES_DIR

        assert "voices" in str(VOICES_DIR)

    def test_test_audio_dir(self):
        """测试音频目录路径"""
        from src.common.paths import TEST_AUDIO_DIR

        assert "test_audio" in str(TEST_AUDIO_DIR)

    def test_output_dir(self):
        """测试输出目录路径"""
        from src.common.paths import OUTPUT_DIR

        assert "output" in str(OUTPUT_DIR)


class TestHelperFunctions:
    """测试辅助函数"""

    def test_ensure_dir(self):
        """测试目录创建函数"""
        from src.common.paths import ensure_dir
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            new_dir = Path(tmp_dir) / "test_dir" / "nested"
            result = ensure_dir(new_dir)

            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_get_model_path(self):
        """测试获取模型路径函数"""
        from src.common.paths import get_model_path, XTTS_MODEL_PATH, OPENVOICE_MODEL_PATH

        assert get_model_path("xtts") == XTTS_MODEL_PATH
        assert get_model_path("XTTS") == XTTS_MODEL_PATH  # 大小写不敏感
        assert get_model_path("openvoice") == OPENVOICE_MODEL_PATH

    def test_verify_model_paths(self):
        """测试验证模型路径函数"""
        from src.common.paths import verify_model_paths

        results = verify_model_paths()

        # 确保返回了所有预期的引擎
        assert "xtts" in results
        assert "openvoice" in results
        assert "whisper" in results
        assert "gpt-sovits" in results
        assert "ffmpeg" in results

        # 检查每个结果的结构
        for name, info in results.items():
            assert "path" in info
            assert "exists" in info
            assert isinstance(info["exists"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
