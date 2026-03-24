#!/usr/bin/env bash
set -euo pipefail

TRACES_DIR="Agentic-Debt/traces"
OUT_ROOT="output"
CONFIG="code_quality_config.yaml"
TYPES=("code" "architectural" "structural")
MASTER_LOG="$OUT_ROOT/run_analysis.log"

mkdir -p "$OUT_ROOT"

# Clear/init the master log
echo "=== Analysis Run: $(date) ===" > "$MASTER_LOG"

log() {
  echo "$1" | tee -a "$MASTER_LOG"
}

for project_dir in "$TRACES_DIR"/*/; do
  project=$(basename "$project_dir")

  py_count=$(find "$project_dir" -type f -name "*.py" | wc -l)
  if [[ "$py_count" -eq 0 ]]; then
    log "SKIP $project (no .py files)"
    continue
  fi

  log ""
  log "=== [$project] $py_count .py file(s) ==="

  project_out="$OUT_ROOT/$project"
  mkdir -p "$project_out"

  for t in "${TYPES[@]}"; do
    type_out="$project_out/$t"
    mkdir -p "$type_out"

    report_name="${project}_${t}"
    per_run_log="$type_out/${report_name}.log"

    log "  -> type=$t | report: $type_out/$report_name"

    # Run analyzer, capture its own output, also keep the tool's code_analysis.log
    if analyze_code_quality "$project_dir" \
        --config "$CONFIG" \
        --output "$type_out/$report_name" \
        --type "$t" \
        --debug \
        > "$per_run_log" 2>&1; then
      log "     OK"
    else
      log "     FAILED (see $per_run_log)"
    fi

    # Copy the tool's own log (it writes to code_analysis.log by default)
    if [[ -f "code_analysis.log" ]]; then
      cp "code_analysis.log" "$type_out/${report_name}_tool.log"
    fi

  done
done

log ""
log "=== Done: $(date) ==="
log "Outputs in: $OUT_ROOT/<project>/{code,architectural,structural}/"