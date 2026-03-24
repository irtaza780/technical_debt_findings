"""
Agentic Debt Pipeline — Full Smell Trajectory
==============================================
Produces one CSV row per turn per project, covering every phase.
This single CSV supports both:
  - RQ1: filter all rows, group by project, order by turn_index → smell trajectory
  - RQ3: filter where phase == 'Coding' (baseline) and
         last phase == 'CodeReviewModification' (post-review) → compute delta

Prereqs:
  - Run with the python_smells_detector venv ACTIVE
  - Place pkls/ folder alongside this script (or pass --pkl_dir)
  - Pass --config pointing at code_quality_config.yaml

Usage:
    python agentic_debt_pipeline.py \\
        --pkl_dir  ./pkls \\
        --config   ./code_quality_config.yaml \\
        --output   agentic_debt_results.csv

Output CSV columns (one row per turn):
    project                   — project name (from .pkl filename)
    turn_index                — turn number within the project (0-based)
    phase                     — e.g. Coding, CodeReviewModification, TestModification, ...
    role                      — agent role, e.g. Programmer
    interlocutor              — counterpart agent, e.g. Code Reviewer
    timestamp                 — turn timestamp from the pkl
    py_files                  — number of .py files in current_codebase at this turn
    code_lines                — effective code lines (from software_info)
    structural_smells         — PyExamine: Total Structural Smells
    code_smells               — PyExamine: Total Code Smells
    architectural_smells      — PyExamine: Total Architectural Smells
    total_smells              — sum of all three
    tokens_prompt             — prompt tokens this turn
    tokens_completion         — completion tokens this turn
    tokens_reasoning          — reasoning tokens this turn
    tokens_total              — total tokens this turn
    cost_usd                  — cost this turn in USD
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
# SECTION 1 — PyExamine invocation
# ============================================================

def run_pyexamine(src_dir: str, report_stem: str, config_path: str) -> dict:
    """
    Run analyze_code_quality on src_dir, return parsed smell counts.
    report_stem: full path prefix for the output file (no .txt extension).
    """
    cmd = [
        "analyze_code_quality",
        src_dir,
        "--config", config_path,
        "--output", report_stem,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print(f"      WARNING: analyze_code_quality failed: "
              f"{e.stderr.decode(errors='replace').strip()}")
        return _empty_counts()
    except FileNotFoundError:
        print("      ERROR: `analyze_code_quality` not found — is the venv active?")
        sys.exit(1)

    # Tool may write the report relative to cwd or to src_dir
    for candidate in [
        f"{report_stem}.txt",
        os.path.join(src_dir, f"{os.path.basename(report_stem)}.txt"),
    ]:
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                return parse_summary(f.read())

    print(f"      WARNING: report not found for stem: {report_stem}")
    return _empty_counts()


def parse_summary(text: str) -> dict:
    """
    Extract the three summary counts from the bottom of a PyExamine report:
        Total Structural Smells: 6
        Total Code Smells: 4
        Total Architectural Smells: 5
    """
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
    return {
        "structural_smells": 0,
        "code_smells": 0,
        "architectural_smells": 0,
        "total_smells": 0,
    }


# ============================================================
# SECTION 2 — Helpers
# ============================================================

def extract_py_files(codebase: dict, dest_dir: str) -> list:
    """Write only .py files from current_codebase dict to dest_dir."""
    os.makedirs(dest_dir, exist_ok=True)
    written = []
    for filename, content in codebase.items():
        if filename.endswith(".py"):
            out_path = os.path.join(dest_dir, filename)
            with open(out_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content if content else "")
            written.append(filename)
    return written


def get_code_lines(software_info: Optional[dict]) -> int:
    if not software_info:
        return 0
    return software_info.get("code_lines", 0) or 0


# ============================================================
# SECTION 3 — Per-project processing
# ============================================================

def process_pkl(pkl_path: str, work_root: str, config_path: str) -> list:
    """
    Load one .pkl and return a list of row dicts — one per turn.
    Returns empty list on fatal error.
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
        return []

    if not isinstance(turns, list) or not turns:
        print(f"  ERROR: expected list of turn dicts, got {type(turns)}")
        return []

    print(f"  Turns found: {len(turns)}")

    rows = []
    work_dir = os.path.join(work_root, project_name)
    os.makedirs(work_dir, exist_ok=True)

    for turn in turns:
        turn_index = turn.get("turn_index", "?")
        phase      = turn.get("phase", "")
        role       = turn.get("role", "")
        interlocutor = turn.get("interlocutor", "")
        timestamp  = turn.get("timestamp", "")

        print(f"  → turn {turn_index}  phase={phase}  role={role}  "
              f"interlocutor={interlocutor}")

        codebase = turn.get("current_codebase") or {}

        # Skip turns with no Python code (e.g. pure doc turns)
        py_files_list = [f for f in codebase if f.endswith(".py")]
        if not py_files_list:
            print(f"      No .py files — skipping PyExamine for this turn")
            smells = _empty_counts()
        else:
            # Extract snapshot
            snap_dir = os.path.join(
                work_dir, f"turn_{turn_index}_{phase.replace(' ', '_')}_src"
            )
            extract_py_files(codebase, snap_dir)

            # Run PyExamine
            report_stem = os.path.join(
                work_dir,
                f"{project_name}_turn_{turn_index}_{phase.replace(' ', '_')}_report"
            )
            smells = run_pyexamine(snap_dir, report_stem, config_path)

        print(f"      structural={smells['structural_smells']}  "
              f"code={smells['code_smells']}  "
              f"architectural={smells['architectural_smells']}  "
              f"total={smells['total_smells']}")

        row = {
            "project":              project_name,
            "turn_index":           turn_index,
            "phase":                phase,
            "role":                 role,
            "interlocutor":         interlocutor,
            "timestamp":            timestamp,
            "py_files":             len(py_files_list),
            "code_lines":           get_code_lines(turn.get("software_info")),
            "structural_smells":    smells["structural_smells"],
            "code_smells":          smells["code_smells"],
            "architectural_smells": smells["architectural_smells"],
            "total_smells":         smells["total_smells"],
            "tokens_prompt":        turn.get("tokens_prompt", 0) or 0,
            "tokens_completion":    turn.get("tokens_completion", 0) or 0,
            "tokens_reasoning":     turn.get("tokens_reasoning", 0) or 0,
            "tokens_total":         turn.get("tokens_total", 0) or 0,
            "cost_usd":             turn.get("cost_usd", 0.0) or 0.0,
        }
        rows.append(row)

    print(f"  Done — {len(rows)} rows for {project_name}")
    return rows


