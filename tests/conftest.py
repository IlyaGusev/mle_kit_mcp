import os
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(autouse=True)
def setup_workspace():
    temp_dir = Path(tempfile.mkdtemp())
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["WORKSPACE_DIR"] = str(temp_dir)
    yield
    shutil.rmtree(temp_dir)
