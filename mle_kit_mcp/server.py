from typing import Optional, Literal

import fire  # type: ignore
from mcp.server.fastmcp import FastMCP
from mle_kit_mcp.settings import settings

from mle_kit_mcp.tools.bash import bash
from mle_kit_mcp.tools.text_editor import text_editor
from mle_kit_mcp.tools.remote_gpu import (
    remote_bash,
    create_remote_text_editor,
    remote_download,
)
from mle_kit_mcp.tools.llm_proxy import (
    llm_proxy_local,
    llm_proxy_remote,
)
from mle_kit_mcp.tools.file_system import use_glob, use_grep
from mle_kit_mcp.files import get_workspace_dir


def run(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http",
) -> None:
    assert (
        settings.WORKSPACE_DIR is not None
    ), "WORKSPACE_DIR is not set. Please set it with the environment variable."
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
    server.add_tool(use_glob)
    server.add_tool(use_grep)
    if settings.OPENROUTER_API_KEY:
        server.add_tool(llm_proxy_local)
        server.add_tool(llm_proxy_remote)

    if port is None:
        port = int(settings.PORT)
    server.settings.port = port
    server.settings.host = host
    server.run(transport=transport)


if __name__ == "__main__":
    fire.Fire(run)
