from pathlib import Path

from mle_kit_mcp.settings import settings


def get_workspace_dir() -> Path:
    assert settings.WORKSPACE_DIR is not None, "Please set the WORKSPACE_DIR environment variable"
    directory = Path(settings.WORKSPACE_DIR)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_host_workspace_dir() -> Path:
    if settings.HOST_WORKSPACE_DIR is not None:
        directory = Path(settings.HOST_WORKSPACE_DIR)
    else:
        directory = Path(settings.WORKSPACE_DIR)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory
