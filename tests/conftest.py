import pytest
from pathlib import Path
import tempfile
import shutil

from mle_kit_mcp.settings import settings


@pytest.fixture(autouse=True, scope="session")
def setup_workspace():
    temp_dir = Path(tempfile.mkdtemp())
    temp_dir.mkdir(parents=True, exist_ok=True)
    settings.WORKSPACE_DIR = str(temp_dir)
    yield
    shutil.rmtree(temp_dir, ignore_errors=True)
