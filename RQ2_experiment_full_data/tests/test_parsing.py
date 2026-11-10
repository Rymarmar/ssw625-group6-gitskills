"""Regression tests for professor-identified RQ2 Markdown parsing defects.

Run from the RQ2_experiment folder:
    python3 -m unittest discover -s tests -v
No database or external Python packages are needed to run these tests.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rq2_parsing import heading_count, remove_code_blocks, repeated_content_analysis


PARAGRAPH = (
    "This instruction block has enough words and characters to be counted as a "
    "repeated skill instruction, and it will occur twice in the test."
)


def fake_token_count(text):
    """Deterministic stand-in; production uses cl100k_base via tiktoken."""
    return len(text.split())


class HeadingFenceRegressionTests(unittest.TestCase):
    def test_shorter_backtick_fence_must_not_close(self):
        document = "# Visible one\n````python\n```\n# Hidden\n````\n# Visible two\n"
        self.assertEqual(heading_count(document), 2)

    def test_shorter_tilde_fence_must_not_close(self):
        document = "~~~ ~\n# Inside\n~~~~\n# Outside\n"
        self.assertEqual(heading_count(document), 1)

    def test_different_fence_character_does_not_close(self):
        document = "````\n~~~~\n# Hidden\n````\n# Visible\n"
        self.assertEqual(heading_count(document), 1)

    def test_closer_with_trailing_text_is_invalid(self):
        document = "````\n```` not a close\n# Hidden\n````  \n# Visible\n"
        self.assertEqual(heading_count(document), 1)

    def test_longer_valid_closer_and_indent(self):
        document = "   ```python\n# Hidden\n   ````\n   # Visible\n"
        self.assertEqual(heading_count(document), 1)

    def test_no_fence_counts_normal_headings(self):
        self.assertEqual(heading_count("# A\n## B\n    # Not heading\n"), 2)

    def test_same_rule_for_code_block_removal(self):
        document = "before\n\n````python\n```\nkeep hidden\n````\n\nafter"
        stripped = remove_code_blocks(document)
        self.assertNotIn("keep hidden", stripped)
        self.assertIn("before", stripped)
        self.assertIn("after", stripped)


class RepetitionNewlineRegressionTests(unittest.TestCase):
    def _check_newlines(self, separator):
        body = PARAGRAPH + separator + PARAGRAPH
        return repeated_content_analysis(body, fake_token_count)

    def test_lf_blank_lines_detect_duplicate(self):
        result = self._check_newlines("\n\n")
        self.assertEqual(result, (1, fake_token_count(PARAGRAPH)))

    def test_crlf_blank_lines_match_lf(self):
        self.assertEqual(self._check_newlines("\r\n\r\n"), self._check_newlines("\n\n"))

    def test_old_mac_cr_blank_lines_match_lf(self):
        self.assertEqual(self._check_newlines("\r\r"), self._check_newlines("\n\n"))

    def test_crlf_with_spaced_blank_line(self):
        self.assertEqual(self._check_newlines("\r\n  \r\n"), self._check_newlines("\n\n"))

    def test_repetition_inside_fence_is_not_counted(self):
        body = "````\n" + PARAGRAPH + "\n\n" + PARAGRAPH + "\n````"
        self.assertEqual(repeated_content_analysis(body, fake_token_count), (0, 0))

    def test_subthreshold_blocks_are_not_counted(self):
        self.assertEqual(repeated_content_analysis("short\n\nshort", fake_token_count), (0, 0))

    def test_third_occurrence_counts_twice(self):
        body = "\n\n".join([PARAGRAPH] * 3)
        self.assertEqual(repeated_content_analysis(body, fake_token_count), (2, 2 * fake_token_count(PARAGRAPH)))


if __name__ == "__main__":
    unittest.main()
