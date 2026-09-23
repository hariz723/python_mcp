import json
from pathlib import Path

from python_mcp.ollama_agent import OllamaFileAgent
from python_mcp.security import SecurityManager


def test_agent_init_and_tools(tmp_path: Path):
    sec = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    agent = OllamaFileAgent(model="gpt-oss:latest", security_manager=sec, verbose=False)

    assert agent.model == "gpt-oss:latest"
    assert len(agent.tools_map) == 13

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
    assert expected_tools.issubset(set(agent.tools_map.keys()))


def test_agent_tool_execution(tmp_path: Path):
    sec = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    agent = OllamaFileAgent(security_manager=sec, verbose=False)

    # 1. Write file through agent tool
    write_tool = agent.tools_map["write_file"]
    res_raw = write_tool(path=str(tmp_path / "agent_test.txt"), content="agent content\nline 2")
    res = json.loads(res_raw)
    assert res["success"] is True

    # 2. Read file through agent tool
    read_tool = agent.tools_map["read_file"]
    res_raw = read_tool(path=str(tmp_path / "agent_test.txt"))
    res = json.loads(res_raw)
    assert res["success"] is True
    assert "agent content" in res["content"]

    # 3. Security error when accessing outside allowed path
    res_outside = json.loads(read_tool(path="/etc/passwd"))
    assert res_outside["success"] is False
    assert "Access denied" in res_outside["error"]


def test_agent_reset(tmp_path: Path):
    sec = SecurityManager(allowed_directories=[tmp_path], base_dir=tmp_path)
    agent = OllamaFileAgent(security_manager=sec, verbose=False)

    agent.messages.append({"role": "user", "content": "hello"})
    assert len(agent.messages) == 2

    agent.reset()
    assert len(agent.messages) == 1
    assert agent.messages[0]["role"] == "system"
