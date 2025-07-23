# MLE KIT MCP

A collection of MCP tools related to the experiments on remote gpu:
- Bash and remote bash
- Text editor and remote text editor 
- Remote download


Run the mcp server:
```
uv run python -m mle_kit_mcp --host 127.0.0.1 --port 5056 --workspace workdir
```

Claude Desktop config:
```
{
  "mcpServers": {
      "mle_kit": {"url": "http://127.0.0.1:5056/mcp", "transport": "streamable-http"}
  }
}
```