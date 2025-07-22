import pytest
from pathlib import Path
from mle_kit_mcp.files import set_workspace_dir, WORKSPACE_DIR_PATH
import tempfile
import shutil

@pytest.fixture(autouse=True)
def setup_workspace():
    temp_dir = Path(tempfile.mkdtemp())
    set_workspace_dir(temp_dir)
    yield
    shutil.rmtree(temp_dir)