"""Path resolution and security controls for file system operations."""

from pathlib import Path
from typing import Sequence


class SecurityError(PermissionError):
    """Raised when an operation violates path sandboxing or permission constraints."""
    pass


class SecurityManager:
    """Manages allowed directories and sandboxing for the MCP server.

    Ensures that file system manipulation operations cannot escape
    the configured boundaries.
    """

    def __init__(
        self,
        allowed_directories: Sequence[str | Path] | None = None,
        base_dir: str | Path | None = None,
    ):
        """Initialize the SecurityManager.

        Args:
            allowed_directories: List of directories within which operations are permitted.
                If None or contains "*", unrestricted access is granted.
            base_dir: Base directory used to resolve relative paths. Defaults to Path.cwd().
        """
        self.base_dir = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()

        if allowed_directories is None:
            # Default to base_dir if none provided
            self.allow_all = False
            self.allowed_directories = [self.base_dir]
        elif "*" in allowed_directories:
            self.allow_all = True
            self.allowed_directories = []
        else:
            self.allow_all = False
            self.allowed_directories = [
                Path(d).expanduser().resolve() for d in allowed_directories
            ]

    def resolve_path(self, path_str: str | Path) -> Path:
        """Resolve a path string safely, expanding user paths and checking boundaries.

        Args:
            path_str: The relative or absolute path string.

        Returns:
            Resolved absolute Path.

        Raises:
            SecurityError: If the resolved path lies outside all allowed directories.
        """
        path = Path(path_str).expanduser()
        if not path.is_absolute():
            path = (self.base_dir / path).resolve()
        else:
            path = path.resolve()

        if self.allow_all:
            return path

        # Check if path is contained in any allowed directory
        is_allowed = False
        for allowed_dir in self.allowed_directories:
            try:
                # is_relative_to returns True if path == allowed_dir or is child of allowed_dir
                if path.is_relative_to(allowed_dir):
                    is_allowed = True
                    break
            except AttributeError:
                # Fallback for Python versions before 3.9 (though we are on 3.13)
                try:
                    path.relative_to(allowed_dir)
                    is_allowed = True
                    break
                except ValueError:
                    pass

        if not is_allowed:
            allowed_str = ", ".join(str(d) for d in self.allowed_directories)
            raise SecurityError(
                f"Access denied: Path '{path}' is outside allowed directories: [{allowed_str}]"
            )

        return path

    def validate_path(
        self,
        path_str: str | Path,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
    ) -> Path:
        """Resolve path and optionally validate existence and file/directory type.

        Args:
            path_str: Path to validate.
            must_exist: If True, path must exist.
            must_be_file: If True, path must exist and be a regular file.
            must_be_dir: If True, path must exist and be a directory.

        Returns:
            Resolved Path.

        Raises:
            SecurityError: If outside allowed directories.
            FileNotFoundError: If must_exist is True and path does not exist.
            IsADirectoryError: If must_be_file is True and path is a directory.
            NotADirectoryError: If must_be_dir is True and path is a file.
        """
        path = self.resolve_path(path_str)

        if must_exist and not path.exists():
            raise FileNotFoundError(f"File or directory does not exist: {path}")

        if must_be_file:
            if not path.exists():
                raise FileNotFoundError(f"File does not exist: {path}")
            if not path.is_file():
                raise IsADirectoryError(f"Expected a regular file, but found a directory: {path}")

        if must_be_dir:
            if not path.exists():
                raise FileNotFoundError(f"Directory does not exist: {path}")
            if not path.is_dir():
                raise NotADirectoryError(f"Expected a directory, but found a file: {path}")

        return path
