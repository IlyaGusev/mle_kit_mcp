import os

from mle_kit_mcp.tools import bash
from mle_kit_mcp.files import get_workspace_dir


def test_bash() -> None:
    result = bash('echo "Hello World"')
    assert result == "Command stdout: Hello World"

    result = bash("pwd")
    assert result == "Command stdout: /workdir"

    result = bash("touch dummy")
    assert os.path.exists(get_workspace_dir() / "dummy")

    result = bash("fddafad")
    assert "fddafad: command not found" in result


def test_bash_cwd() -> None:
    bash("mkdir -p dummy_dir")
    bash("touch dummy", cwd="dummy_dir")
    assert os.path.exists(get_workspace_dir() / "dummy_dir" / "dummy")


def test_bash_timeout_base() -> None:
    result = bash("sleep 10", timeout=5)
    assert "Command timed out" in result


def test_bash_timeout_with_output() -> None:
    result = bash("echo 'hello' && sleep 100", timeout=5)
    assert "hello" in result
    assert "Command timed out" in result
