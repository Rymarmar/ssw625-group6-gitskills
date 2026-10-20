"""
RQ1: How is exact SKILL.md reuse distributed across repositories in GitSkills?

Step 1, pick ONE data source:
  a) Sample (recommended, 13k distinct skills):
       python rq1_reuse.py sample agent_skills_sample.db
     The .db comes from agent_skills_sample.zip in
     https://github.com/giuseppedestefanis/gitskills-sample
  b) Full dataset (3.8M files, needs internet):
       python rq1_reuse.py fetch
     Pulls only the small columns needed from Hugging Face (mvaccargiu/gitskills).
  Both write data/occ.parquet and data/repos.parquet.
Step 2 (offline, re-runnable):  python rq1_reuse.py analyze
    Writes CSV tables to out/ and prints a summary.

Requires: pip install duckdb pandas scipy
"""
import os
import sys

import sqlite3

import duckdb
import numpy as np
import pandas as pd

HF = "hf://datasets/mvaccargiu/gitskills@~parquet"
DATA, OUT = "data", "out"
# Files shorter than this are mostly stubs/symlink text (e.g. "../.claude/SKILL.md").
MIN_BODY_CHARS = 100


def fetch():
    os.makedirs(DATA, exist_ok=True)
    con = duckdb.connect()
    con.sql("INSTALL httpfs; LOAD httpfs;")
    print("Downloading artifact occurrences (selected columns only)...")
    con.sql(f"""
        COPY (
          SELECT {OCC_COLS}
          FROM read_parquet('{HF}/artifacts/train/*.parquet')
        ) TO '{DATA}/occ.parquet' (FORMAT parquet)
    """)
    print("Downloading repository metadata...")
    con.sql(f"""
        COPY (SELECT * EXCLUDE (description) FROM read_parquet('{HF}/repos/train/*.parquet'))
        TO '{DATA}/repos.parquet' (FORMAT parquet)
    """)
    print("Done:", con.sql(f"SELECT count(*) FROM '{DATA}/occ.parquet'").fetchone()[0], "occurrences")


OCC_COLS = ("repo_full_name, path, location_class, file_sha, dedup_primary, "
            "frontmatter_valid, name, body_chars, has_scripts, has_references")


def sample(db_path):
    os.makedirs(DATA, exist_ok=True)
    src = sqlite3.connect(db_path)
    occ = duckdb.from_df(__import__("pandas").read_sql(f"SELECT {OCC_COLS} FROM artifacts", src))
    occ.write_parquet(f"{DATA}/occ.parquet")
    repos = duckdb.from_df(__import__("pandas").read_sql("SELECT * FROM repos", src).drop(columns=["description"]))
    repos.write_parquet(f"{DATA}/repos.parquet")
    print("Done:", len(occ), "occurrences from", db_path)


def location_test(tab, unit):
    """Chi-square test of location_class x cross_repo, plus odds ratio (95% CI) of each
    location being cross-repo relative to the 'other' location."""
    from scipy.stats import chi2_contingency
    ct = tab.pivot(index="location_class", columns="cross_repo", values="n").fillna(0)
    chi2, p, dof, _ = chi2_contingency(ct.values)
    cramers_v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
    ref = ct.loc["other"]
    rows = []
    for loc, r in ct.iterrows():
        a, b, c, d = r[1], r[0], ref[1], ref[0]   # cross / not-cross for loc and for 'other'
        odds = (a * d) / (b * c)
        se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        rows.append({"unit": unit, "location_class": loc, "n": int(a + b),
                     "pct_cross_repo": round(100 * a / (a + b), 2),
                     "odds_ratio_vs_other": round(odds, 3),
                     "or_ci95_low": round(odds * np.exp(-1.96 * se), 3),
                     "or_ci95_high": round(odds * np.exp(1.96 * se), 3),
                     "chi2": round(chi2, 2), "dof": dof, "p_value": p,
                     "cramers_v": round(cramers_v, 3)})
    return pd.DataFrame(rows)


def analyze():
    os.makedirs(OUT, exist_ok=True)
    con = duckdb.connect()
    con.sql(f"CREATE VIEW occ AS SELECT * FROM '{DATA}/occ.parquet'")
    con.sql(f"CREATE VIEW repos AS SELECT * FROM '{DATA}/repos.parquet'")

    # One row per distinct content (file_sha)
    con.sql(f"""
        CREATE TABLE grp AS
        SELECT file_sha,
               count(*)                         AS occurrences,
               count(DISTINCT repo_full_name)   AS n_repos,
               arg_max(name, dedup_primary)     AS name,
               max(body_chars)                  AS body_chars,
               max(has_scripts)                 AS has_scripts,
               max(has_references)              AS has_references
        FROM occ GROUP BY file_sha
    """)

    def save(sql, fname):
        df = con.sql(sql).df()
        df.to_csv(f"{OUT}/{fname}", index=False)
        return df

    # T1: headline numbers (all files, and excluding tiny stubs)
    t1 = save(f"""
        SELECT label,
               sum(occurrences)                                            AS occurrences,
               count(*)                                                    AS distinct_contents,
               round(100.0 * sum(occurrences) FILTER (WHERE occurrences > 1) / sum(occurrences), 2)
                                                                           AS pct_occ_duplicated,
               count(*) FILTER (WHERE n_repos > 1)                         AS contents_in_2plus_repos,
               round(100.0 * sum(occurrences) FILTER (WHERE n_repos > 1) / sum(occurrences), 2)
                                                                           AS pct_occ_cross_repo,
               round(100.0 * sum(occurrences) FILTER (WHERE occurrences > 1 AND n_repos = 1) / sum(occurrences), 2)
                                                                           AS pct_occ_within_repo_only
        FROM (SELECT 'all' AS label, * FROM grp
              UNION ALL
              SELECT 'body_chars>={MIN_BODY_CHARS}', * FROM grp WHERE body_chars >= {MIN_BODY_CHARS})
        GROUP BY label ORDER BY label
    """, "t1_overview.csv")

    # T2: how many repos does each distinct content appear in?
    t2 = save("""
        SELECT bucket, count(*) AS distinct_contents, sum(occurrences) AS occurrences
        FROM (SELECT *, CASE WHEN n_repos = 1 THEN '1'
                             WHEN n_repos = 2 THEN '2'
                             WHEN n_repos <= 5 THEN '3-5'
                             WHEN n_repos <= 10 THEN '6-10'
                             WHEN n_repos <= 100 THEN '11-100'
                             WHEN n_repos <= 1000 THEN '101-1000'
                             ELSE '>1000' END AS bucket,
                        CASE WHEN n_repos = 1 THEN 1 WHEN n_repos = 2 THEN 2 WHEN n_repos <= 5 THEN 3
                             WHEN n_repos <= 10 THEN 4 WHEN n_repos <= 100 THEN 5
                             WHEN n_repos <= 1000 THEN 6 ELSE 7 END AS ord
              FROM grp)
        GROUP BY bucket, ord ORDER BY ord
    """, "t2_repos_per_content.csv")

    # T3: concentration - share of cross-repo occurrences held by the top-K contents
    t3 = save("""
        WITH x AS (SELECT occurrences, row_number() OVER (ORDER BY n_repos DESC, occurrences DESC) AS rk,
                          count(*) OVER () AS n, sum(occurrences) OVER () AS tot
                   FROM grp WHERE n_repos > 1)
        SELECT k AS top_k,
               round(100.0 * sum(occurrences) FILTER (WHERE rk <= k) / any_value(tot), 2) AS pct_of_cross_repo_occ
        FROM x, (SELECT unnest([10, 100, 1000, 10000]) AS k)
        GROUP BY k ORDER BY k
    """, "t3_concentration.csv")

    # T4: most reused skills
    t4 = save("""
        SELECT file_sha, name, n_repos, occurrences, body_chars, has_scripts, has_references
        FROM grp ORDER BY n_repos DESC, occurrences DESC, file_sha LIMIT 50
    """, "t4_top50_reused.csv")

    # T5: robustness - drop forked repositories
    t5 = save(f"""
        WITH o AS (SELECT occ.* FROM occ JOIN repos r ON r.full_name = occ.repo_full_name WHERE r.is_fork = 0),
             g AS (SELECT file_sha, count(*) AS occurrences, count(DISTINCT repo_full_name) AS n_repos FROM o GROUP BY 1)
        SELECT 'non-fork repos' AS label, sum(occurrences) AS occurrences, count(*) AS distinct_contents,
               round(100.0 * sum(occurrences) FILTER (WHERE n_repos > 1) / sum(occurrences), 2) AS pct_occ_cross_repo
        FROM g
    """, "t5_nonfork.csv")

    # T6: reuse by location (e.g. .claude/skills vs other)
    t6 = save("""
        SELECT o.location_class, count(*) AS occurrences,
               round(100.0 * count(*) FILTER (WHERE g.n_repos > 1) / count(*), 2) AS pct_cross_repo
        FROM occ o JOIN grp g USING (file_sha)
        GROUP BY 1 ORDER BY occurrences DESC
    """, "t6_by_location.csv")

    # T7: is cross-repo reuse associated with location? Chi-square + odds ratios vs 'other'.
    # Two units of analysis: every file occurrence (matches T6), and one row per distinct
    # content using its representative's location (independent observations).
    occ_tab = con.sql("""
        SELECT o.location_class, (g.n_repos > 1)::INT AS cross_repo, count(*) AS n
        FROM occ o JOIN grp g USING (file_sha) GROUP BY 1, 2
    """).df()
    cont_tab = con.sql("""
        SELECT o.location_class, (g.n_repos > 1)::INT AS cross_repo, count(*) AS n
        FROM occ o JOIN grp g USING (file_sha) WHERE o.dedup_primary = 1 GROUP BY 1, 2
    """).df()
    t7 = pd.concat([location_test(occ_tab, "file occurrences"),
                    location_test(cont_tab, "distinct contents")])
    t7.to_csv(f"{OUT}/t7_location_test.csv", index=False)

    for title, df in [("Overview", t1), ("Repos per content", t2), ("Concentration", t3),
                      ("Top 10 reused", t4.head(10)), ("Non-fork", t5), ("By location", t6),
                      ("Location vs cross-repo reuse (chi-square, odds ratio vs 'other')", t7)]:
        print(f"\n== {title} ==\n{df.to_string(index=False)}")
    print(f"\nCSV files written to {OUT}/")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sample" and len(sys.argv) > 2:
        sample(sys.argv[2])
    elif cmd in ("fetch", "analyze"):
        {"fetch": fetch, "analyze": analyze}[cmd]()
    else:
        print(__doc__)
