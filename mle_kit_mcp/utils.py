import random
import socket
from typing import Optional


def truncate_content(
    content: str,
    max_length: int,
    prefix_only: bool = False,
    suffix_only: bool = False,
    target_line: Optional[int] = None,
) -> str:
    assert int(prefix_only) + int(suffix_only) + int(target_line is not None) <= 1
    disclaimer = (
        f"\n\n..._This content has been truncated to stay below {max_length} characters_...\n\n"
    )
    half_length = max_length // 2
    if len(content) <= max_length:
        return content

    if prefix_only:
        prefix = content[:max_length]
        return prefix + disclaimer

    elif suffix_only:
        suffix = content[-max_length:]
        return disclaimer + suffix

    elif target_line:
        line_start_pos = 0
        next_pos = content.find("\n") + 1
        line_end_pos = next_pos
        for _ in range(target_line):
            next_pos = content.find("\n", next_pos) + 1
            line_start_pos = line_end_pos
            line_end_pos = next_pos
        assert line_end_pos >= line_start_pos
        length = line_end_pos - line_start_pos
        remaining_length = max(0, max_length - length)
        half_length = remaining_length // 2
        start = max(0, line_start_pos - half_length)
        end = min(len(content), line_end_pos + half_length)
        final_content = content[start:end]
        if start == 0:
            return final_content + disclaimer
        elif end == len(content):
            return disclaimer + final_content
        return disclaimer + content[start:end] + disclaimer

    prefix = content[:half_length]
    suffix = content[-half_length:]
    return prefix + disclaimer + suffix


def find_free_port() -> Optional[int]:
    ports = list(range(5000, 6001))
    random.shuffle(ports)
    for port in ports:
        try:
            with socket.socket() as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return None
