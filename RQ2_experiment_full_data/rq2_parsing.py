"""Shared RQ2 Markdown and repetition parsing functions.

These functions are used by both the Phase 2-compatible scripts and notebooks.
They do not load the dataset, so they can be tested independently.
"""

import re


def _opening_fence(line):
    """Return (marker character, length) for a Markdown fenced-code opener."""
    match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
    if not match:
        return None

    marker, info = match.groups()
    # Markdown backtick-fence info strings must not contain backticks.
    if marker[0] == "`" and "`" in info:
        return None
    return marker[0], len(marker)


def _closing_fence(line, marker_char, opening_length):
    """Only the same marker, at least as long, with whitespace afterward closes."""
    return bool(
        re.fullmatch(
            r" {0,3}" + re.escape(marker_char)
            + "{" + str(opening_length) + r",}[ \t]*",
            line,
        )
    )


def heading_count(content):
    """Count ATX Markdown headings outside fenced code blocks."""
    count = 0
    fence = None

    for line in (content or "").splitlines():
        if fence is not None:
            if _closing_fence(line, fence[0], fence[1]):
                fence = None
            continue

        opener = _opening_fence(line)
        if opener is not None:
            fence = opener
            continue

        if re.match(r"^ {0,3}#{1,6}[ \t]+\S", line):
            count += 1

    return count


def remove_code_blocks(text):
    """Omit fenced blocks, inserting paragraph boundaries for repetition checks."""
    result = []
    fence = None

    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if fence is None:
            opener = _opening_fence(stripped)
            if opener is not None:
                fence = opener
                result.append("\n\n")
            else:
                result.append(line)
        elif _closing_fence(stripped, fence[0], fence[1]):
            fence = None
            result.append("\n\n")

    return "".join(result)


def repeated_content_analysis(body, count_tokens, min_block_chars=80, min_block_words=10):
    """Count repeat occurrences after first match, and their token totals.

    Normalize CRLF and CR line endings BEFORE segmenting paragraphs.
    Tokens are measured with the caller's original token-counting function.
    """
    normalized_body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    text = remove_code_blocks(normalized_body)
    blocks = re.split(r"\n[ \t]*\n+", text)

    seen = set()
    repeated_blocks = 0
    repeated_tokens = 0

    for block in blocks:
        block = block.strip()
        normalized = " ".join(block.split()).casefold()
        if len(normalized) < min_block_chars:
            continue
        if len(normalized.split()) < min_block_words:
            continue
        if normalized in seen:
            repeated_blocks += 1
            repeated_tokens += count_tokens(block)
        else:
            seen.add(normalized)

    return repeated_blocks, repeated_tokens
