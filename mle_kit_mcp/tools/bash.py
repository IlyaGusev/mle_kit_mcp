import atexit
import signal
from typing import Optional, Any

from docker import from_env as docker_from_env  # type: ignore
from docker import DockerClient
from docker.models.containers import Container  # type: ignore

from mle_kit_mcp.files import get_workspace_dir


_container = None
_client = None

BASE_IMAGE = "python:3.12-slim"
DOCKER_WORKSPACE_DIR_PATH = "/workdir"


def get_docker_client() -> DockerClient:
    global _client
    if not _client:
        _client = docker_from_env()
    return _client


def create_container() -> Container:
    client = get_docker_client()
    container = client.containers.run(
        BASE_IMAGE,
        "tail -f /dev/null",
        detach=True,
        remove=True,
        tty=True,
        stdin_open=True,
        volumes={
            get_workspace_dir(): {
                "bind": DOCKER_WORKSPACE_DIR_PATH,
                "mode": "rw",
            }
        },
        working_dir=DOCKER_WORKSPACE_DIR_PATH,
    )
    return container


def get_container() -> Container:
    global _container
    if not _container:
        _container = create_container()
    return _container


def cleanup_container(signum: Optional[Any] = None, frame: Optional[Any] = None) -> None:
    global _container
    if _container:
        try:
            _container.remove(force=True)
            _container = None
        except Exception:
            pass
    if signum == signal.SIGINT:
        raise KeyboardInterrupt()


atexit.register(cleanup_container)
signal.signal(signal.SIGINT, cleanup_container)
signal.signal(signal.SIGTERM, cleanup_container)


def bash(command: str, cwd: Optional[str] = None) -> str:
    """
    Run commands in a bash shell.
    When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    You don't have access to the internet via this tool.
    You do have access to a mirror of common linux and python packages via apt and pip.
    State is persistent across command calls and discussions with the user.
    To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    Please avoid commands that may produce a very large amount of output.
    Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.

    Args:
        command: The bash command to run.
        cwd: The working directory to run the command in. Relative to the workspace directory.
    """

    container = get_container()
    workdir = DOCKER_WORKSPACE_DIR_PATH
    if cwd:
        workdir = DOCKER_WORKSPACE_DIR_PATH + "/" + cwd
    result = container.exec_run(
        ["bash", "-c", command],
        workdir=workdir,
        stdout=True,
        stderr=True,
    )
    output: str = result.output.decode("utf-8").strip()
    return output
