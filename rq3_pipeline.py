


# """
# RQ3 Pipeline: Agentic Debt — Reviewer Mitigation Analysis
# ==========================================================
# Prereqs:
#   - Run with the python_smells_detector venv ACTIVE
#   - Place pkls/ folder alongside this script (or pass --pkl_dir)
#   - Pass --config pointing at code_quality_config.yaml

# Usage:
#     python rq3_pipeline.py \\
#         --pkl_dir  ./pkls \\
#         --config   ./code_quality_config.yaml \\
#         --output   rq3_results.csv

# CSV structure (per project row):
#   [Identity]
#     project, coding_phase, coding_role, coding_interlocutor, coding_turn_index,
#     last_review_phase, last_review_role, last_review_interlocutor,
#     last_review_turn_index, review_cycles_count,
#     py_files_baseline, py_files_post_review,
#     code_lines_baseline, code_lines_post_review

#   [Smell counts — baseline]
#     baseline_structural_smells, baseline_code_smells,
#     baseline_architectural_smells, baseline_total_smells

#   [Smell counts — post-review]
#     postreview_structural_smells, postreview_code_smells,
#     postreview_architectural_smells, postreview_total_smells

#   [Deltas  (negative = improvement)]
#     delta_structural_smells, delta_code_smells,
#     delta_architectural_smells, delta_total_smells

#   [Per review-cycle agent + cost columns  (cycle_1_, cycle_2_, ...)]
#     cycle_N_turn_index, cycle_N_phase,
#     cycle_N_role, cycle_N_interlocutor, cycle_N_timestamp,
#     cycle_N_tokens_prompt, cycle_N_tokens_completion,
#     cycle_N_tokens_reasoning, cycle_N_tokens_total, cycle_N_cost_usd

#   [Review totals]
#     review_tokens_prompt, review_tokens_completion,
#     review_tokens_reasoning, review_tokens_total, review_cost_usd
# """

# import os
# import re
# import sys
# import csv
# import pickle
# import argparse
# import subprocess
# from pathlib import Path
# from typing import Optional


# # ============================================================
# # SECTION 1 — PyExamine invocation
# # ============================================================

# def run_pyexamine(src_dir: str, report_stem: str, config_path: str) -> dict:
#     """
#     Run analyze_code_quality on src_dir.
#     report_stem: full path prefix for the output file (no .txt).
#     Returns smell count dict.
#     """
#     cmd = [
#         "analyze_code_quality",
#         src_dir,
#         "--config", config_path,
#         "--output", report_stem,
#     ]
#     try:
#         subprocess.run(
#             cmd,
#             check=True,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.PIPE,
#         )
#     except subprocess.CalledProcessError as e:
#         print(f"    WARNING: analyze_code_quality failed:\n"
#               f"    {e.stderr.decode(errors='replace').strip()}")
#         return _empty_counts()
#     except FileNotFoundError:
#         print("    ERROR: `analyze_code_quality` not found — is the venv active?")
#         sys.exit(1)

#     # Tool may write the report relative to cwd or relative to src_dir
#     for candidate in [f"{report_stem}.txt",
#                       os.path.join(src_dir, f"{os.path.basename(report_stem)}.txt")]:
#         if os.path.isfile(candidate):
#             with open(candidate, "r", encoding="utf-8", errors="replace") as f:
#                 return parse_summary(f.read())

#     print(f"    WARNING: report not found for stem {report_stem}")
#     return _empty_counts()


# def parse_summary(text: str) -> dict:
#     """Parse the three summary lines from a PyExamine report."""
#     patterns = {
#         "structural_smells":    r"Total Structural Smells\s*:\s*(\d+)",
#         "code_smells":          r"Total Code Smells\s*:\s*(\d+)",
#         "architectural_smells": r"Total Architectural Smells\s*:\s*(\d+)",
#     }
#     counts = {}
#     for key, pattern in patterns.items():
#         m = re.search(pattern, text, re.IGNORECASE)
#         counts[key] = int(m.group(1)) if m else 0
#     counts["total_smells"] = sum(counts.values())
#     return counts


