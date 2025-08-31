import os

from mle_kit_mcp.tools import bash
from mle_kit_mcp.files import get_workspace_dir


def test_bash() -> None:
    result = bash('echo "Hello World"')
    assert result == "Hello World"

    result = bash("pwd")
    assert result == "/workdir"

    result = bash("touch dummy")
    assert os.path.exists(get_workspace_dir() / "dummy")

    result = bash("fddafad")
    assert "fddafad: command not found" in result


def test_bash_cwd() -> None:
    bash("mkdir -p dummy_dir")
    bash("touch dummy", cwd="dummy_dir")
    assert os.path.exists(get_workspace_dir() / "dummy_dir" / "dummy")
