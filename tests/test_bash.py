import os

from mle_kit_mcp.tools import bash
from mle_kit_mcp.files import WORKSPACE_DIR_PATH


def test_bash() -> None:
    result = bash('echo "Hello World"')
    assert result == "Hello World"

    result = bash("pwd")
    assert result == "/workdir"

    result = bash("touch dummy")
    assert os.path.exists(WORKSPACE_DIR_PATH / "dummy")

    result = bash("fddafad")
    assert "fddafad: command not found" in result