from pathlib import Path

DIR_PATH = Path(__file__).parent
ROOT_PATH = DIR_PATH.parent

WORKSPACE_DIR_PATH: Path = ROOT_PATH / "workdir"


def set_workspace_dir(path: Path) -> None:
    global WORKSPACE_DIR_PATH
    path.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR_PATH = path
