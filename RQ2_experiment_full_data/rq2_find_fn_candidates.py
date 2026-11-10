import re
import duckdb
from pathlib import Path
from difflib import SequenceMatcher

DATA = "../data/artifacts/part-00000.parquet"
OUTPUT = Path("/tmp")
MAX_RESULTS = 5

def normalize(text):
    return re.sub(r"\s+", " ", text).strip()

def references(text):
    return set(re.findall(r"`[^`]+`|https?://[^\s)]+", text))

def paragraphs(content):
    body = content.replace("\r\n", "\n").replace("\r", "\n")

    # Exclude leading YAML front matter.
    body = re.sub(
        r"\A---[ \t]*\n.*?\n---[ \t]*(?:\n|$)",
        "",
        body,
        count=1,
        flags=re.DOTALL,
    )

    # For this candidate search, skip files with fenced code.
    if "```" in body or "~~~" in body:
        return []

    parts = re.split(r"\n\s*\n", body)
    result = []

    for part in parts:
        text = normalize(part)
        if (
            100 <= len(text) <= 1200
            and len(text.split()) >= 12
            and not text.startswith("|")
        ):
            result.append(text)

    return result[:50]

con = duckdb.connect()
cursor = con.execute(f"""
    SELECT file_sha, repo_full_name, path, content
    FROM read_parquet('{DATA}')
    WHERE dedup_primary = 1
      AND length(content) BETWEEN 800 AND 16000
    LIMIT 20000
""")

found = 0
checked = 0

while True:
    rows = cursor.fetchmany(250)
    if not rows:
        break

    for sha, repo, path, content in rows:
        checked += 1
        blocks = paragraphs(content)

        for i in range(len(blocks)):
            if found >= MAX_RESULTS:
                break

            for j in range(i + 1, len(blocks)):
                a, b = blocks[i], blocks[j]

                if a == b:
                    continue

                # Reject passages referring to different resources.
                if references(a) != references(b):
                    continue

                if min(len(a), len(b)) / max(len(a), len(b)) < 0.85:
                    continue

                score = SequenceMatcher(
                    None, a.lower(), b.lower(), autojunk=False
                ).ratio()

                if 0.88 <= score < 0.995:
                    found += 1
                    filename = OUTPUT / f"rq2_fn_candidate_{found}.md"
                    filename.write_text(content, encoding="utf-8")

                    print(f"\nCANDIDATE {found}")
                    print("Hash:", sha)
                    print("Repository:", repo)
                    print("Path:", path)
                    print("Similarity:", round(score, 3))
                    print("\nFIRST PASSAGE:\n", a[:600])
                    print("\nSECOND PASSAGE:\n", b[:600])
                    print("Saved to:", filename)
                    break

        if found >= MAX_RESULTS:
            break

    if found >= MAX_RESULTS:
        break

print(f"\nFiles checked: {checked}")
print(f"Candidates found: {found}")
