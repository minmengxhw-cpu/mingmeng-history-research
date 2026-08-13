# Batch 13 Migration Report

## Scope

1. Insert 11 `page_provenance` stubs for domestic short pages that lacked provenance.
2. Clear binary PNG garbage text on page_id=20623.
3. No OCR. No citation promotion.

## Preconditions

- Branch: `agent/deepseek-domestic-audit-20260803`
- Source DB SHA-256 (Batch12 after): `d8c4dcebddd11e7bc7d62fab9704e7da3bebfb1abc57021b4f62df6b97e65363`
- Input: `02_analysis/batch13_missing_provenance_stubs.csv`

## Apply result

| Item | Value |
|---|---|
| Stubs inserted | 11 |
| Binary text cleared | 1 |
| Stubs with citation_ready=1 | 0 |
| Short pages still missing provenance | 0 |
| FK violations | 0 |
| integrity_check | ok |
| Result SHA-256 | `9413af230e80a8a64768daa92722c5cfec0eea8b6732212e3351b0d1e8e7646a` |
| Backup | `research_index.sqlite.pre_deepseek_batch13_20260807T230546.bak` |

## Notes

- `source_sha256` is a deterministic **locator stub** over URL/path + page_id, not file bytes; notes mark `locator_stub_not_file_bytes`.
- Broader domestic missing-provenance (~588 pages) is out of this batch.
