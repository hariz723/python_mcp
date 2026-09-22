"""MCP prompt templates for manipulating files with LLM guidance."""

from mcp.server.mcpserver import MCPServer
from python_mcp.security import SecurityManager


def register_prompts(server: MCPServer, security: SecurityManager) -> None:
    """Register MCP prompt templates for file system manipulation tasks.

    Args:
        server: Target MCPServer instance.
        security: SecurityManager instance.
    """

    @server.prompt(
        name="organize_directory",
        description="Prompt the LLM to inspect a directory and organize its files into structured folders.",
    )
    def organize_directory_prompt(
        directory: str = ".",
        goal: str = "categorize by file extension and logical purpose",
    ) -> str:
        """Prompt to organize a folder."""
        return f"""You are a file system organization assistant.

Your task is to inspect the directory '{directory}' and organize its contents according to this goal:
Goal: {goal}

Follow this step-by-step procedure:
1. Call `list_directory` on '{directory}' with recursive=False to inspect the current files.
2. Formulate a clean, sensible folder structure (e.g., separating documents, media, code, data).
3. Call `create_directory` for each new folder you plan to introduce.
4. Call `move_file` to relocate files into their appropriate destination subfolders.
5. Finally, call `list_directory` again to show the user the updated, clean directory layout.

Safety rule: Do not delete any files unless explicitly instructed by the user."""

    @server.prompt(
        name="refactor_file",
        description="Prompt the LLM to read a file, analyze it, and apply targeted modifications.",
    )
    def refactor_file_prompt(
        file_path: str,
        instruction: str,
    ) -> str:
        """Prompt to refactor or update a code/text file."""
        return f"""You are an expert code and text refactoring assistant.

Target File: {file_path}
Task Instructions: {instruction}

Follow this step-by-step procedure:
1. Call `read_file` on '{file_path}' to inspect its current content and exact line numbers.
2. Analyze the file and plan the necessary edits to satisfy the instructions.
3. For surgical modifications, use `edit_file` with the exact snippet to replace and the new replacement snippet.
   If rewriting the entire file is cleaner, use `write_file` with overwrite=True.
4. Call `read_file` or `get_file_info` on '{file_path}' to verify the changes took effect as intended.
5. Summarize the changes made clearly for the user."""

    @server.prompt(
        name="find_and_replace",
        description="Prompt the LLM to find text across files and replace it consistently.",
    )
    def find_and_replace_prompt(
        directory: str = ".",
        find_text: str = "",
        replace_text: str = "",
        file_pattern: str = "*",
    ) -> str:
        """Prompt to find and replace across multiple files."""
        return f"""You are a code maintenance assistant performing a global search-and-replace.

Directory: {directory}
Find: "{find_text}"
Replace with: "{replace_text}"
File Pattern filter: {file_pattern}

Follow this step-by-step procedure:
1. Call `search_file_content` in '{directory}' for '{find_text}' with file_pattern='{file_pattern}'.
2. Review the search results and verify which files and lines should be changed.
3. For each affected file, call `edit_file` targeting the exact snippet '{find_text}' and replacing with '{replace_text}'.
4. Call `search_file_content` again to verify that all occurrences have been properly updated.
5. Provide a summary listing each file updated and how many occurrences were replaced."""

    @server.prompt(
        name="clean_directory",
        description="Prompt the LLM to scan for and safely clean temporary, log, or cache files.",
    )
    def clean_directory_prompt(
        directory: str = ".",
        target_types: str = "cache files, temporary files, logs, __pycache__, .tmp",
    ) -> str:
        """Prompt to identify and delete temporary/clutter files."""
        return f"""You are a disk cleanup assistant.

Target Directory: {directory}
Targets to clean: {target_types}

Follow this step-by-step procedure:
1. Call `search_files` in '{directory}' to locate files matching common clutter patterns (*.tmp, *~, *.log, __pycache__, etc.).
2. Present a clear list of identified files with their sizes (obtained via `get_file_info`).
3. Call `delete_file` for each identified clutter file or directory.
4. Report the total number of files deleted and disk space reclaimed."""

    @server.prompt(
        name="scaffold_project",
        description="Prompt the LLM to create a new project directory structure with starter files.",
    )
    def scaffold_project_prompt(
        root_directory: str,
        project_type: str,
        project_name: str,
        requirements: str = "",
    ) -> str:
        """Prompt to scaffold a project structure with directories and starter files."""
        return f"""You are a software architect assistant.

Project Name: {project_name}
Project Type: {project_type}
Target Root: {root_directory}
Requirements: {requirements}

Follow this step-by-step procedure:
1. Plan an idiomatic, best-practice directory layout for a {project_type} project named '{project_name}'.
2. Call `create_directory` to create the project directory tree (e.g., src, tests, docs).
3. Call `write_file` to create initial configuration files (e.g., README.md, .gitignore, dependencies file).
4. Call `write_file` to write initial module or entrypoint boilerplate code.
5. Call `list_directory` recursively to present the completed project scaffold."""

    @server.prompt(
        name="batch_rename",
        description="Prompt the LLM to batch rename files according to a consistent pattern.",
    )
    def batch_rename_prompt(
        directory: str = ".",
        pattern: str = "*",
        naming_rule: str = "lowercase with underscores",
    ) -> str:
        """Prompt to batch rename files."""
        return f"""You are a file management assistant.

Directory: {directory}
Filter pattern: {pattern}
Naming rule: {naming_rule}

Follow this step-by-step procedure:
1. Call `search_files` or `list_directory` in '{directory}' matching pattern '{pattern}'.
2. For each file, compute the new filename adhering to the naming rule: '{naming_rule}'.
3. Call `move_file` for each item, renaming source to destination.
4. Report the mapping of original filenames to new filenames."""