# def _empty_counts() -> dict:
#     return {"structural_smells": 0, "code_smells": 0,
#             "architectural_smells": 0, "total_smells": 0}


# # ============================================================
# # SECTION 2 — Snapshot helpers
# # ============================================================

# def extract_py_files(codebase: dict, dest_dir: str) -> list:
#     """Write only .py files from current_codebase dict to dest_dir."""
#     os.makedirs(dest_dir, exist_ok=True)
#     written = []
#     for filename, content in codebase.items():
#         if filename.endswith(".py"):
#             out_path = os.path.join(dest_dir, filename)
#             with open(out_path, "w", encoding="utf-8", errors="replace") as f:
#                 f.write(content if content else "")
#             written.append(filename)
#     return written


# def get_code_lines(software_info: Optional[dict]) -> int:
#     """Extract code_lines from software_info if present."""
#     if not software_info:
#         return 0
#     return software_info.get("code_lines", 0) or 0


# def find_coding_turn(turns: list) -> Optional[dict]:
#     for t in turns:
#         if t.get("phase") == "Coding":
#             return t
#     return None


# def find_all_review_turns(turns: list) -> list:
#     """Return ALL CodeReviewModification turns in order."""
#     return [t for t in turns if t.get("phase") == "CodeReviewModification"]


# def compute_delta(baseline: dict, post_review: dict) -> dict:
#     """delta = post_review − baseline. Negative = fewer smells = improvement."""
#     all_keys = set(baseline) | set(post_review)
#     return {
#         f"delta_{k}": (post_review.get(k, 0) or 0) - (baseline.get(k, 0) or 0)
#         for k in all_keys
#     }


# # ============================================================
# # SECTION 3 — Per-project processing
# # ============================================================

# def process_pkl(pkl_path: str, work_root: str, config_path: str,
#                 max_cycles: int) -> Optional[dict]:
#     project_name = Path(pkl_path).stem
#     print(f"\n{'='*60}")
#     print(f"Project: {project_name}")
#     print(f"{'='*60}")

#     try:
#         with open(pkl_path, "rb") as f:
#             turns = pickle.load(f)
#     except Exception as e:
#         print(f"  ERROR loading pkl: {e}")
#         return None

#     if not isinstance(turns, list) or not turns:
#         print(f"  ERROR: expected list of turn dicts")
#         return None

#     coding_turn   = find_coding_turn(turns)
#     review_turns  = find_all_review_turns(turns)

#     if coding_turn is None:
#         print(f"  SKIP: no Coding turn found")
#         return None
#     if not review_turns:
#         print(f"  SKIP: no CodeReviewModification turns found")
#         return None

#     last_review_turn = review_turns[-1]

#     print(f"  Baseline    : turn_index={coding_turn.get('turn_index')}  "
#           f"role={coding_turn.get('role')}  interlocutor={coding_turn.get('interlocutor')}")
#     print(f"  Review cycles: {len(review_turns)}  "
#           f"(last turn_index={last_review_turn.get('turn_index')})")

#     coding_codebase  = coding_turn.get("current_codebase") or {}
#     review_codebase  = last_review_turn.get("current_codebase") or {}

#     # Snapshot directories
#     work_dir       = os.path.join(work_root, project_name)
#     baseline_src   = os.path.join(work_dir, "baseline_src")
#     postreview_src = os.path.join(work_dir, "postreview_src")

#     b_files = extract_py_files(coding_codebase, baseline_src)
#     p_files = extract_py_files(review_codebase, postreview_src)
#     print(f"  Baseline .py files   : {b_files}")
#     print(f"  Post-review .py files: {p_files}")

#     # Report stems
#     baseline_report   = os.path.join(work_dir, f"{project_name}_baseline_report")
#     postreview_report = os.path.join(work_dir, f"{project_name}_postreview_report")

#     print("  Running PyExamine on baseline ...")
#     baseline_metrics = run_pyexamine(baseline_src, baseline_report, config_path)
#     print(f"    structural={baseline_metrics['structural_smells']}  "
#           f"code={baseline_metrics['code_smells']}  "
#           f"architectural={baseline_metrics['architectural_smells']}  "
#           f"total={baseline_metrics['total_smells']}")

#     print("  Running PyExamine on post-review ...")
#     postreview_metrics = run_pyexamine(postreview_src, postreview_report, config_path)
#     print(f"    structural={postreview_metrics['structural_smells']}  "
#           f"code={postreview_metrics['code_smells']}  "
#           f"architectural={postreview_metrics['architectural_smells']}  "
#           f"total={postreview_metrics['total_smells']}")

#     delta = compute_delta(baseline_metrics, postreview_metrics)
#     print(f"  Δ total smells : {delta['delta_total_smells']:+d}")

#     # ── Assemble row ──────────────────────────────────────────

#     row = {
#         # Identity & agent metadata — coding turn
#         "project":                  project_name,
#         "coding_phase":             coding_turn.get("phase"),
#         "coding_role":              coding_turn.get("role"),
#         "coding_interlocutor":      coding_turn.get("interlocutor"),
#         "coding_turn_index":        coding_turn.get("turn_index"),
#         # Identity & agent metadata — last review turn
#         "last_review_phase":        last_review_turn.get("phase"),
#         "last_review_role":         last_review_turn.get("role"),
#         "last_review_interlocutor": last_review_turn.get("interlocutor"),
#         "last_review_turn_index":   last_review_turn.get("turn_index"),
#         "review_cycles_count":      len(review_turns),
#         # Project size
#         "py_files_baseline":        len(b_files),
#         "py_files_post_review":     len(p_files),
#         "code_lines_baseline":      get_code_lines(coding_turn.get("software_info")),
#         "code_lines_post_review":   get_code_lines(last_review_turn.get("software_info")),
#         # Smell counts — baseline
#         "baseline_structural_smells":      baseline_metrics["structural_smells"],
#         "baseline_code_smells":            baseline_metrics["code_smells"],
#         "baseline_architectural_smells":   baseline_metrics["architectural_smells"],
#         "baseline_total_smells":           baseline_metrics["total_smells"],
#         # Smell counts — post-review
#         "postreview_structural_smells":    postreview_metrics["structural_smells"],
#         "postreview_code_smells":          postreview_metrics["code_smells"],
#         "postreview_architectural_smells": postreview_metrics["architectural_smells"],
#         "postreview_total_smells":         postreview_metrics["total_smells"],
#         # Deltas
#         "delta_structural_smells":         delta["delta_structural_smells"],
#         "delta_code_smells":               delta["delta_code_smells"],
#         "delta_architectural_smells":      delta["delta_architectural_smells"],
#         "delta_total_smells":              delta["delta_total_smells"],
#     }

#     # Per-cycle agent + token columns
#     # Padded to max_cycles so every row has the same columns
#     review_tokens_prompt     = 0
#     review_tokens_completion = 0
#     review_tokens_reasoning  = 0
#     review_tokens_total      = 0
#     review_cost_usd          = 0.0

#     for i in range(1, max_cycles + 1):
#         prefix = f"cycle_{i}_"
#         if i <= len(review_turns):
#             t = review_turns[i - 1]
#             row[f"{prefix}turn_index"]        = t.get("turn_index")
#             row[f"{prefix}phase"]             = t.get("phase")
#             row[f"{prefix}role"]              = t.get("role")
#             row[f"{prefix}interlocutor"]      = t.get("interlocutor")
#             row[f"{prefix}timestamp"]         = t.get("timestamp")
#             row[f"{prefix}tokens_prompt"]     = t.get("tokens_prompt", 0) or 0
#             row[f"{prefix}tokens_completion"] = t.get("tokens_completion", 0) or 0
#             row[f"{prefix}tokens_reasoning"]  = t.get("tokens_reasoning", 0) or 0
#             row[f"{prefix}tokens_total"]      = t.get("tokens_total", 0) or 0
#             row[f"{prefix}cost_usd"]          = t.get("cost_usd", 0.0) or 0.0

#             review_tokens_prompt     += t.get("tokens_prompt", 0) or 0
#             review_tokens_completion += t.get("tokens_completion", 0) or 0
#             review_tokens_reasoning  += t.get("tokens_reasoning", 0) or 0
#             review_tokens_total      += t.get("tokens_total", 0) or 0
#             review_cost_usd          += t.get("cost_usd", 0.0) or 0.0
#         else:
#             # Pad with empty values for projects with fewer cycles
#             for suffix in ["turn_index", "phase", "role", "interlocutor",
#                            "timestamp", "tokens_prompt", "tokens_completion",
#                            "tokens_reasoning", "tokens_total", "cost_usd"]:
#                 row[f"{prefix}{suffix}"] = ""

#     # Review totals
#     row["review_tokens_prompt"]     = review_tokens_prompt
#     row["review_tokens_completion"] = review_tokens_completion
#     row["review_tokens_reasoning"]  = review_tokens_reasoning
#     row["review_tokens_total"]      = review_tokens_total
#     row["review_cost_usd"]          = review_cost_usd

#     print(f"  Review total : ${review_cost_usd:.4f}  |  "
#           f"tokens: {review_tokens_total}  |  cycles: {len(review_turns)}")

#     return row


# # ============================================================
# # SECTION 4 — Main
# # ============================================================

# def main():
#     parser = argparse.ArgumentParser(
#         description="RQ3: Reviewer mitigation of Agentic Debt"
#     )
#     parser.add_argument("--pkl_dir",  required=True,
#                         help="Directory containing .pkl project files")
#     parser.add_argument("--config",   required=True,
#                         help="Path to code_quality_config.yaml")
#     parser.add_argument("--output",   default="rq3_results.csv",
#                         help="Output CSV path (default: rq3_results.csv)")
#     parser.add_argument("--work_dir", default="rq3_workdir",
#                         help="Working dir for snapshots and reports (default: rq3_workdir)")
#     args = parser.parse_args()

#     if not os.path.isfile(args.config):
#         print(f"ERROR: config not found: {args.config}")
#         sys.exit(1)

#     pkl_files = sorted(Path(args.pkl_dir).glob("*.pkl"))
#     if not pkl_files:
#         print(f"No .pkl files found in: {args.pkl_dir}")
#         sys.exit(1)

#     print(f"Found {len(pkl_files)} project(s)")
#     os.makedirs(args.work_dir, exist_ok=True)

#     # ── First pass: find the maximum number of review cycles across all projects
#     # so we can size the per-cycle columns correctly before writing the CSV.
#     print("Scanning for max review cycles...")
#     max_cycles = 0
#     for pkl_path in pkl_files:
#         try:
#             with open(pkl_path, "rb") as f:
#                 turns = pickle.load(f)
#             n = sum(1 for t in turns if t.get("phase") == "CodeReviewModification")
#             max_cycles = max(max_cycles, n)
#         except Exception:
#             pass
#     print(f"  Max review cycles found: {max_cycles}")

#     # ── Second pass: full analysis
#     results, skipped = [], []
#     for pkl_path in pkl_files:
#         row = process_pkl(str(pkl_path), args.work_dir, args.config, max_cycles)
#         if row is not None:
#             results.append(row)
#         else:
#             skipped.append(pkl_path.name)

#     if skipped:
#         print(f"\nSkipped {len(skipped)} project(s): {skipped}")
#     if not results:
#         print("No results produced.")
#         sys.exit(1)

#     # All rows have identical columns (guaranteed by max_cycles padding)
#     fieldnames = list(results[0].keys())
#     with open(args.output, "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(results)

#     print(f"\nDone. {len(results)} project(s) → {args.output}")
#     print(f"Columns per row: {len(fieldnames)}")


# if __name__ == "__main__":
#     main()





