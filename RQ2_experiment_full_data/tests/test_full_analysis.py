"""Full-data RQ2 tests. Integration test uses a tiny temporary Parquet dataset.

Unlike the production run, it downloads nothing and changes no real project data.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

HAS_DEPS = bool(importlib.util.find_spec("duckdb") and importlib.util.find_spec("tiktoken"))


@unittest.skipUnless(HAS_DEPS, "duckdb and tiktoken required for full-analysis tests")
class FullAnalysisTests(unittest.TestCase):
    def test_extract_body_preserves_phase2_rules(self):
        import rq2_full_analysis as mod
        self.assertEqual(mod.extract_body("---\nname: X\n---\n# Body\n"), "# Body\n")
        self.assertEqual(mod.extract_body("---\nno closing marker\n"), "---\nno closing marker\n")
        self.assertEqual(mod.extract_body("# Body"), "# Body")

    def test_structure_and_token_statistics(self):
        from rq2_full_analysis import StructureStats, TokenStats
        s = StructureStats()
        s.add(100, 2, 1)
        s.add(300, 4, None)
        self.assertEqual(s.median_chars, 200)
        self.assertEqual(s.median_headings, 3)
        self.assertEqual(s.refs_pct, 100.0)
        t = TokenStats()
        t.add(100, 0, 0)
        t.add(6000, 2, 150)
        self.assertEqual(t.median_tokens, 3050)
        self.assertEqual(t.repeated_blocks, 2)
        self.assertEqual(t.above_pct, 50.0)
        self.assertEqual(t.overhead_pct, 150 / 6100 * 100)

    def test_two_part_resume_and_full_report(self):
        import duckdb
        import rq2_full_analysis as mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = root / "data" / "artifacts"
            artifacts.mkdir(parents=True)
            out = root / "RQ2_experiment_full_data" / "rq2_outputs" / "full_dataset"
            work = out / "_work"
            metrics = work / "per_part_metrics"

            db = duckdb.connect(":memory:")
            db.execute("""CREATE TABLE items(
                repo_full_name VARCHAR, file_sha VARCHAR, dedup_primary INTEGER,
                content VARCHAR, body_chars BIGINT, has_references INTEGER)""")
            # The first content has two repo occurrences, across BOTH parts.
            db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", [
                "org/a", "sha-reused", 1,
                "# Visible one\n````python\n```\n# Hidden\n````\n# Visible two\n", 50, 1,
            ])
            db.execute("COPY items TO '" + str(artifacts / "part-00000.parquet").replace("'", "''") + "' (FORMAT PARQUET)")
            db.execute("DELETE FROM items")
            db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", [
                "org/b", "sha-reused", 0, None, None, None,
            ])
            db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", [
                "org/c", "sha-single", 1, "# One\nSome instructions here.\n", 27, 0,
            ])
            db.execute("COPY items TO '" + str(artifacts / "part-00001.parquet").replace("'", "''") + "' (FORMAT PARQUET)")
            db.close()

            with patch.multiple(mod,
                                ARTIFACT_DIR=artifacts, OUTPUT_DIR=out, WORK_DIR=work,
                                METRICS_DIR=metrics, MANIFEST_PATH=work / "manifest.json",
                                DB_PATH=work / "reuse_counts.duckdb"):
                self.assertEqual(mod.main(["--max-parts", "1", "--memory-limit", "1GB"]), 0)
                self.assertFalse((out / "rq2_first_analysis_summary.txt").exists())
                self.assertTrue((metrics / "part-00000.csv.gz").exists())
                self.assertFalse((metrics / "part-00001.csv.gz").exists())
                self.assertEqual(mod.main(["--memory-limit", "1GB"]), 0)
                self.assertTrue((metrics / "part-00001.csv.gz").exists())
                report = (out / "rq2_first_analysis_summary.txt").read_text(encoding="utf-8")
                self.assertIn("Distinct content hashes: 2", report)
                self.assertIn("Total file occurrences with non-null hashes: 3", report)
                self.assertIn("Single-repository skills analyzed: 1", report)
                self.assertIn("Cross-repository reused skills analyzed: 1", report)
                self.assertIn("Median Markdown headings - reused: 2", report)
                token_report = (out / "rq2_token_overhead_summary.txt").read_text(encoding="utf-8")
                self.assertIn("Number of skills analyzed: 2", token_report)
                self.assertIn("GITSKILLS FULL DATASET", token_report)


if __name__ == "__main__":
    unittest.main()
