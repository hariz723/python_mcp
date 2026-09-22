"""Core file system manipulation operations for MCP tools."""

from datetime import datetime, timezone
import fnmatch
import mimetypes
import os
from pathlib import Path
import shutil
from typing import Any

# Ignored directory names when scanning recursively
DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "node_modules",
    ".tox",
    ".eggs",
}


def is_binary_file(path: Path, sample_size: int = 8192) -> bool:
    """Check if a file appears to be binary by inspecting initial bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample_size)
            if b"\x00" in chunk:
                return True
        return False
    except Exception:
        return False


def read_file(
    path: Path,
    offset_line: int = 1,
    limit_lines: int | None = None,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Read content of a text file with optional line-level slicing.

    Args:
        path: Path to the file.
        offset_line: 1-indexed line number to start reading from.
        limit_lines: Maximum number of lines to read. None reads to EOF.
        encoding: File text encoding.

    Returns:
        Dictionary containing file metadata, sliced line range, and content.
    """
    if is_binary_file(path):
        mime, _ = mimetypes.guess_type(str(path))
        size = path.stat().st_size
        return {
            "path": str(path),
            "is_binary": True,
            "mime_type": mime or "application/octet-stream",
            "size_bytes": size,
            "message": f"Binary file ({size} bytes). Cannot read as text.",
        }

    with open(path, "r", encoding=encoding, errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    start_idx = max(0, offset_line - 1)
    if limit_lines is not None:
        end_idx = min(total_lines, start_idx + limit_lines)
    else:
        end_idx = total_lines

    selected_lines = lines[start_idx:end_idx]

    return {
        "path": str(path),
        "is_binary": False,
        "total_lines": total_lines,
        "start_line": start_idx + 1 if total_lines > 0 else 0,
        "end_line": end_idx,
        "content": "".join(selected_lines),
    }


def read_multiple_files(paths: list[Path], encoding: str = "utf-8") -> list[dict[str, Any]]:
    """Read multiple files in a single operation.

    Args:
        paths: List of file paths to read.
        encoding: File text encoding.

    Returns:
        List of results or errors for each requested file.
    """
    results: list[dict[str, Any]] = []
    for p in paths:
        try:
            if not p.exists():
                results.append({"path": str(p), "error": "File does not exist"})
            elif not p.is_file():
                results.append({"path": str(p), "error": "Not a regular file"})
            else:
                results.append(read_file(p, encoding=encoding))
        except Exception as e:
            results.append({"path": str(p), "error": str(e)})
    return results


def write_file(
    path: Path,
    content: str,
    overwrite: bool = True,
    make_parents: bool = True,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Create or overwrite a file with given text content.

    Args:
        path: Path to target file.
        content: String content to write.
        overwrite: If False and target exists, raise FileExistsError.
        make_parents: If True, automatically create parent directories.
        encoding: File text encoding.

    Returns:
        Dictionary with written path, bytes count, and line count.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(f"Target file already exists: {path}")

    if make_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding) as f:
        bytes_written = f.write(content)

    return {
        "path": str(path),
        "bytes_written": bytes_written,
        "lines_written": len(content.splitlines()),
        "status": "created" if not path.exists() else "written",
    }


def append_file(
    path: Path,
    content: str,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Append text content to an existing file or create it if not present.

    Args:
        path: Path to target file.
        content: Text content to append.
        encoding: File text encoding.

    Returns:
        Dictionary with path, appended bytes, and total size.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding=encoding) as f:
        bytes_appended = f.write(content)

    return {
        "path": str(path),
        "bytes_appended": bytes_appended,
        "total_size": path.stat().st_size,
    }


def edit_file(
    path: Path,
    target_snippet: str,
    replacement_snippet: str,
    allow_multiple: bool = False,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Targeted replacement of text within an existing file.

    Args:
        path: Path to the file to edit.
        target_snippet: The exact string to find and replace.
        replacement_snippet: The replacement text.
        allow_multiple: If True, replaces all occurrences. Otherwise,
            errors if count != 1.
        encoding: File text encoding.

    Returns:
        Dictionary with path and count of replacements made.
    """
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding=encoding) as f:
        content = f.read()

    count = content.count(target_snippet)
    if count == 0:
        raise ValueError(
            f"Target snippet not found in {path}. Make sure whitespace and formatting match exactly."
        )

    if count > 1 and not allow_multiple:
        raise ValueError(
            f"Found {count} occurrences of target snippet in {path}. Set allow_multiple=True to replace all."
        )

    new_content = content.replace(target_snippet, replacement_snippet)

    with open(path, "w", encoding=encoding) as f:
        f.write(new_content)

    return {
        "path": str(path),
        "replacements_made": count,
        "new_total_lines": len(new_content.splitlines()),
    }


def create_directory(path: Path, exist_ok: bool = True) -> dict[str, Any]:
    """Create a new directory and any missing parent directories.

    Args:
        path: Directory path to create.
        exist_ok: If True, do not error if directory already exists.

    Returns:
        Dictionary with path and success status.
    """
    already_existed = path.exists()
    path.mkdir(parents=True, exist_ok=exist_ok)
    return {
        "path": str(path),
        "created": not already_existed,
        "status": "already_exists" if already_existed else "created",
    }


def list_directory(
    path: Path,
    recursive: bool = False,
    max_depth: int = 2,
    include_hidden: bool = False,
) -> dict[str, Any]:
    """List directory contents with file metadata.

    Args:
        path: Directory to inspect.
        recursive: If True, recursively list subdirectories up to max_depth.
        max_depth: Maximum recursion depth (1 = top level only).
        include_hidden: Whether to include dotfiles / hidden entries.

    Returns:
        Dictionary with summary statistics and entries list.
    """
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    entries: list[dict[str, Any]] = []

    def _scan(current_dir: Path, current_depth: int) -> None:
        try:
            for item in sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if not include_hidden and item.name.startswith("."):
                    continue

                if item.name in DEFAULT_EXCLUDED_DIRS:
                    continue

                try:
                    stat = item.stat()
                    entry = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size_bytes": stat.st_size if item.is_file() else None,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    }
                    entries.append(entry)

                    if recursive and item.is_dir() and current_depth < max_depth:
                        _scan(item, current_depth + 1)
                except (PermissionError, FileNotFoundError):
                    continue
        except PermissionError:
            pass

    _scan(path, 1)

    file_count = sum(1 for e in entries if e["type"] == "file")
    dir_count = sum(1 for e in entries if e["type"] == "directory")

    return {
        "path": str(path),
        "total_entries": len(entries),
        "file_count": file_count,
        "dir_count": dir_count,
        "entries": entries,
    }


def search_files(
    directory: Path,
    pattern: str = "*",
    recursive: bool = True,
    include_hidden: bool = False,
) -> list[dict[str, Any]]:
    """Search for files and directories matching a glob pattern.

    Args:
        directory: Directory to search within.
        pattern: Glob pattern (e.g. '*.py', '**/*.json', 'test_*').
        recursive: If True, search recursively.
        include_hidden: Whether to match hidden files.

    Returns:
        List of matching file metadata dictionaries.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Search target is not a directory: {directory}")

    results: list[dict[str, Any]] = []

    if recursive:
        candidates = directory.rglob(pattern)
    else:
        candidates = directory.glob(pattern)

    for item in candidates:
        if not include_hidden and any(part.startswith(".") for part in item.relative_to(directory).parts):
            continue

        if any(part in DEFAULT_EXCLUDED_DIRS for part in item.relative_to(directory).parts):
            continue

        try:
            stat = item.stat()
            results.append({
                "name": item.name,
                "path": str(item),
                "relative_path": str(item.relative_to(directory)),
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": stat.st_size if item.is_file() else None,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        except (PermissionError, FileNotFoundError):
            continue

    return results


def search_file_content(
    directory: Path,
    query: str,
    case_sensitive: bool = False,
    file_pattern: str = "*",
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """Search for text within files (grep-like).

    Args:
        directory: Directory to search within.
        query: String to search for.
        case_sensitive: Whether match should be case sensitive.
        file_pattern: File glob pattern to filter target files.
        max_results: Maximum number of match lines to return.

    Returns:
        List of matches containing file path, line number, and line content.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory}")

    matches: list[dict[str, Any]] = []
    query_cmp = query if case_sensitive else query.lower()

    for item in directory.rglob("*"):
        if len(matches) >= max_results:
            break

        if not item.is_file():
            continue

        # Skip ignored dirs and hidden files
        rel_parts = item.relative_to(directory).parts
        if any(p.startswith(".") for p in rel_parts) or any(p in DEFAULT_EXCLUDED_DIRS for p in rel_parts):
            continue

        if not fnmatch.fnmatch(item.name, file_pattern):
            continue

        if is_binary_file(item):
            continue

        try:
            with open(item, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    line_cmp = line if case_sensitive else line.lower()
                    if query_cmp in line_cmp:
                        matches.append({
                            "path": str(item),
                            "relative_path": str(item.relative_to(directory)),
                            "line_number": line_no,
                            "line_content": line.rstrip("\r\n"),
                        })
                        if len(matches) >= max_results:
                            break
        except Exception:
            continue

    return matches


def move_path(source: Path, destination: Path, overwrite: bool = False) -> dict[str, Any]:
    """Move or rename a file or directory.

    Args:
        source: Source file or directory path.
        destination: Destination file or directory path.
        overwrite: If True, replaces existing destination.

    Returns:
        Dictionary with source, destination, and status.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")

    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}")
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))

    return {
        "source": str(source),
        "destination": str(destination),
        "status": "moved",
    }


def copy_path(source: Path, destination: Path, overwrite: bool = False) -> dict[str, Any]:
    """Copy a file or directory tree.

    Args:
        source: Source path.
        destination: Target destination path.
        overwrite: If True, overwrite target.

    Returns:
        Dictionary with source, destination, and status.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")

    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}")
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)

    return {
        "source": str(source),
        "destination": str(destination),
        "status": "copied",
    }


def delete_path(path: Path, recursive: bool = False) -> dict[str, Any]:
    """Delete a file or directory.

    Args:
        path: Path to delete.
        recursive: Required to delete non-empty directories.

    Returns:
        Dictionary with path and status.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_dir():
        if not recursive and any(path.iterdir()):
            raise ValueError(
                f"Directory is not empty: {path}. Set recursive=True to delete directory and its contents."
            )
        shutil.rmtree(path)
        deleted_type = "directory"
    else:
        path.unlink()
        deleted_type = "file"

    return {
        "path": str(path),
        "deleted_type": deleted_type,
        "status": "deleted",
    }


def get_metadata(path: Path) -> dict[str, Any]:
    """Get comprehensive file or directory metadata.

    Args:
        path: Path to inspect.

    Returns:
        Dictionary with file size, permissions, timestamps, line count, and mime type.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    stat = path.stat()
    mime_type, _ = mimetypes.guess_type(str(path))

    line_count = None
    if path.is_file() and not is_binary_file(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                line_count = sum(1 for _ in f)
        except Exception:
            pass

    return {
        "name": path.name,
        "path": str(path),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "is_symlink": path.is_symlink(),
        "size_bytes": stat.st_size,
        "line_count": line_count,
        "mime_type": mime_type or ("inode/directory" if path.is_dir() else "application/octet-stream"),
        "permissions_octal": oct(stat.st_mode)[-3:],
        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }
