import json
import pytest
from pathlib import Path
from python_mcp.server import create_server


@pytest.mark.asyncio
async def test_server_tools_and_prompts(tmp_path: Path):
    server = create_server(allowed_directories=[tmp_path], base_dir=tmp_path)

    # Verify tool listing
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    expected_tools = {
        "read_file",
        "read_multiple_files",
        "write_file",
        "append_file",
        "edit_file",
        "create_directory",
        "list_directory",
        "move_file",
        "copy_file",
        "delete_file",
        "get_file_info",
        "search_files",
        "search_file_content",
    }
    assert expected_tools.issubset(tool_names)

    # Verify prompt listing
    prompts = await server.list_prompts()
    prompt_names = {p.name for p in prompts}
    expected_prompts = {
        "organize_directory",
        "refactor_file",
        "find_and_replace",
        "clean_directory",
        "scaffold_project",
        "batch_rename",
    }
    assert expected_prompts.issubset(prompt_names)

    # Test calling a tool via server: write_file
    target_path = str(tmp_path / "hello.txt")
    write_res = await server.call_tool("write_file", {"path": target_path, "content": "world"})
    assert write_res.is_error is False

    # Test calling a tool: read_file
    read_res = await server.call_tool("read_file", {"path": target_path})
    assert read_res.is_error is False

    # Test prompt rendering: organize_directory
    prompt_res = await server.get_prompt("organize_directory", {"directory": str(tmp_path)})
    assert len(prompt_res.messages) > 0

    # Test resource: status
    status_content = await server.read_resource("system://file-server/status")
    raw_json = status_content[0].content if isinstance(status_content, list) else status_content
    status_dict = json.loads(raw_json)
    assert status_dict["server_name"] == "prompt-file-manager"
    assert status_dict["allow_all"] is False
