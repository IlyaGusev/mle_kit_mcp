import fire  # type: ignore
from pathlib import Path
import uvicorn
from mcp.server.fastmcp import FastMCP

from .files import set_workspace_dir
from .tools.bash import bash
from .tools.text_editor import text_editor
from .tools.remote_gpu import (
    remote_bash,
    create_remote_text_editor,
    remote_download,
)


server = FastMCP("MLE kit MCP", stateless_http=True)

remote_text_editor = create_remote_text_editor(text_editor)

server.add_tool(bash)
server.add_tool(text_editor)
server.add_tool(remote_bash)
server.add_tool(remote_text_editor)
server.add_tool(remote_download)

http_app = server.streamable_http_app()


def run(host: str = "0.0.0.0", port: int = 5050, workspace: str = "workdir") -> None:
    workspace_path = Path(workspace)
    set_workspace_dir(workspace_path)
    uvicorn.run(http_app, host=host, port=port)


if __name__ == "__main__":
    fire.Fire(run)