"""
RQ3 Pipeline: Per-Turn Smell Analysis
======================================
Prereqs:
  - Run with the python_smells_detector venv ACTIVE
  - Place pkls/ folder alongside this script (or pass --pkl_dir)
  - Pass --config pointing at code_quality_config.yaml

Usage:
    python rq3_pipeline.py \\
        --pkl_dir  ./pkls \\
        --config   ./code_quality_config.yaml \\
        --output   rq3_results.csv

Output files:
  rq3_results.csv              — one row per turn (original format), columns:
      project, turn_index, phase, role, interlocutor, timestamp,
      py_files, code_lines,
      structural_smells, code_smells, architectural_smells, total_smells,
      tokens_prompt, tokens_completion, tokens_reasoning, tokens_total, cost_usd

  rq3_results_smells_detail.csv — one row per smell instance, columns:
      project, turn_index, phase,
      type, name, description, file, module_class, line_number, severity
"""

import os
import re
import sys
import csv
import pickle
import argparse
import subprocess
from pathlib import Path
from typing import Optional


# ============================================================
# SECTION 1 — PyExamine invocation + CSV parsing
# ============================================================

SMELL_TYPE_MAP = {
    "code":          "code",
    "structural":    "structural",
    "architectural": "architectural",
}

SMELL_CSV_FIELDS = ["type", "name", "description", "file", "module_class", "line_number", "severity"]


def run_pyexamine(src_dir: str, report_stem: str, config_path: str) -> tuple[dict, list[dict]]:
    """
    Run analyze_code_quality on src_dir.
    Returns (counts_dict, smell_rows).
    counts_dict: {structural_smells, code_smells, architectural_smells, total_smells}
    smell_rows:  list of per-smell dicts (empty if no CSV output found)
    """
    cmd = [
        "analyze_code_quality",
        src_dir,
        "--config", config_path,
        "--output", report_stem,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"    WARNING: analyze_code_quality failed:\n"
              f"    {e.stderr.decode(errors='replace').strip()}")
        return _empty_counts(), []
    except FileNotFoundError:
        print("    ERROR: `analyze_code_quality` not found — is the venv active?")
        sys.exit(1)

    smell_rows = []

    # ── Try combined CSV first ───────────────────────────────────────────────
    for candidate in [
        f"{report_stem}.csv",
        f"{report_stem}_smells.csv",
        os.path.join(src_dir, f"{os.path.basename(report_stem)}.csv"),
        os.path.join(src_dir, f"{os.path.basename(report_stem)}_smells.csv"),
    ]:
        if os.path.isfile(candidate):
            smell_rows = _read_pyexamine_csv(candidate)
            return _count_from_rows(smell_rows), smell_rows

    # ── Try per-category CSVs ────────────────────────────────────────────────
    per_type = [
        ("_code_smells.csv",           "code"),
        ("_structural_smells.csv",     "structural"),
        ("_architectural_smells.csv",  "architectural"),
    ]
    for suffix, type_label in per_type:
        for prefix in [report_stem,
                       os.path.join(src_dir, os.path.basename(report_stem))]:
            candidate = f"{prefix}{suffix}"
            if os.path.isfile(candidate):
                smell_rows.extend(_read_pyexamine_csv(candidate, force_type=type_label))

    if smell_rows:
        return _count_from_rows(smell_rows), smell_rows

    # ── Fall back to text summary ────────────────────────────────────────────
    for candidate in [
        f"{report_stem}.txt",
        os.path.join(src_dir, f"{os.path.basename(report_stem)}.txt"),
    ]:
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                counts = _parse_summary_txt(f.read())
            return counts, []

    print(f"    WARNING: no report found for stem {report_stem}")
    return _empty_counts(), []


