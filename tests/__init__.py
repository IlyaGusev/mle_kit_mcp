from pathlib import Path
from mle_kit_mcp.files import set_workspace_dir

set_workspace_dir(Path(__file__).parent.parent / "workdir")