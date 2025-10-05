from pathlib import Path

from mle_kit_mcp.settings import settings


def get_workspace_dir() -> Path:
    assert settings.WORKSPACE_DIR is not None, "Please set the WORKSPACE_DIR environment variable"
    directory = Path(settings.WORKSPACE_DIR)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_host_workspace_dir() -> Path:
    directory_str = settings.HOST_WORKSPACE_DIR or settings.WORKSPACE_DIR
    assert (
        directory_str is not None
    ), "Please set the WORKSPACE_DIR or HOST_WORKSPACE_DIR environment variable"
    directory = Path(directory_str)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory
