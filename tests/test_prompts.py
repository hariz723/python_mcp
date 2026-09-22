import pytest
from python_mcp.server import create_server


@pytest.mark.asyncio
async def test_all_prompts(tmp_path):
    server = create_server(allowed_directories=[tmp_path], base_dir=tmp_path)

    # 1. organize_directory
    p1 = await server.get_prompt("organize_directory", {"directory": "my_folder", "goal": "group by extension"})
    assert "my_folder" in p1.messages[0].content.text
    assert "group by extension" in p1.messages[0].content.text

    # 2. refactor_file
    p2 = await server.get_prompt("refactor_file", {"file_path": "app.py", "instruction": "use async def"})
    assert "app.py" in p2.messages[0].content.text
    assert "use async def" in p2.messages[0].content.text

    # 3. find_and_replace
    p3 = await server.get_prompt("find_and_replace", {"directory": "src", "find_text": "old_var", "replace_text": "new_var"})
    assert "old_var" in p3.messages[0].content.text
    assert "new_var" in p3.messages[0].content.text

    # 4. clean_directory
    p4 = await server.get_prompt("clean_directory", {"directory": "logs"})
    assert "logs" in p4.messages[0].content.text

    # 5. scaffold_project
    p5 = await server.get_prompt("scaffold_project", {
        "root_directory": "new_app",
        "project_type": "fastapi",
        "project_name": "my_api",
        "requirements": "auth and postgres"
    })
    assert "my_api" in p5.messages[0].content.text
    assert "fastapi" in p5.messages[0].content.text

    # 6. batch_rename
    p6 = await server.get_prompt("batch_rename", {"directory": "photos", "pattern": "*.jpeg", "naming_rule": "photo_001.jpg"})
    assert "photos" in p6.messages[0].content.text
    assert "*.jpeg" in p6.messages[0].content.text
