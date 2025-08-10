from mle_kit_mcp.utils import truncate_content

DOCUMENT = """First line
Second line here
Third line is the target
Fourth line appears
Last line of text"""


def test_truncate_content_centered() -> None:
    result = truncate_content(DOCUMENT, max_length=40, target_line=2)
    lines = DOCUMENT.splitlines()
    parts = result.split("\n\n")
    assert 39 <= len(parts[2]) <= 41
    assert parts[2] in DOCUMENT
    assert lines[2] in result


def test_truncate_content_not_applied() -> None:
    result = truncate_content(DOCUMENT, max_length=500)
    assert result == DOCUMENT


def test_truncate_content_prefix() -> None:
    result = truncate_content(DOCUMENT, max_length=40, prefix_only=True)
    parts = result.split("\n\n")
    assert DOCUMENT.startswith(parts[0])
    assert len(parts[0]) == 40


def test_truncate_content_suffix() -> None:
    result = truncate_content(DOCUMENT, max_length=40, suffix_only=True)
    parts = result.split("\n\n")
    assert DOCUMENT.endswith(parts[2])
    assert len(parts[2]) == 40