def _read_pyexamine_csv(csv_path: str, force_type: Optional[str] = None) -> list[dict]:
    """Read a PyExamine CSV and normalise each row into a canonical dict."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            raw = {k.strip(): v.strip() for k, v in raw.items() if k}
            smell_type = (
                force_type
                or SMELL_TYPE_MAP.get(raw.get("Type", "").lower(),
                                      raw.get("Type", "").lower())
            )
            rows.append({
                "type":         smell_type,
                "name":         raw.get("Name", ""),
                "description":  raw.get("Description", ""),
                "file":         raw.get("File", ""),
                "module_class": raw.get("Module/Class", raw.get("Module/class", "")),
                "line_number":  _safe_int(raw.get("Line Number",
                                                   raw.get("Line number", ""))),
                "severity":     raw.get("Severity", ""),
            })
    return rows


def _count_from_rows(smell_rows: list[dict]) -> dict:
    counts = _empty_counts()
    for row in smell_rows:
        t = row.get("type", "").lower()
        if   t == "structural":    counts["structural_smells"]    += 1
        elif t == "code":          counts["code_smells"]          += 1
        elif t == "architectural": counts["architectural_smells"] += 1
    counts["total_smells"] = (
        counts["structural_smells"]
        + counts["code_smells"]
        + counts["architectural_smells"]
    )
    return counts


def _parse_summary_txt(text: str) -> dict:
    """Fallback: parse the three summary lines from a PyExamine text report."""
    patterns = {
        "structural_smells":    r"Total Structural Smells\s*:\s*(\d+)",
        "code_smells":          r"Total Code Smells\s*:\s*(\d+)",
        "architectural_smells": r"Total Architectural Smells\s*:\s*(\d+)",
    }
    counts = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        counts[key] = int(m.group(1)) if m else 0
    counts["total_smells"] = sum(counts.values())
    return counts


def _empty_counts() -> dict:
    return {"structural_smells": 0, "code_smells": 0,
            "architectural_smells": 0, "total_smells": 0}


def _safe_int(val: str) -> Optional[int]:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


# ============================================================
# SECTION 2 — Snapshot helpers
# ============================================================

def extract_py_files(files_dict: dict, dest_dir: str) -> int:
    """Write .py files from a {filename: code} dict to dest_dir. Returns count written."""
    os.makedirs(dest_dir, exist_ok=True)
    written = 0
    for filename, content in files_dict.items():
        if filename.endswith(".py"):
            out_path = os.path.join(dest_dir, filename)
            with open(out_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content if content else "")
            written += 1
    return written


def get_code_lines(software_info: Optional[dict]) -> int:
    if not software_info:
        return 0
    return software_info.get("code_lines", 0) or 0


# ============================================================
# SECTION 3 — Per-project processing
# ============================================================

def process_pkl(pkl_path: str, work_root: str, config_path: str) -> Optional[tuple[list[dict], list[dict]]]:
    """
    Process one project .pkl file, iterating every turn.

    Returns:
        (turn_rows, detail_rows)
        turn_rows   — one dict per turn matching original CSV columns
        detail_rows — one dict per smell instance, joinable via project + turn_index
    """
    project_name = Path(pkl_path).stem
    print(f"\n{'='*60}")
    print(f"Project: {project_name}")
    print(f"{'='*60}")

    try:
        with open(pkl_path, "rb") as f:
            turns = pickle.load(f)
    except Exception as e:
        print(f"  ERROR loading pkl: {e}")
        return None

    if not isinstance(turns, list) or not turns:
        print(f"  ERROR: expected list of turn dicts")
        return None

    work_dir    = os.path.join(work_root, project_name)
    turn_rows   = []
    detail_rows = []

    for turn in turns:
        turn_index   = turn.get("turn_index")
        phase        = turn.get("phase", "")
        role         = turn.get("role", "")
        interlocutor = turn.get("interlocutor", "")
        timestamp    = turn.get("timestamp", "")
        codebase     = turn.get("current_codebase") or {}
        code_lines   = get_code_lines(turn.get("software_info"))

        print(f"  Turn {turn_index:02d}  phase={phase}  role={role}")

        # Write codebase snapshot and run PyExamine
        snap_src    = os.path.join(work_dir, f"turn_{turn_index:02d}_src")
        report_stem = os.path.join(work_dir, f"turn_{turn_index:02d}_report")

        py_file_count = extract_py_files(codebase, snap_src)

        if py_file_count == 0:
            print(f"    No .py files — skipping PyExamine, recording zeros")
            counts = _empty_counts()
            smells = []
        else:
            counts, smells = run_pyexamine(snap_src, report_stem, config_path)

        print(f"    py_files={py_file_count}  code_lines={code_lines}  "
              f"structural={counts['structural_smells']}  "
              f"code={counts['code_smells']}  "
              f"architectural={counts['architectural_smells']}  "
              f"total={counts['total_smells']}")

        # ── Turn-level row — original columns ────────────────────────────────
        turn_rows.append({
            "project":              project_name,
            "turn_index":           turn_index,
            "phase":                phase,
            "role":                 role,
            "interlocutor":         interlocutor,
            "timestamp":            timestamp,
            "py_files":             py_file_count,
            "code_lines":           code_lines,
            "structural_smells":    counts["structural_smells"],
            "code_smells":          counts["code_smells"],
            "architectural_smells": counts["architectural_smells"],
            "total_smells":         counts["total_smells"],
            "tokens_prompt":        turn.get("tokens_prompt", 0) or 0,
            "tokens_completion":    turn.get("tokens_completion", 0) or 0,
            "tokens_reasoning":     turn.get("tokens_reasoning", 0) or 0,
            "tokens_total":         turn.get("tokens_total", 0) or 0,
            "cost_usd":             turn.get("cost_usd", 0.0) or 0.0,
        })

        # ── Per-smell detail rows — joinable via project + turn_index ─────────
        for smell in smells:
            detail_rows.append({
                "project":    project_name,
                "turn_index": turn_index,
                "phase":      phase,
                **smell,
            })

    print(f"  Done — {len(turn_rows)} turns, {len(detail_rows)} smell instances")
    return turn_rows, detail_rows


# ============================================================
# SECTION 4 — Main
# ============================================================

TURN_FIELDS = [
    "project", "turn_index", "phase", "role", "interlocutor", "timestamp",
    "py_files", "code_lines",
    "structural_smells", "code_smells", "architectural_smells", "total_smells",
    "tokens_prompt", "tokens_completion", "tokens_reasoning", "tokens_total", "cost_usd",
]

DETAIL_FIELDS = ["project", "turn_index", "phase"] + SMELL_CSV_FIELDS


def main():
    parser = argparse.ArgumentParser(description="RQ3: Per-turn smell analysis")
    parser.add_argument("--pkl_dir",  required=True,
                        help="Directory containing .pkl project files")
    parser.add_argument("--config",   required=True,
                        help="Path to code_quality_config.yaml")
    parser.add_argument("--output",   default="rq3_results.csv",
                        help="Output CSV path (default: rq3_results.csv)")
    parser.add_argument("--work_dir", default="rq3_workdir",
                        help="Working dir for snapshots and reports (default: rq3_workdir)")
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    pkl_files = sorted(Path(args.pkl_dir).glob("*.pkl"))
    if not pkl_files:
        print(f"No .pkl files found in: {args.pkl_dir}")
        sys.exit(1)

    print(f"Found {len(pkl_files)} project(s)")
    os.makedirs(args.work_dir, exist_ok=True)

    all_turn_rows   = []
    all_detail_rows = []
    skipped         = []

    for pkl_path in pkl_files:
        result = process_pkl(str(pkl_path), args.work_dir, args.config)
        if result is not None:
            turn_rows, detail_rows = result
            all_turn_rows.extend(turn_rows)
            all_detail_rows.extend(detail_rows)
        else:
            skipped.append(pkl_path.name)

    if skipped:
        print(f"\nSkipped {len(skipped)} project(s): {skipped}")
    if not all_turn_rows:
        print("No results produced.")
        sys.exit(1)

    # ── Turn-level CSV (original format, fully preserved) ────────────────────
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TURN_FIELDS)
        writer.writeheader()
        writer.writerows(all_turn_rows)
    print(f"\nTurn-level CSV   → {args.output} ({len(all_turn_rows)} rows)")

    # ── Per-smell detail CSV (new, joinable on project + turn_index) ──────────
    if all_detail_rows:
        detail_path = args.output.replace(".csv", "_smells_detail.csv")
        with open(detail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DETAIL_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_detail_rows)
        print(f"Smell detail CSV → {detail_path} ({len(all_detail_rows)} rows)")
    else:
        print("Note: no smell detail CSV written (PyExamine produced no CSV output).")


if __name__ == "__main__":
    main()