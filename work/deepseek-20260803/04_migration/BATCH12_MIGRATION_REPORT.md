# Batch 12 Migration Report

## Scope

Demote unsafe `page_provenance.citation_ready` flags on domestic short pages
(`text < 120`), and stamp empty-page audit notes. No OCR. No citation promotion.

## Preconditions

- Branch guard: `agent/deepseek-domestic-audit-20260803`
- Source DB SHA-256 (Batch10 after): `fb7cefcf70fcee92fb9d020d20b1c610d102f14aa6aaaf004d34f50237859295`
- Input: `02_analysis/short_pages_citation_demote.csv` (82 rows)

## Apply result

| Item | Value |
|---|---|
| Mode | apply |
| Pages demoted (1→0) | 82 |
| Empty pages stamped | 6 |
| Short pages still citation_ready=1 | 0 |
| FK violations | 0 |
| integrity_check | ok |
| Result SHA-256 | `d8c4dcebddd11e7bc7d62fab9704e7da3bebfb1abc57021b4f62df6b97e65363` |
| Backup | `research_index.sqlite.pre_deepseek_batch12_20260807T230218.bak` |

## Policy

1. Never promote citation_ready in this batch.
2. Any domestic page with `text < 120` and `citation_ready=1` is demoted.
3. Demoted rows: `needs_human_review=1`, `review_status=review_only`, machine note prefixed `DeepSeek Batch12 short-page demotion`.