# ============================================================
# SECTION 4 — Main
# ============================================================

FIELDNAMES = [
    "project",
    "turn_index",
    "phase",
    "role",
    "interlocutor",
    "timestamp",
    "py_files",
    "code_lines",
    "structural_smells",
    "code_smells",
    "architectural_smells",
    "total_smells",
    "tokens_prompt",
    "tokens_completion",
    "tokens_reasoning",
    "tokens_total",
    "cost_usd",
]


def main():
    parser = argparse.ArgumentParser(
        description="Agentic Debt: full smell trajectory — one row per turn per project"
    )
    parser.add_argument("--pkl_dir",  required=True,
                        help="Directory containing .pkl project files")
    parser.add_argument("--config",   required=True,
                        help="Path to code_quality_config.yaml")
    parser.add_argument("--output",   default="agentic_debt_results.csv",
                        help="Output CSV path (default: agentic_debt_results.csv)")
    parser.add_argument("--work_dir", default="agentic_debt_workdir",
                        help="Working dir for snapshots and reports "
                             "(default: agentic_debt_workdir)")
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

    all_rows = []
    skipped  = []

    for pkl_path in pkl_files:
        rows = process_pkl(str(pkl_path), args.work_dir, args.config)
        if rows:
            all_rows.extend(rows)
        else:
            skipped.append(pkl_path.name)

    if skipped:
        print(f"\nSkipped {len(skipped)} project(s): {skipped}")
    if not all_rows:
        print("No rows produced.")
        sys.exit(1)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{'='*60}")
    print(f"Done.")
    print(f"  Total rows   : {len(all_rows)}")
    print(f"  Projects     : {len(pkl_files) - len(skipped)}")
    print(f"  Output CSV   : {args.output}")
    print(f"{'='*60}")
    print()
    print("To use for RQ3 in pandas:")
    print("  df = pd.read_csv('agentic_debt_results.csv')")
    print("  baseline    = df[df['phase'] == 'Coding']")
    print("  post_review = df[df['phase'] == 'CodeReviewModification']")
    print("                  .groupby('project').last().reset_index()")
    print()
    print("To use for RQ1:")
    print("  trajectory = df.sort_values(['project', 'turn_index'])")


if __name__ == "__main__":
    main()