"""Extra RQ1 numbers used in the paper text: Gini coefficient and the
collection/mirror path share. Run after: python code/rq1_reuse.py sample (or fetch)
Usage: python code/rq1_extra.py [path/to/occ.parquet]"""
import sys, duckdb, numpy as np

OCC = sys.argv[1] if len(sys.argv) > 1 else "data/occ.parquet"
con = duckdb.connect()

# 1) Gini coefficient of the number of repositories per distinct content
r = con.sql(f"""SELECT count(DISTINCT repo_full_name) AS n_repos
               FROM '{OCC}' GROUP BY file_sha""").df().n_repos.values
x = np.sort(r).astype(float); n = len(x); i = np.arange(1, n + 1)
gini = 2 * np.sum(i * x) / (n * x.sum()) - (n + 1) / n
print(f"Gini (repos per content, n={n}): {gini:.5f}")

# 2) Share of occurrences in collection/mirror paths: top-100 contents vs all files.
#    Agent config folders (.claude/, .agents/, ...) are checked first, so a path
#    like .claude/skills/awesome-x/ is NOT counted as collection/mirror.
#    Top 100 = same order as t4_top50_reused (n_repos DESC, occurrences DESC, file_sha).
q = f"""
WITH occ AS (
  SELECT file_sha, repo_full_name,
    CASE WHEN regexp_matches(path, '^\\.[a-z]+/') THEN 'agent config dir'
         WHEN regexp_matches(lower(path), 'awesome|mirror|collection|vendor|third_party|external')
              THEN 'collection/mirror'
         ELSE 'other' END AS path_kind
  FROM '{OCC}'),
top100 AS (
  SELECT file_sha FROM occ GROUP BY file_sha
  ORDER BY count(DISTINCT repo_full_name) DESC, count(*) DESC, file_sha LIMIT 100)
SELECT 'top 100 contents' AS grp,
       round(100.0 * avg(CASE WHEN path_kind = 'collection/mirror' THEN 1 ELSE 0 END), 1) AS pct_collection_mirror,
       count(*) AS occurrences
FROM occ WHERE file_sha IN (SELECT file_sha FROM top100)
UNION ALL
SELECT 'all files',
       round(100.0 * avg(CASE WHEN path_kind = 'collection/mirror' THEN 1 ELSE 0 END), 1),
       count(*)
FROM occ
"""
print(con.sql(q).df().to_string(index=False))
