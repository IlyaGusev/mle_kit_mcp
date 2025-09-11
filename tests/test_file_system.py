
import shutil
import pytest

from mle_kit_mcp.tools import glob, bash, grep

rg_missing = shutil.which("rg") is None


def test_glob_base():
    bash("mkdir -p dummy_dir")
    bash("touch dummy.txt", cwd="dummy_dir")
    assert glob("**/*.txt") == ["dummy_dir/dummy.txt"]


@pytest.mark.skipif(rg_missing, reason="ripgrep (rg) is not installed")
def test_grep_files_with_matches_basic():
    bash("mkdir -p rg_dummy")
    bash("printf 'hello\\nworld\\n' > a.txt", cwd="rg_dummy")
    bash("printf 'print(\"Hello\")\\n' > b.py", cwd="rg_dummy")
    bash("printf 'bye\\n' > c.txt", cwd="rg_dummy")

    out = grep("hello", path="rg_dummy")
    assert "a.txt" in out
    assert "b.py" not in out


@pytest.mark.skipif(rg_missing, reason="ripgrep (rg) is not installed")
def test_grep_content_mode_with_context_and_insensitive():
    bash("mkdir -p rg_dummy2")
    bash("printf 'alpha\\nBravo\\ncharlie\\n' > notes.txt", cwd="rg_dummy2")
    bash("printf 'print(\"Hello\")\\n' > code.py", cwd="rg_dummy2")

    out = grep(
        "hello",
        path="rg_dummy2",
        output_mode="content",
        center_context=1,
        insensitive=True,
    )
    assert "code.py" in out
    assert ":" in out


@pytest.mark.skipif(rg_missing, reason="ripgrep (rg) is not installed")
def test_grep_count_mode_with_glob_and_head_limit():
    bash("mkdir -p rg_dummy3")
    bash("printf 'hello\\nworld\\n' > a.txt", cwd="rg_dummy3")
    bash("printf 'foo\\nbar\\n' > m.txt", cwd="rg_dummy3")

    out = grep(
        "o",
        path="rg_dummy3",
        output_mode="count",
        glob="*.txt",
        head_limit=1,
    )
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) <= 1
    assert ".txt:" in lines[0]


@pytest.mark.skipif(rg_missing, reason="ripgrep (rg) is not installed")
def test_grep_multiline_matching():
    bash("mkdir -p rg_dummy4")
    bash("printf 'foo\\nbar\\n' > multi.txt", cwd="rg_dummy4")

    out = grep(
        "foo.*bar",
        path="rg_dummy4",
        output_mode="content",
        multiline=True,
    )
    assert "multi.txt" in out
