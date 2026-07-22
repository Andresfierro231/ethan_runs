# Proposed Evidence Directory Plan

This is an instruction plan only. It does not create or mutate an external
LaTeX repository.

## Proposed Structure

```text
evidence/
  README.md
  schema/
    evidence_packet_schema.csv
  index/
    chapter_evidence_packet_queue.csv
    scientific_study_dispatch_matrix.csv
  ch01_ch04_foundations/
    README.md
    source_path_ledger.csv
    equations_definitions_ledger.csv
    claim_boundary_ledger.csv
    figure_table_targets.csv
  glossary/
    equation_ledger.csv
    symbol_glossary.csv
    assumptions_caveats.csv
    claim_use_map.csv
    source_manifest.csv
  ch07_ch08_results/
    result_status_matrix.csv
    claim_boundary_ledger.csv
    figure_table_target_ledger.csv
    next_study_queue.csv
  ch09_limits_sam/
    README.md
    sam_transfer_ledger.csv
    limitations_status_ledger.csv
    future_work_queue.csv
    claim_boundary_ledger.csv
  reference/
    claim_ledger_summary.md
```

## Import Rules

- Copy only small Markdown/CSV ledgers or selected reviewed figures.
- Preserve original `ethan_runs` source paths in every copied file or in an
  adjacent manifest.
- Do not rewrite prose during artifact transfer.
- Do not make LaTeX `\input{}` changes from this row.
- Do not copy source trees, raw fields, scheduler logs, or broad generated
  artifact directories.

## Outside Writer Use

The outside writer should open:

1. `evidence/README.md`
2. `evidence/glossary/equation_ledger.csv`
3. `evidence/glossary/symbol_glossary.csv`
4. `evidence/ch01_ch04_foundations/README.md`
5. `evidence/ch07_ch08_results/result_status_matrix.csv`
6. `evidence/ch07_ch08_results/claim_boundary_ledger.csv`

The writer can then draft prose in the manuscript workflow while preserving
the source-path, split-role, admission, and runtime-leakage caveats.
