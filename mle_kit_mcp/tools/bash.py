import atexit
import signal
import shlex
import os
from typing import Optional, Any, Union, Sequence

from docker import from_env as docker_from_env  # type: ignore
from docker import DockerClient
from docker.models.containers import Container  # type: ignore

from mle_kit_mcp.files import get_host_workspace_dir
from mle_kit_mcp.settings import settings


_container = None
_client = None

DOCKER_WORKSPACE_DIR_PATH = "/workdir"


def get_docker_client() -> DockerClient:
    global _client
    if not _client:
        _client = docker_from_env()
    return _client


def create_container() -> Container:
    client = get_docker_client()
    uid = os.getuid()
    gid = os.getgid()
    container = client.containers.run(
        settings.MLE_KIT_IMAGE,
        "tail -f /dev/null",
        detach=True,
        remove=True,
        tty=True,
        stdin_open=True,
        user=f"{uid}:{gid}",
        environment={
            "HOME": DOCKER_WORKSPACE_DIR_PATH,
            "XDG_CACHE_HOME": f"{DOCKER_WORKSPACE_DIR_PATH}/.cache",
        },
        volumes={
            str(get_host_workspace_dir()): {
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


def _run_bash_command(
    command: str,
    timeout: int = 60,
    cwd: Optional[str] = None,
    run_as_root: bool = False,
) -> str:
    assert timeout and timeout > 0, "Timeout must be set and greater than 0"
    container = get_container()
    workdir = DOCKER_WORKSPACE_DIR_PATH
    if cwd:
        workdir += "/" + cwd

    wrapped = f"bash -lc {shlex.quote(command)}"
    final_command = f"timeout --signal=TERM --kill-after=5s {int(timeout)}s {wrapped}"

    result = container.exec_run(
        ["bash", "-lc", final_command],
        workdir=workdir,
        stdout=True,
        stderr=True,
        demux=True,
        user="root" if run_as_root else None,
    )
    stdout_bytes, stderr_bytes = (
        result.output if isinstance(result.output, tuple) else (result.output, b"")
    )

    if result.exit_code in (124, 137):
        timeout_msg = (
            f"Command timed out after {int(timeout)} seconds: {command};\n"
            f"You can increase the timeout by changing the parameter of the tool call."
        )
        stderr_bytes = (stderr_bytes or b"") + timeout_msg.encode("utf-8")

    stdout_text = (stdout_bytes or b"").decode("utf-8", errors="replace").strip()
    stderr_text = (stderr_bytes or b"").decode("utf-8", errors="replace").strip()

    output_parts = []
    if stdout_text:
        output_parts.append("Command stdout: " + stdout_text)
    if stderr_text:
        output_parts.append("Command stderr: " + stderr_text)
    output = ("\n".join(output_parts)).strip()
    if not output:
        output = "No output from the command"
    return output


def bash(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 60,
) -> str:
    """
    Run commands in a bash shell.
    When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    You don't have access to the internet via this tool.
    You do have access to a mirror of common linux and python packages via apt and pip.
    State is persistent across command calls and discussions with the user.
    To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    Please avoid commands that may produce a very large amount of output.

    Args:
        command: The bash command to run.
        cwd: The working directory to run the command in. Relative to the workspace directory.
        timeout: Timeout for the command execution in seconds. Kills after this. 60 seconds by default.
    """
    return _run_bash_command(command=command, timeout=timeout, cwd=cwd, run_as_root=False)


def install_with_apt(
    packages: Union[str, Sequence[str]],
    update: bool = True,
    timeout: int = 600,
) -> str:
    """
    Install one or more apt packages inside the Docker container as the root user.

    Args:
        packages: A single package name or a sequence of package names.
        update: Whether to run 'apt-get update' before install. Defaults to True.
        timeout: Timeout for the entire apt operation in seconds. Defaults to 600.
    """

    if isinstance(packages, str):
        packages_str = packages.strip()
    else:
        packages_str = " ".join(shlex.quote(p) for p in packages)

    if not packages_str:
        return "No packages specified"

    apt_commands = []
    if update:
        apt_commands.append("apt-get update -y")
    apt_commands.append(
        f"DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {packages_str}"
    )
    command = " && ".join(apt_commands)
    return _run_bash_command(command=command, timeout=timeout, run_as_root=True)
