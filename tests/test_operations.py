import pytest
from pathlib import Path
from python_mcp import operations


def test_write_and_read_file(tmp_path: Path):
    target = tmp_path / "sub" / "hello.txt"
    res_write = operations.write_file(target, "Line 1\nLine 2\nLine 3\n")
    assert res_write["lines_written"] == 3
    assert target.exists()

    res_read = operations.read_file(target)
    assert res_read["total_lines"] == 3
    assert res_read["content"] == "Line 1\nLine 2\nLine 3\n"

    # Test line windowing
    sliced = operations.read_file(target, offset_line=2, limit_lines=1)
    assert sliced["start_line"] == 2
    assert sliced["end_line"] == 2
    assert sliced["content"] == "Line 2\n"


def test_append_file(tmp_path: Path):
    target = tmp_path / "log.txt"
    operations.write_file(target, "first\n")
    operations.append_file(target, "second\n")
    assert target.read_text() == "first\nsecond\n"


def test_edit_file(tmp_path: Path):
    target = tmp_path / "code.py"
    operations.write_file(target, "def greet():\n    print('hi')\n")

    res = operations.edit_file(target, "print('hi')", "print('hello world')")
    assert res["replacements_made"] == 1
    assert "print('hello world')" in target.read_text()

    # Target not found should raise ValueError
    with pytest.raises(ValueError):
        operations.edit_file(target, "nonexistent", "replacement")


def test_list_directory_and_search(tmp_path: Path):
    (tmp_path / "a.py").write_text("import sys\n")
    (tmp_path / "b.txt").write_text("plain text\n")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "c.py").write_text("import os\n")

    # List directory
    listing = operations.list_directory(tmp_path, recursive=True)
    assert listing["total_entries"] >= 3

    # Search files
    py_files = operations.search_files(tmp_path, pattern="*.py", recursive=True)
    names = [f["name"] for f in py_files]
    assert "a.py" in names
    assert "c.py" in names
    assert "b.txt" not in names

    # Search content
    content_matches = operations.search_file_content(tmp_path, query="import")
    assert len(content_matches) == 2


def test_move_and_copy(tmp_path: Path):
    src = tmp_path / "original.txt"
    src.write_text("source content")

    copied = tmp_path / "copied.txt"
    operations.copy_path(src, copied)
    assert copied.exists()
    assert copied.read_text() == "source content"

    moved = tmp_path / "moved.txt"
    operations.move_path(copied, moved)
    assert not copied.exists()
    assert moved.exists()
    assert moved.read_text() == "source content"


def test_delete_and_metadata(tmp_path: Path):
    file_path = tmp_path / "info.txt"
    file_path.write_text("line 1\nline 2\n")

    meta = operations.get_metadata(file_path)
    assert meta["is_file"] is True
    assert meta["line_count"] == 2

    # Delete file
    del_res = operations.delete_path(file_path)
    assert del_res["status"] == "deleted"
    assert not file_path.exists()
