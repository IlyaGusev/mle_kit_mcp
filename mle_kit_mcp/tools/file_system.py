from typing import List, Optional
from pathlib import Path
import subprocess

from mle_kit_mcp.files import get_workspace_dir


def glob(pattern: str, path: Optional[str] = None) -> List[str]:
    """
    - Fast file pattern matching tool that works with any codebase size
    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time
    - Use this tool when you need to find files by name patterns

    Args:
        pattern: The glob pattern to match files against, required.
        path: The directory to search in. If not specified, the current working directory will be used.
            IMPORTANT: Omit this field to use the default directory. DO NOT enter "undefined" or "null".
            Simply omit it for the default behavior.
            Must be a valid directory path if provided.

    Returns:
        A list of matching file paths.
    """
    full_path: Path = get_workspace_dir()
    if path is not None:
        full_path = get_workspace_dir() / path
    files = [p for p in full_path.glob(pattern)]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    resolved_files = [str(p.resolve()) for p in files]
    resolved_files = [f.replace(str(get_workspace_dir()) + "/", "") for f in resolved_files]
    return resolved_files


def grep(
    pattern: str,
    path: Optional[str] = None,
    glob: Optional[str] = None,
    output_mode: str = "files_with_matches",
    before_context: Optional[int] = None,
    after_context: Optional[int] = None,
    center_context: Optional[int] = None,
    insensitive: bool = False,
    type: Optional[str] = None,
    head_limit: Optional[int] = None,
    multiline: bool = False,
) -> str:
    r"""
    A powerful search tool built on ripgrep

    Usage:
    - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command.
    - The Grep tool has been optimized for correct permissions and access.
    - Supports full regex syntax (e.g., "log.*Error")
    - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter (e.g., "js", "py", "rust")
    - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths (default), "count" shows match counts
    - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\{\}` to find `interface{}` in Go code)
    - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \{[\s\S]*?field`, use `multiline: true`

    Args:
        pattern: The regular expression pattern to search for in file contents
        path: File or directory to search. Defaults to current working directory.
        glob: Glob pattern to filter files (e.g. "*.js", "*.{ts,tsx}")
        output_mode: The output mode to use. Possible values are "content", "files_with_matches", "count".
            "content" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit)
            "files_with_matches" shows file paths (supports head_limit)
            "count" shows match counts (supports head_limit).
            Defaults to "files_with_matches"
        before_context: Number of lines to show before each match (rg -B). Requires output_mode: "content", ignored otherwise.
        after_context: Number of lines to show after each match (rg -A). Requires output_mode: "content", ignored otherwise.
        center_context: Number of lines to show before and after each match (rg -C). Requires output_mode: "content", ignored otherwise.
        insensitive: Case insensitive search (rg -i). Defaults to False.
        type: File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types.
        head_limit: Limit output to first N lines/entries, equivalent to "| head -N". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). When unspecified, shows all results from ripgrep.
        multiline: Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false.

    Returns:
        A string with the search results.
    """
    assert pattern, "'pattern' must be a non-empty string"

    valid_output_modes = {"content", "files_with_matches", "count"}
    assert (
        output_mode in valid_output_modes
    ), f"Invalid output_mode: {output_mode}. Expected one of {sorted(valid_output_modes)}"

    if center_context is not None:
        assert (
            before_context is None and after_context is None
        ), "Use either 'center_context' or ('before_context'/'after_context'), not both"

    cmd: List[str] = [
        "rg",
        "--color=never",
        "--no-heading",
    ]

    if output_mode == "files_with_matches":
        cmd.append("-l")
    elif output_mode == "count":
        cmd.append("-c")
    else:
        cmd.append("-n")

    if insensitive:
        cmd.append("-i")

    if multiline:
        cmd.extend(["--multiline", "--multiline-dotall"])

    if type:
        cmd.extend(["--type", type])

    if glob:
        cmd.extend(["--glob", glob])

    if output_mode == "content":
        if center_context is not None:
            cmd.extend(["-C", str(center_context)])
        else:
            if before_context is not None:
                cmd.extend(["-B", str(before_context)])
            if after_context is not None:
                cmd.extend(["-A", str(after_context)])

    cmd.append("--")
    cmd.append(pattern)

    search_root: Path = get_workspace_dir()
    if path is not None:
        search_root = search_root / path
    cmd.append(str(search_root))

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "ripgrep (rg) not found. Please install ripgrep in the environment where this tool runs."

    stdout = (result.stdout or "").rstrip("\n")
    stderr = (result.stderr or "").strip()

    if head_limit is not None and head_limit >= 0 and stdout:
        stdout_lines = stdout.splitlines()
        stdout = "\n".join(stdout_lines[:head_limit])

    if result.returncode not in (0, 1) and stderr:
        return stderr

    return stdout
