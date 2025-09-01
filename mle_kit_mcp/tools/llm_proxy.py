import os
import json
import time
import random
from pathlib import Path

from dotenv import load_dotenv

from mle_kit_mcp.tools.bash import get_container
from mle_kit_mcp.files import get_workspace_dir

from mle_kit_mcp.tools.remote_gpu import (
    get_instance as _remote_get_instance,
    run_command as _remote_run_command,
    send_rsync as _remote_send_rsync,
)

INPUT_SCRIPT_FILE_NAME = "llm_proxy.py"
OUTPUT_SCRIPT_FILE_NAME = "llm_proxy.py"
DEPENDENCIES = "fastapi uvicorn httpx openai fire"
START_TIMEOUT = 30


def _write_proxy_script(script_path: Path) -> None:
    source_script_path = Path(__file__).parent.parent / INPUT_SCRIPT_FILE_NAME
    script = source_script_path.read_text()
    script_path.write_text(script)


def llm_proxy_local() -> str:
    """
    Start a lightweight OpenRouter proxy inside the same Docker container used by the "bash" tool.

    Returns a JSON string with url and scope.
    The url is reachable from inside the "bash" container as localhost.
    It runs a standard OpenAI compatible server, so you can use it with any OpenAI compatible client.
    You can use all models available on OpenRouter, for instance:
    - openai/gpt-5-mini
    - google/gemini-2.5-pro
    - anthropic/claude-sonnet-4

    Args:
        port: Optional fixed port to bind inside the container. Random if omitted.
    """

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "Set OPENROUTER_API_KEY in the environment before starting the proxy."

    _write_proxy_script(get_workspace_dir() / OUTPUT_SCRIPT_FILE_NAME)

    container = get_container()
    dependencies_cmd = f"python -m pip install --quiet --no-input {DEPENDENCIES}"
    container.exec_run(["bash", "-lc", dependencies_cmd])

    chosen_port = random.randint(5000, 6000)
    launch_cmd = (
        f"OPENROUTER_API_KEY='{api_key}' "
        f"nohup python {OUTPUT_SCRIPT_FILE_NAME} "
        f"--host 127.0.0.1 --port {chosen_port} "
        f"> llm_proxy.log 2>&1 "
        f"& echo $! > llm_proxy.pid"
    )
    container.exec_run(["bash", "-lc", launch_cmd])

    health_cmd = f'import httpx; print(httpx.get("http://127.0.0.1:{chosen_port}/health").json())'
    start_time = time.time()
    while time.time() - start_time < START_TIMEOUT:
        result = container.exec_run(["python", "-c", health_cmd])
        if result.exit_code == 0 and "ok" in result.output.decode("utf-8").strip():
            break
        time.sleep(1)
    else:
        raise Exception("Failed to start the proxy")

    return json.dumps(
        {
            "url": f"http://127.0.0.1:{chosen_port}/v1/chat/completions",
            "scope": "bash-container",
        }
    )


def llm_proxy_remote() -> str:
    """
    Start a lightweight OpenRouter proxy on the remote GPU machine.

    Returns a JSON string with url and scope.
    The url is reachable from inside the remote machine as localhost.
    It runs a standard OpenAI compatible server, so you can use it with any OpenAI compatible client.
    You can use all models available on OpenRouter, for instance:
    - openai/gpt-5-mini
    - google/gemini-2.5-pro
    - anthropic/claude-sonnet-4
    """

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "Set OPENROUTER_API_KEY in the environment before starting the proxy."

    instance = _remote_get_instance()
    script_path = get_workspace_dir() / OUTPUT_SCRIPT_FILE_NAME
    _write_proxy_script(script_path)
    _remote_send_rsync(instance, f"{script_path}", "/root")

    chosen_port = random.randint(5000, 6000)
    dependencies_cmd = f"python3 -m pip install -q --no-input {DEPENDENCIES}"
    _remote_run_command(instance, dependencies_cmd, timeout=300)

    launch_cmd = (
        f"OPENROUTER_API_KEY='{api_key}' "
        f"nohup python {OUTPUT_SCRIPT_FILE_NAME} "
        f"--host 127.0.0.1 --port {chosen_port} "
        f"> openrouter_proxy.log 2>&1 "
        f"& echo $! > openrouter_proxy.pid"
    )
    _remote_run_command(instance, launch_cmd, timeout=60)

    health_cmd = f'import httpx; print(httpx.get("http://127.0.0.1:{chosen_port}/health").json())'
    start_time = time.time()
    while time.time() - start_time < START_TIMEOUT:
        result = _remote_run_command(instance, f"python -c '{health_cmd}'", timeout=10)
        if result.returncode == 0 and "ok" in result.stdout.strip():
            break
        time.sleep(1)
    else:
        raise Exception("Failed to start the proxy")

    return json.dumps(
        {
            "url": f"http://127.0.0.1:{chosen_port}/v1/chat/completions",
            "scope": "remote-gpu",
        }
    )
