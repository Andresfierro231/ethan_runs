#!/bin/bash
set -euo pipefail

ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
CAMPAIGN="$ROOT/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
MANIFEST="$CAMPAIGN/corrected_case_manifest.csv"
LAUNCHER="$CAMPAIGN/scripts/run_packed_corrected_salt_q.sbatch"
OUT="$CAMPAIGN/submitted_jobs.csv"

python - <<'PY' "$MANIFEST" "$CAMPAIGN/job_groups.tsv"
import csv, sys
manifest, out = sys.argv[1], sys.argv[2]
rows=list(csv.DictReader(open(manifest)))
groups=[rows[i:i+4] for i in range(0,len(rows),4)]
with open(out,'w') as f:
    f.write('group\tcase_keys\tcase_dirs\n')
    for idx,g in enumerate(groups,1):
        f.write(f"corr_saltq_g{idx}\t{','.join(r['case_key'] for r in g)}\t{','.join(r['case_dir'] for r in g)}\n")
PY

echo "group,job_id,case_keys,case_dirs" > "$OUT"
while IFS=$'\t' read -r group case_keys case_dirs; do
    [[ "$group" == "group" ]] && continue
    sbatch_output="$(sbatch --parsable -J "$group" --export=ALL,CASE_GROUP="$group" "$LAUNCHER")"
    job_id="$(printf '%s\n' "$sbatch_output" | awk '/^[0-9]+(;[A-Za-z0-9_:-]+)?$/ { id=$1 } END { print id }')"
    if [[ -z "$job_id" ]]; then
        printf '%s\n' "$sbatch_output" >&2
        echo "Could not parse sbatch job id for $group" >&2
        exit 1
    fi
    echo "$group,$job_id,$case_keys,$case_dirs" >> "$OUT"
    echo "$group -> $job_id"
done < "$CAMPAIGN/job_groups.tsv"
