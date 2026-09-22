import pytest
from pathlib import Path
from python_mcp.security import SecurityManager, SecurityError


def test_security_manager_defaults(tmp_path: Path):
    manager = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    # Path inside tmp_path should resolve
    test_file = tmp_path / "inside.txt"
    resolved = manager.resolve_path("inside.txt")
    assert resolved == test_file.resolve()


def test_security_manager_blocks_outside_path(tmp_path: Path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    manager = SecurityManager(allowed_directories=[sandbox], base_dir=sandbox)

    # Trying to access outside sandbox should raise SecurityError
    with pytest.raises(SecurityError):
        manager.resolve_path(tmp_path / "outside.txt")

    with pytest.raises(SecurityError):
        manager.resolve_path("../outside.txt")


def test_security_manager_allow_all(tmp_path: Path):
    manager = SecurityManager(allowed_directories=["*"])
    assert manager.allow_all is True
    # Can resolve anywhere
    resolved = manager.resolve_path("/etc")
    assert resolved == Path("/etc").resolve()


def test_security_manager_validate_path(tmp_path: Path):
    manager = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello")

    # must_exist
    assert manager.validate_path("sample.txt", must_exist=True) == file_path.resolve()

    # must_be_file
    assert manager.validate_path("sample.txt", must_be_file=True) == file_path.resolve()

    # non-existent file
    with pytest.raises(FileNotFoundError):
        manager.validate_path("does_not_exist.txt", must_exist=True)

    # directory checking
    dir_path = tmp_path / "subdir"
    dir_path.mkdir()
    assert manager.validate_path("subdir", must_be_dir=True) == dir_path.resolve()

    with pytest.raises(NotADirectoryError):
        manager.validate_path("sample.txt", must_be_dir=True)

    with pytest.raises(IsADirectoryError):
        manager.validate_path("subdir", must_be_file=True)
