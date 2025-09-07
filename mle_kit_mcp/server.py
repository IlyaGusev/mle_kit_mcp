import os
from pathlib import Path
from typing import Optional, Literal

import fire  # type: ignore
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .tools.bash import bash
from .tools.text_editor import text_editor
from .tools.remote_gpu import (
    remote_bash,
    create_remote_text_editor,
    remote_download,
)
from .tools.llm_proxy import (
    llm_proxy_local,
    llm_proxy_remote,
)
from .files import get_workspace_dir, WorkspaceDirectory


def run(
    host: str = "0.0.0.0",
    port: int = 5050,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    workspace: Optional[str] = None,
    transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http",
) -> None:
    load_dotenv()
    if workspace:
        WorkspaceDirectory.set_dir(Path(workspace))
    workspace_path = get_workspace_dir()
    workspace_path.mkdir(parents=True, exist_ok=True)

    server = FastMCP(
        "MLE kit MCP",
        stateless_http=True,
        streamable_http_path=streamable_http_path,
        mount_path=mount_path,
    )

    remote_text_editor = create_remote_text_editor(text_editor)

    server.add_tool(bash)
    server.add_tool(text_editor)
    server.add_tool(remote_bash)
    server.add_tool(remote_text_editor)
    server.add_tool(remote_download)
    if os.getenv("OPENROUTER_API_KEY"):
        server.add_tool(llm_proxy_local)
        server.add_tool(llm_proxy_remote)

    server.settings.port = port
    server.settings.host = host
    server.run(transport=transport)


if __name__ == "__main__":
    fire.Fire(run)
