import os
import time
import subprocess
import atexit
import signal
import inspect
import functools
from pathlib import Path
from typing import List, Optional, Any, Callable
from dataclasses import dataclass

from dotenv import load_dotenv
from vastai_sdk import VastAI  # type: ignore

from mle_kit_mcp.files import get_workspace_dir

BASE_IMAGE = "phoenix120/holosophos_mle"
DEFAULT_GPU_TYPE = "RTX_3090"
GLOBAL_TIMEOUT = 43200
VAST_AI_GREETING = """Welcome to vast.ai. If authentication fails, try again after a few seconds, and double check your ssh key.
Have fun!"""


@dataclass
class InstanceInfo:
    instance_id: int
    ip: str = ""
    port: int = 0
    username: str = ""
    ssh_key_path: str = ""
    gpu_name: str = ""
    start_time: int = 0


_sdk: Optional[VastAI] = None
_instance_info: Optional[InstanceInfo] = None


def get_sdk() -> VastAI:
    global _sdk
    if not _sdk:
        _sdk = VastAI(api_key=os.getenv("VAST_AI_KEY"))
    return _sdk


def get_instance() -> InstanceInfo:
    load_dotenv()
    signal.alarm(GLOBAL_TIMEOUT)
    global _instance_info
    if not _instance_info:
        _instance_info = launch_instance(get_sdk(), DEFAULT_GPU_TYPE)

    if _instance_info:
        send_scripts()

    assert _instance_info, "Failed to connect to a remote instance! Try again"
    return _instance_info


def cleanup_instance(signum: Optional[Any] = None, frame: Optional[Any] = None) -> None:
    global _instance_info
    signal.alarm(0)
    if _instance_info and _sdk:
        print("Cleaning up...")
        try:
            _sdk.destroy_instance(id=_instance_info.instance_id)
            _instance_info = None
        except Exception:
            pass
    if signum == signal.SIGINT:
        raise KeyboardInterrupt()


atexit.register(cleanup_instance)
signal.signal(signal.SIGINT, cleanup_instance)
signal.signal(signal.SIGTERM, cleanup_instance)
signal.signal(signal.SIGALRM, cleanup_instance)


def wait_for_instance(vast_sdk: VastAI, instance_id: str, max_wait_time: int = 300) -> bool:
    print(f"Waiting for instance {instance_id} to be ready...")
    start_wait = int(time.time())
    instance_ready = False
    while time.time() - start_wait < max_wait_time:
        instance_details = vast_sdk.show_instance(id=instance_id)
        if (
            isinstance(instance_details, dict)
            and instance_details.get("actual_status") == "running"
        ):
            instance_ready = True
            print(f"Instance {instance_id} is running and ready.")
            break
        print(f"Instance {instance_id} not ready yet. Waiting...")
        time.sleep(15)
    return instance_ready


def get_offers(vast_sdk: VastAI, gpu_name: str) -> List[int]:
    params = [
        f"gpu_name={gpu_name}",
        "cuda_vers>=12.1",
        "num_gpus=1",
        "reliability > 0.99",
        "inet_up > 400",
        "inet_down > 400",
        "verified=True",
        "rentable=True",
        "disk_space > 100",
    ]
    query = "  ".join(params)
    order = "score-"
    offers = vast_sdk.search_offers(query=query, order=order)
    assert offers
    return [int(o["id"]) for o in offers]


