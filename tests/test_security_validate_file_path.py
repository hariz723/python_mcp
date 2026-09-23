import pytest
from pathlib import Path
from python_mcp.security import SecurityManager, SecurityError


def test_validate_file_path_basic(tmp_path: Path):
    manager = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    file_path = tmp_path / "sample.txt"
    file_path.write_text("content")
    dir_path = tmp_path / "subdir"
    dir_path.mkdir()

    # Valid file
    assert manager.validate_file_path("sample.txt") == file_path.resolve()
    # Must exist flag True
    assert manager.validate_file_path("sample.txt", must_exist=True) == file_path.resolve()

    # Non-existent file should raise FileNotFoundError regardless of must_exist flag
    with pytest.raises(FileNotFoundError):
        manager.validate_file_path("does_not_exist.txt")
    with pytest.raises(FileNotFoundError):
        manager.validate_file_path("does_not_exist.txt", must_exist=True)

    # Directory should raise IsADirectoryError
    with pytest.raises(IsADirectoryError):
        manager.validate_file_path("subdir")

    # Path outside allowed directory should raise SecurityError
    with pytest.raises(SecurityError):
        manager.validate_file_path("../outside.txt")
