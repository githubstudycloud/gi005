"""
工具函数测试
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "production"))

from common.utils import ensure_dir, get_audio_duration, is_valid_audio


class TestEnsureDir:
    """测试 ensure_dir 函数"""

    def test_create_new_directory(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_dir = Path(tmp_dir) / "test_dir"
            assert not new_dir.exists()

            ensure_dir(str(new_dir))
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_existing_directory(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 目录已存在，不应报错
            ensure_dir(tmp_dir)
            assert Path(tmp_dir).exists()

    def test_nested_directory(self):
        """测试嵌套目录创建"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested = Path(tmp_dir) / "a" / "b" / "c"
            ensure_dir(str(nested))
            assert nested.exists()


class TestAudioValidation:
    """测试音频验证函数"""

    def test_invalid_path(self):
        """测试无效路径"""
        assert not is_valid_audio("/nonexistent/path/audio.wav")

    def test_invalid_extension(self):
        """测试无效扩展名"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not audio")
            try:
                assert not is_valid_audio(f.name)
            finally:
                os.unlink(f.name)


class TestLogger:
    """测试日志系统"""

    def test_get_logger(self):
        """测试获取 logger"""
        from common.logger import get_logger

        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_setup_logging(self):
        """测试日志配置"""
        from common.logger import setup_logging, get_logger

        with tempfile.TemporaryDirectory() as tmp_dir:
            setup_logging(
                level="DEBUG",
                log_dir=tmp_dir,
                console_output=False,
                file_output=True,
            )

            logger = get_logger("test_setup")
            logger.info("Test message")

            # 检查日志文件是否创建
            log_files = list(Path(tmp_dir).glob("*.log"))
            assert len(log_files) > 0


class TestParseSize:
    """测试大小解析"""

    def test_parse_bytes(self):
        """测试字节解析"""
        from common.logger import parse_size

        assert parse_size("1024B") == 1024
        assert parse_size("100B") == 100

    def test_parse_kilobytes(self):
        """测试 KB 解析"""
        from common.logger import parse_size

        assert parse_size("1KB") == 1024
        assert parse_size("10KB") == 10 * 1024

    def test_parse_megabytes(self):
        """测试 MB 解析"""
        from common.logger import parse_size

        assert parse_size("1MB") == 1024 * 1024
        assert parse_size("10MB") == 10 * 1024 * 1024

    def test_parse_gigabytes(self):
        """测试 GB 解析"""
        from common.logger import parse_size

        assert parse_size("1GB") == 1024 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
