import fire  # type: ignore
import uvicorn
from mcp.server.fastmcp import FastMCP

#from .tools.arxiv_search import arxiv_search

server = FastMCP("MLE kit MCP", stateless_http=True)

#server.add_tool(arxiv_search)

http_app = server.streamable_http_app()


def run(host: str = "0.0.0.0", port: int = 5050) -> None:
    uvicorn.run(http_app, host=host, port=port)


if __name__ == "__main__":
    fire.Fire(run)