def run_command(
    instance: InstanceInfo, command: str, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "ssh",
        "-i",
        instance.ssh_key_path,
        "-p",
        str(instance.port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
        "-o",
        "TCPKeepAlive=yes",
        f"{instance.username}@{instance.ip}",
        command,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            result.stdout = result.stdout.replace(VAST_AI_GREETING, "").strip()
        if result.stderr:
            result.stderr = result.stderr.replace(VAST_AI_GREETING, "").strip()
    except subprocess.TimeoutExpired as e:
        output = None
        if e.stdout:
            output_message = e.stdout.decode("utf-8").strip()
            output_message = output_message.replace(VAST_AI_GREETING, "").strip()
            if output_message:
                output = output_message
        error = (
            f"Command timed out after {timeout} seconds: {command};\n"
            f"You can increase the timeout by changing the parameter of the tool call.\n"
        )
        if e.stderr:
            error_message = e.stderr.decode("utf-8").strip()
            error_message = error_message.replace(VAST_AI_GREETING, "").strip()
            if error_message:
                error += f"Original stderr: {error_message}"
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=-9,
            stdout=output,
            stderr=error,
        )
    return result


def recieve_rsync(
    info: InstanceInfo, remote_path: str, local_path: str
) -> subprocess.CompletedProcess[str]:
    rsync_cmd = [
        "rsync",
        "-avz",
        "-e",
        f"ssh -i {info.ssh_key_path} -p {info.port} -o StrictHostKeyChecking=no",
        f"{info.username}@{info.ip}:{remote_path}",
        local_path,
    ]

    result = subprocess.run(rsync_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_output = (
            f"Error syncing directory: {remote_path} to {local_path}. Error: {result.stderr}"
        )
        raise Exception(error_output)
    return result


def send_rsync(
    info: InstanceInfo, local_path: str, remote_path: str
) -> subprocess.CompletedProcess[str]:
    rsync_cmd = [
        "rsync",
        "-avz",
        "-e",
        f"ssh -i {info.ssh_key_path} -p {info.port} -o StrictHostKeyChecking=no",
        local_path,
        f"{info.username}@{info.ip}:{remote_path}",
    ]

    result = subprocess.run(rsync_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_output = (
            f"Error syncing directory: {local_path} to {remote_path}. Error: {result.stderr}"
        )
        raise Exception(error_output)
    return result


def launch_instance(vast_sdk: VastAI, gpu_name: str) -> Optional[InstanceInfo]:
    print(f"Selecting instance with {gpu_name}...")
    offer_ids = get_offers(vast_sdk, gpu_name)

    instance_id = None
    info: Optional[InstanceInfo] = None

    for offer_id in offer_ids:
        print(f"Launching offer {offer_id}...")
        instance = vast_sdk.create_instance(id=offer_id, image=BASE_IMAGE, disk=300.0)
        if not instance["success"]:
            continue
        instance_id = instance["new_contract"]
        assert instance_id
        global _instance_info
        _instance_info = InstanceInfo(instance_id=instance_id)
        print(f"Instance launched successfully. ID: {instance_id}")
        is_ready = wait_for_instance(vast_sdk, instance_id)
        if not is_ready:
            print(f"Destroying instance {instance_id}...")
            vast_sdk.destroy_instance(id=instance_id)
            continue

        print("Attaching SSH key...")
        ssh_key_path = Path("~/.ssh/id_rsa").expanduser()
        if not ssh_key_path.exists():
            print(f"Generating SSH key at {ssh_key_path}...")
            os.makedirs(ssh_key_path.parent, exist_ok=True)
            subprocess.run(
                [
                    "ssh-keygen",
                    "-t",
                    "rsa",
                    "-b",
                    "4096",
                    "-f",
                    str(ssh_key_path),
                    "-N",
                    "",
                ]
            )

        public_key = Path(f"{ssh_key_path}.pub").read_text().strip()
        vast_sdk.attach_ssh(instance_id=instance_id, ssh_key=public_key)
        instance_details = vast_sdk.show_instance(id=instance_id)

        info = InstanceInfo(
            instance_id=instance_details.get("id"),
            ip=instance_details.get("ssh_host"),
            port=instance_details.get("ssh_port"),
            username="root",
            ssh_key_path=str(ssh_key_path),
            gpu_name=instance_details.get("gpu_name"),
            start_time=int(time.time()),
        )

        print(info)
        print(f"Checking SSH connection to {info.ip}:{info.port}...")
        max_attempts = 10
        is_okay = False
        for attempt in range(max_attempts):
            result = run_command(info, "echo 'SSH connection successful'")
            if result.returncode != 0:
                print(f"Waiting for SSH... {result.stderr}\n(Attempt {attempt+1}/{max_attempts})")
                time.sleep(30)
                continue
            if "SSH connection successful" in result.stdout:
                print("SSH connection established successfully!")
                is_okay = True
                break
            print(f"Waiting for SSH... (Attempt {attempt+1}/{max_attempts})")
            time.sleep(30)

        if not is_okay:
            print(f"Destroying instance {instance_id}...")
            vast_sdk.destroy_instance(id=instance_id)
            continue

        break

    return info


def send_scripts() -> None:
    assert _instance_info
    for name in os.listdir(get_workspace_dir()):
        if name.endswith(".py"):
            send_rsync(_instance_info, f"{get_workspace_dir()}/{name}", "/root")


def remote_bash(command: str, timeout: int = 60) -> str:
    """
    Run commands in a bash shell on a remote machine with GPU cards.
    When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    You don't have access to the internet via this tool.
    You do have access to a mirror of common linux and python packages via apt and pip.
    State is persistent across command calls and discussions with the user.
    To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    Please avoid commands that may produce a very large amount of output.
    Do not run commands in the background.
    You can use python3.

    Args:
        command: The bash command to run.
        timeout: Timeout for the command execution. 60 seconds by default. Set a higher value for heavy jobs.
    """

    instance = get_instance()
    assert instance
    assert timeout
    result = run_command(instance, command, timeout=timeout)
    output = ("Command stdout: " + result.stdout + "\n") if result.stdout else ""
    output += ("Command stderr: " + result.stderr) if result.stderr else ""
    if not output.strip():
        output = "No output from the command"
    return output


def remote_download(file_path: str) -> str:
    """
    Copies a file from a remote machine to the local work directory.
    Use it to download final artefacts of the runs.
    Args:
        file_path: Path to the file on a remote machine.
    """
    instance = get_instance()
    assert instance
    recieve_rsync(instance, f"/root/{file_path}", f"{get_workspace_dir()}")
    return f"File '{file_path}' downloaded!"


def create_remote_text_editor(
    text_editor_func: Callable[..., str],
) -> Callable[..., str]:
    @functools.wraps(text_editor_func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        instance = get_instance()

        args_dict = {k: v for k, v in kwargs.items()}
        if args:
            args_dict.update(dict(zip(("command", "path"), args)))
        path = args_dict["path"]
        command = args_dict["command"]

        if command != "write":
            dir_path = "/".join(path.split("/")[:-1])
            if dir_path:
                recieve_rsync(instance, f"/root/{path}", f"{get_workspace_dir()}/{dir_path}")
            recieve_rsync(instance, f"/root/{path}", f"{get_workspace_dir()}")

        result: str = text_editor_func(*args, **kwargs)

        if command != "view":
            dir_path = "/".join(path.split("/")[:-1])
            if dir_path:
                send_rsync(instance, f"{get_workspace_dir()}/{path}", f"/root/{dir_path}")
            send_rsync(instance, f"{get_workspace_dir()}/{path}", "/root")

        return result

    orig_sig = inspect.signature(text_editor_func)
    wrapper.__signature__ = orig_sig  # type: ignore
    if text_editor_func.__doc__:
        orig_doc = text_editor_func.__doc__
        new_doc = orig_doc.replace("text_editor", "remote_text_editor")
        wrapper.__doc__ = "Executes on a remote machine with GPU.\n" + new_doc
        wrapper.__name__ = "remote_text_editor"
    return wrapper
