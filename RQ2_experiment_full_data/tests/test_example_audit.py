"""Unit tests for audit-only utilities. Run with unittest discovery."""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rq2_example_audit import audit_text, eligible_blocks, exact_repeat_pairs, normalize_block


def token_count(text):
    return len(text.split())


class ExampleAuditTests(unittest.TestCase):
    def test_duplicate_text_detected(self):
        paragraph = "This example paragraph repeats a valid instruction block with enough different words to pass the minimum threshold."
        result = audit_text(paragraph + "\n\n" + paragraph, token_count)
        self.assertEqual(result["exploratory_repeat_count"], 1)
        self.assertEqual(result["corrected_repeat_count"], 1)

    def test_fenced_repetition_not_counted(self):
        paragraph = "This example paragraph repeats a valid instruction block with enough different words to pass the minimum threshold."
        result = audit_text("```\n\n" + paragraph + "\n\n" + paragraph + "\n\n```", token_count)
        self.assertEqual(result["exploratory_repeat_count"], 1)
        self.assertEqual(result["corrected_repeat_count"], 0)

    def test_frontmatter_not_counted_as_first_match(self):
        paragraph = "description: this is a very long example of front matter with adequate words to qualify for the matching threshold"
        raw = "---\n" + paragraph + "\n---\n\n" + paragraph
        result = audit_text(raw, token_count)
        self.assertEqual(result["corrected_repeat_count"], 0)

    def test_crlf_normalized(self):
        paragraph = "This example paragraph repeats a valid instruction block with enough different words to pass the minimum threshold."
        result = audit_text(paragraph + "\r\n\r\n" + paragraph, token_count)
        self.assertEqual(result["corrected_repeat_count"], 1)


if __name__ == "__main__":
    unittest.main()
