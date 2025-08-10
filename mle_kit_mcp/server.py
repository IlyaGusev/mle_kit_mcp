from pathlib import Path
from typing import Optional

import fire  # type: ignore
import uvicorn
from mcp.server.fastmcp import FastMCP

from .tools.bash import bash
from .tools.text_editor import text_editor
from .tools.remote_gpu import (
    remote_bash,
    create_remote_text_editor,
    remote_download,
)
from .files import get_workspace_dir, WorkspaceDirectory


def run(host: str = "0.0.0.0", port: int = 5050, workspace: Optional[str] = None) -> None:
    if workspace:
        WorkspaceDirectory.set_dir(Path(workspace))
    workspace_path = get_workspace_dir()
    workspace_path.mkdir(parents=True, exist_ok=True)

    server = FastMCP("MLE kit MCP", stateless_http=True)

    remote_text_editor = create_remote_text_editor(text_editor)

    server.add_tool(bash)
    server.add_tool(text_editor)
    server.add_tool(remote_bash)
    server.add_tool(remote_text_editor)
    server.add_tool(remote_download)

    http_app = server.streamable_http_app()

    uvicorn.run(http_app, host=host, port=port)


if __name__ == "__main__":
    fire.Fire(run)
