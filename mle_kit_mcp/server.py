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


server = FastMCP("MLE kit MCP", stateless_http=True)

server.add_tool(bash)
server.add_tool(text_editor)
server.add_tool(remote_bash)
server.add_tool(create_remote_text_editor)
server.add_tool(remote_download)

http_app = server.streamable_http_app()


def run(host: str = "0.0.0.0", port: int = 5050) -> None:
    uvicorn.run(http_app, host=host, port=port)


if __name__ == "__main__":
    fire.Fire(run)
