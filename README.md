# MLE kit MCP


[![PyPI](https://img.shields.io/pypi/v/mle-kit-mcp?label=PyPI%20package)](https://pypi.org/project/mle-kit-mcp/)
[![CI](https://github.com/IlyaGusev/mle_kit_mcp/actions/workflows/python.yml/badge.svg)](https://github.com/IlyaGusev/mle_kit_mcp/actions/workflows/python.yml)
[![License](https://img.shields.io/github/license/IlyaGusev/mle_kit_mcp)](LICENSE)


MCP server providing practical tools for ML engineering workflows, including local/remote bash, a text editor, file search, remote GPU helpers (via vast.ai), and an OpenRouter LLM proxy.

### Features
- **bash**: Run commands in an isolated Docker container mounted to your `WORKSPACE_DIR`.
- **text_editor**: View and edit files and directories in your workspace with undo support.
- **glob / grep**: Fast filename globbing and ripgrep-based content search.
- **remote_bash / remote_text_editor / remote_download**: Execute and edit on a remote GPU machine and sync files to/from it.
- **llm_proxy_local / llm_proxy_remote**: Launch an OpenAI-compatible proxy backed by OpenRouter locally (in the bash container) or on the remote GPU.

## Requirements
- Python 3.12+
- Docker daemon available (for `bash` tool)
- ripgrep (`rg`) installed on the host (for `grep` tool)
- `WORKSPACE_DIR` should be set with a path to working directory
- Optional (for remote GPU tools): a `VAST_AI_KEY` with billing set up on vast.ai
- Optional (for LLM proxy tools): an `OPENROUTER_API_KEY`

## Install
Using uv (recommended):
```bash
uv sync
```

Or standard pip install:
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .
```

## Run the MCP server
Set a workspace directory and start the server. The MCP endpoint is served at `/mcp`.

```bash 
WORKSPACE_DIR=/absolute/path/to/workdir uv run python -m mle_kit_mcp --port 5057
```

Defaults:
- `PORT` defaults to `5057` if `--port` is not provided
- `mount_path=/` and `streamable_http_path=/mcp`

### Claude Desktop config
```json
{
  "mcpServers": {
    "mle_kit": {
      "command": "python3",
      "args": [
        "-m",
        "mle_kit_mcp",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

## Tools overview
- **bash(command, cwd=None, timeout=60)**: Runs inside a `python:3.12-slim` container with your workspace bind-mounted at `/workdir`. State persists between calls. Timeouts return a helpful message.
- **text_editor(command, path, ...)**: Supports `view`, `write`, `append`, `insert`, `str_replace` (with optional `dry_run`), and `undo_edit`. Only relative paths under the workspace are allowed.
- **glob(pattern, path=None)**: Returns matching files under the workspace (optionally under `path`), sorted by modification time.
- **grep(pattern, path=None, glob=None, output_mode=..., ...)**: ripgrep wrapper. Install `rg` on the host to enable. Output modes: `files_with_matches`, `content`, `count`.
- **remote_bash(command, timeout=60)**: Runs commands on a remote vast.ai instance. Manages lifecycle unless you supply an existing instance (see env vars below).
- **remote_download(file_path)**: Copies a file from the remote (`/root/<file_path>`) to your workspace.
- **remote_text_editor(...)**: Same API as `text_editor`, but syncs the file(s) before and after edits to the remote.
- **llm_proxy_local() / llm_proxy_remote()**: Starts a small FastAPI OpenAI-compatible server backed by OpenRouter, returning a JSON string with `url` and `scope`.

## Configuration (env vars)
All variables can be placed in a local `.env` file or exported in your shell.

- `WORKSPACE_DIR` (required): Absolute path to your workspace directory.
- `PORT` (optional): Default server port (defaults to `5057`).

Remote GPU (vast.ai):
- `GPU_TYPE` (default: `RTX_3090`)
- `DISK_SPACE` (GB, default: `300`)
- `EXISTING_INSTANCE_ID` (optional): Use an existing vast.ai instance instead of creating a new one.
- `EXISTING_SSH_KEY` (optional): Path to an SSH private key to use with the existing instance.
- `VAST_AI_KEY` (optional but required to launch new instances)

OpenRouter proxy:
- `OPENROUTER_API_KEY` (optional but required for proxy tools)
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)

Notes:
- The remote GPU helper will generate an SSH key at `~/.ssh/id_rsa` if one is missing, and attach it to the instance.
- Creating/destroying instances may incur cost; be mindful of environment defaults.

## Development
Run tests:
```bash
make test
```

Lint / type-check / format:
```bash
make validate
```

## Docker
You can also build and run via the provided `Dockerfile`:
```bash
docker build -t mle_kit_mcp .
docker run --rm -p 5057:5057 \
  -e PORT=5057 \
  -e WORKSPACE_DIR=/workspace \
  -v "$PWD/workdir:/workspace" \
  mle_kit_mcp
```