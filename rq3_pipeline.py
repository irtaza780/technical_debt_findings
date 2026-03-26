"""
RQ3 Pipeline v4: Per-Turn Smell Analysis + Multi-Version Refactored Comparison
===============================================================================
Runs BOTH PyExamine and DPy on every snapshot (per-turn + refactored v1/v2/v3).

Prereqs:
  - Run with the python_smells_detector venv ACTIVE
  - Place pkls/ folder alongside this script (or pass --pkl_dir)
  - Pass --config pointing at code_quality_config.yaml
  - Pass --dpy_dir pointing at the DPy/ folder (contains the ./DPy binary)
  - Optionally pass --refactored_dirs (up to 3 dirs, space-separated)

Caching behaviour:
  - PyExamine: if turn_XX_report.csv already exists → skipped
  - DPy:       if <project>_implementation_smells.json already exists in the
               per-turn dpy output dir → skipped
  - Same rules apply for each refactored version snapshot.

Usage:
    python rq3_pipeline.py \\
        --pkl_dir        ./pkls \\
        --config         ./code_quality_config.yaml \\
        --dpy_dir        ./DPy \\
        --output         rq3_results.csv \\
        --work_dir       rq3_workdir \\
        --refactored_dirs ./refactored_code ./refactored_code_v2 ./refactored_code_v3

Output files:
  rq3_results.csv
      One row per turn. Per-turn columns are the same as before.
      Refactored columns are emitted once per version, prefixed v1_/v2_/v3_:

        -- Refactored vN: PyExamine --
        vN_refactored_py_files,
        vN_refactored_structural_smells, vN_refactored_code_smells,
        vN_refactored_architectural_smells, vN_refactored_total_smells,
        vN_delta_ref_vs_baseline_structural, vN_delta_ref_vs_baseline_code,
        vN_delta_ref_vs_baseline_architectural, vN_delta_ref_vs_baseline_total,
        vN_delta_ref_vs_postreview_structural, vN_delta_ref_vs_postreview_code,
        vN_delta_ref_vs_postreview_architectural, vN_delta_ref_vs_postreview_total,

        -- Refactored vN: DPy --
        vN_refactored_dpy_implementation_smells, vN_refactored_dpy_design_smells,
        vN_refactored_dpy_architecture_smells, vN_refactored_dpy_total_smells,
        vN_delta_ref_vs_baseline_dpy_implementation,
        vN_delta_ref_vs_baseline_dpy_design,
        vN_delta_ref_vs_baseline_dpy_architecture,
        vN_delta_ref_vs_baseline_dpy_total,
        vN_delta_ref_vs_postreview_dpy_implementation,
        vN_delta_ref_vs_postreview_dpy_design,
        vN_delta_ref_vs_postreview_dpy_architecture,
        vN_delta_ref_vs_postreview_dpy_total

  rq3_results_smells_detail.csv
      One row per smell instance.
      Columns: tool, type, name, description, file, module_class,
               line_number, severity.
      snapshot column values: "turn_N", "refactored_v1", "refactored_v2",
                               "refactored_v3"
"""

import os
import re
import sys
import csv
import json
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

SMELL_CSV_FIELDS = [
    "tool", "type", "name", "description", "file",
    "module_class", "line_number", "severity",
]


def run_pyexamine(src_dir: str, report_stem: str, config_path: str) -> tuple[dict, list[dict]]:
    """
    Run analyze_code_quality on src_dir.
    Returns (counts_dict, smell_rows).
    Skips execution if report CSV already exists (caching).
    """
    cached = _find_report_csv(report_stem, src_dir)
    if cached:
        smell_rows = _read_pyexamine_csv(cached)
        print(f"    [pyexamine cached] {os.path.basename(cached)} ({len(smell_rows)} rows)")
        return _count_from_rows(smell_rows), smell_rows

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
        return _empty_pyexamine_counts(), []
    except FileNotFoundError:
        print("    ERROR: `analyze_code_quality` not found — is the venv active?")
        sys.exit(1)

    smell_rows = []

    combined = _find_report_csv(report_stem, src_dir)
    if combined:
        smell_rows = _read_pyexamine_csv(combined)
        return _count_from_rows(smell_rows), smell_rows

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

    for candidate in [
        f"{report_stem}.txt",
        os.path.join(src_dir, f"{os.path.basename(report_stem)}.txt"),
    ]:
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                counts = _parse_summary_txt(f.read())
            print(f"    [pyexamine txt fallback] {os.path.basename(candidate)}")
            return counts, []

    print(f"    WARNING: no pyexamine report found for stem {report_stem}")
    return _empty_pyexamine_counts(), []


def _find_report_csv(report_stem: str, src_dir: str) -> Optional[str]:
    for candidate in [
        f"{report_stem}.csv",
        f"{report_stem}_smells.csv",
        os.path.join(src_dir, f"{os.path.basename(report_stem)}.csv"),
        os.path.join(src_dir, f"{os.path.basename(report_stem)}_smells.csv"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return None


def _read_pyexamine_csv(csv_path: str, force_type: Optional[str] = None) -> list[dict]:
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
                "tool":         "pyexamine",
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
    counts = _empty_pyexamine_counts()
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


def _empty_pyexamine_counts() -> dict:
    return {
        "structural_smells":    0,
        "code_smells":          0,
        "architectural_smells": 0,
        "total_smells":         0,
    }


# ============================================================
# SECTION 2 — DPy invocation + JSON parsing
# ============================================================

DPY_SMELL_FILES = {
    "implementation": "_implementation_smells.json",
    "design":         "_design_smells.json",
    "architecture":   "_architecture_smells.json",
}


def run_dpy(
    src_dir: str,
    dpy_output_dir: str,
    dpy_bin_dir: str,
) -> tuple[dict, list[dict]]:
    """
    Run DPy on src_dir, writing JSON outputs to dpy_output_dir.
    Returns (counts_dict, smell_rows).
    Caches: if the implementation smells JSON already exists, skip re-running.
    """
    project_name = Path(src_dir).name
    os.makedirs(dpy_output_dir, exist_ok=True)

    sentinel = os.path.join(
        dpy_output_dir, f"{project_name}_implementation_smells.json"
    )
    if os.path.isfile(sentinel):
        print(f"    [dpy cached] {project_name}")
        return _parse_dpy_outputs(dpy_output_dir, project_name)

    abs_dpy_bin_dir = os.path.abspath(dpy_bin_dir)
    cmd = [
        "./DPy", "analyze",
        "-i", os.path.abspath(src_dir),
        "-o", os.path.abspath(dpy_output_dir),
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            cwd=abs_dpy_bin_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print(f"    WARNING: DPy failed:\n"
              f"    {e.stderr.decode(errors='replace').strip()}")
        return _empty_dpy_counts(), []
    except FileNotFoundError:
        print(f"    ERROR: DPy binary not found in {abs_dpy_bin_dir}")
        sys.exit(1)

    return _parse_dpy_outputs(dpy_output_dir, project_name)


def _parse_dpy_outputs(dpy_output_dir: str, project_name: str) -> tuple[dict, list[dict]]:
    counts     = _empty_dpy_counts()
    smell_rows = []

    for category, suffix in DPY_SMELL_FILES.items():
        json_path = os.path.join(dpy_output_dir, f"{project_name}{suffix}")
        if not os.path.isfile(json_path):
            continue
        try:
            with open(json_path, "r", encoding="utf-8", errors="replace") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"    WARNING: could not read {json_path}: {e}")
            continue

        if not isinstance(entries, list):
            continue

        counts[f"dpy_{category}_smells"] = len(entries)

        for entry in entries:
            smell_rows.append({
                "tool":         "dpy",
                "type":         category,
                "name":         entry.get("Smell", ""),
                "description":  entry.get("Description", ""),
                "file":         entry.get("File", ""),
                "module_class": _dpy_module_class(entry),
                "line_number":  _safe_int(
                                    str(entry.get("Line no", "")).split("-")[0].strip()
                                ),
                "severity":     "",
            })

    counts["dpy_total_smells"] = (
        counts["dpy_implementation_smells"]
        + counts["dpy_design_smells"]
        + counts["dpy_architecture_smells"]
    )
    return counts, smell_rows


def _dpy_module_class(entry: dict) -> str:
    parts = [entry.get("Module", ""), entry.get("Class", "")]
    return ".".join(p for p in parts if p)


def _empty_dpy_counts() -> dict:
    return {
        "dpy_implementation_smells": 0,
        "dpy_design_smells":         0,
        "dpy_architecture_smells":   0,
        "dpy_total_smells":          0,
    }


# ============================================================
# SECTION 3 — Snapshot helpers
# ============================================================

def extract_py_files(files_dict: dict, dest_dir: str) -> int:
    os.makedirs(dest_dir, exist_ok=True)
    written = 0
    for filename, content in files_dict.items():
        if filename.endswith(".py"):
            out_path = os.path.join(dest_dir, filename)
            with open(out_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content if content else "")
            written += 1
    return written


def count_py_files_in_dir(src_dir: str) -> int:
    return (
        sum(1 for f in Path(src_dir).iterdir() if f.suffix == ".py")
        if Path(src_dir).exists() else 0
    )


def get_code_lines(software_info: Optional[dict]) -> int:
    if not software_info:
        return 0
    return software_info.get("code_lines", 0) or 0


def _safe_int(val) -> Optional[int]:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


# ============================================================
# SECTION 4 — Refactored version column helpers
# ============================================================

def _ref_col_names(version: str) -> list[str]:
    """Return all column names for one refactored version (e.g. 'v1')."""
    p = f"{version}_"
    return [
        # PyExamine counts
        f"{p}refactored_py_files",
        f"{p}refactored_structural_smells",
        f"{p}refactored_code_smells",
        f"{p}refactored_architectural_smells",
        f"{p}refactored_total_smells",
        # PyExamine deltas vs baseline
        f"{p}delta_ref_vs_baseline_structural",
        f"{p}delta_ref_vs_baseline_code",
        f"{p}delta_ref_vs_baseline_architectural",
        f"{p}delta_ref_vs_baseline_total",
        # PyExamine deltas vs post-review
        f"{p}delta_ref_vs_postreview_structural",
        f"{p}delta_ref_vs_postreview_code",
        f"{p}delta_ref_vs_postreview_architectural",
        f"{p}delta_ref_vs_postreview_total",
        # DPy counts
        f"{p}refactored_dpy_implementation_smells",
        f"{p}refactored_dpy_design_smells",
        f"{p}refactored_dpy_architecture_smells",
        f"{p}refactored_dpy_total_smells",
        # DPy deltas vs baseline
        f"{p}delta_ref_vs_baseline_dpy_implementation",
        f"{p}delta_ref_vs_baseline_dpy_design",
        f"{p}delta_ref_vs_baseline_dpy_architecture",
        f"{p}delta_ref_vs_baseline_dpy_total",
        # DPy deltas vs post-review
        f"{p}delta_ref_vs_postreview_dpy_implementation",
        f"{p}delta_ref_vs_postreview_dpy_design",
        f"{p}delta_ref_vs_postreview_dpy_architecture",
        f"{p}delta_ref_vs_postreview_dpy_total",
    ]


def _empty_ref_cols(version: str) -> dict:
    """Return a dict of all refactored columns for one version, all None."""
    return {col: None for col in _ref_col_names(version)}


def _fill_ref_cols(
    version: str,
    ref_py_files: int,
    ref_pe_counts: dict,
    ref_dpy_counts: dict,
    baseline_counts_pe: Optional[dict],
    postreview_counts_pe: Optional[dict],
    baseline_counts_dpy: Optional[dict],
    postreview_counts_dpy: Optional[dict],
) -> dict:
    """
    Build the vN_* column dict for one refactored version,
    computing deltas against the project's baseline and post-review turns.
    """
    p = f"{version}_"

    def _delta(ref_val, base_val):
        if ref_val is None or base_val is None:
            return None
        return ref_val - base_val

    cols = {}

    # ── PyExamine ─────────────────────────────────────────────────────────────
    cols[f"{p}refactored_py_files"]               = ref_py_files
    cols[f"{p}refactored_structural_smells"]       = ref_pe_counts["structural_smells"]
    cols[f"{p}refactored_code_smells"]             = ref_pe_counts["code_smells"]
    cols[f"{p}refactored_architectural_smells"]    = ref_pe_counts["architectural_smells"]
    cols[f"{p}refactored_total_smells"]            = ref_pe_counts["total_smells"]

    b = baseline_counts_pe
    cols[f"{p}delta_ref_vs_baseline_structural"]    = _delta(ref_pe_counts["structural_smells"],    b["structural_smells"])    if b else None
    cols[f"{p}delta_ref_vs_baseline_code"]          = _delta(ref_pe_counts["code_smells"],          b["code_smells"])          if b else None
    cols[f"{p}delta_ref_vs_baseline_architectural"] = _delta(ref_pe_counts["architectural_smells"], b["architectural_smells"]) if b else None
    cols[f"{p}delta_ref_vs_baseline_total"]         = _delta(ref_pe_counts["total_smells"],         b["total_smells"])         if b else None

    p2 = postreview_counts_pe
    cols[f"{p}delta_ref_vs_postreview_structural"]    = _delta(ref_pe_counts["structural_smells"],    p2["structural_smells"])    if p2 else None
    cols[f"{p}delta_ref_vs_postreview_code"]          = _delta(ref_pe_counts["code_smells"],          p2["code_smells"])          if p2 else None
    cols[f"{p}delta_ref_vs_postreview_architectural"] = _delta(ref_pe_counts["architectural_smells"], p2["architectural_smells"]) if p2 else None
    cols[f"{p}delta_ref_vs_postreview_total"]         = _delta(ref_pe_counts["total_smells"],         p2["total_smells"])         if p2 else None

    # ── DPy ───────────────────────────────────────────────────────────────────
    cols[f"{p}refactored_dpy_implementation_smells"] = ref_dpy_counts["dpy_implementation_smells"]
    cols[f"{p}refactored_dpy_design_smells"]         = ref_dpy_counts["dpy_design_smells"]
    cols[f"{p}refactored_dpy_architecture_smells"]   = ref_dpy_counts["dpy_architecture_smells"]
    cols[f"{p}refactored_dpy_total_smells"]          = ref_dpy_counts["dpy_total_smells"]

    b = baseline_counts_dpy
    cols[f"{p}delta_ref_vs_baseline_dpy_implementation"] = _delta(ref_dpy_counts["dpy_implementation_smells"], b["dpy_implementation_smells"]) if b else None
    cols[f"{p}delta_ref_vs_baseline_dpy_design"]         = _delta(ref_dpy_counts["dpy_design_smells"],         b["dpy_design_smells"])         if b else None
    cols[f"{p}delta_ref_vs_baseline_dpy_architecture"]   = _delta(ref_dpy_counts["dpy_architecture_smells"],   b["dpy_architecture_smells"])   if b else None
    cols[f"{p}delta_ref_vs_baseline_dpy_total"]          = _delta(ref_dpy_counts["dpy_total_smells"],          b["dpy_total_smells"])          if b else None

    p2 = postreview_counts_dpy
    cols[f"{p}delta_ref_vs_postreview_dpy_implementation"] = _delta(ref_dpy_counts["dpy_implementation_smells"], p2["dpy_implementation_smells"]) if p2 else None
    cols[f"{p}delta_ref_vs_postreview_dpy_design"]         = _delta(ref_dpy_counts["dpy_design_smells"],         p2["dpy_design_smells"])         if p2 else None
    cols[f"{p}delta_ref_vs_postreview_dpy_architecture"]   = _delta(ref_dpy_counts["dpy_architecture_smells"],   p2["dpy_architecture_smells"])   if p2 else None
    cols[f"{p}delta_ref_vs_postreview_dpy_total"]          = _delta(ref_dpy_counts["dpy_total_smells"],          p2["dpy_total_smells"])          if p2 else None

    return cols


# ============================================================
# SECTION 5 — Per-project processing
# ============================================================

def process_pkl(
    pkl_path: str,
    work_root: str,
    config_path: str,
    dpy_bin_dir: Optional[str],
    refactored_dirs: list[tuple[str, str]],   # [(version_label, abs_path), ...]
) -> Optional[tuple[list[dict], list[dict]]]:
    """
    Process one project .pkl file.

    refactored_dirs is a list of (version_label, dir_path) tuples,
    e.g. [("v1", "/abs/refactored_code"), ("v2", "/abs/refactored_code_v2"), ...]

    Returns (turn_rows, detail_rows) or None on failure.
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

    work_dir = os.path.join(work_root, project_name)
    os.makedirs(work_dir, exist_ok=True)

    turn_rows   = []
    detail_rows = []

    baseline_counts_pe    = None
    postreview_counts_pe  = None
    baseline_counts_dpy   = None
    postreview_counts_dpy = None

    # ── Process each turn ────────────────────────────────────────────────────
    for turn in turns:
        turn_index   = turn.get("turn_index")
        phase        = turn.get("phase", "")
        role         = turn.get("role", "")
        interlocutor = turn.get("interlocutor", "")
        timestamp    = turn.get("timestamp", "")
        codebase     = turn.get("current_codebase") or {}
        code_lines   = get_code_lines(turn.get("software_info"))

        snap_src    = os.path.join(work_dir, f"turn_{turn_index:02d}_src")
        report_stem = os.path.join(work_dir, f"turn_{turn_index:02d}_report")

        if not Path(snap_src).exists():
            py_file_count = extract_py_files(codebase, snap_src)
        else:
            py_file_count = count_py_files_in_dir(snap_src)

        print(f"  Turn {turn_index:02d}  phase={phase}  role={role}")

        if py_file_count == 0:
            print(f"    → no .py files, zeros")
            pe_counts  = _empty_pyexamine_counts()
            pe_smells  = []
            dpy_counts = _empty_dpy_counts()
            dpy_smells = []
        else:
            pe_counts, pe_smells = run_pyexamine(snap_src, report_stem, config_path)
            print(f"    [pyexamine] structural={pe_counts['structural_smells']}  "
                  f"code={pe_counts['code_smells']}  "
                  f"architectural={pe_counts['architectural_smells']}  "
                  f"total={pe_counts['total_smells']}")

            if dpy_bin_dir:
                dpy_out = os.path.join(work_dir, f"turn_{turn_index:02d}_dpy_output")
                dpy_counts, dpy_smells = run_dpy(snap_src, dpy_out, dpy_bin_dir)
                print(f"    [dpy]       implementation={dpy_counts['dpy_implementation_smells']}  "
                      f"design={dpy_counts['dpy_design_smells']}  "
                      f"architecture={dpy_counts['dpy_architecture_smells']}  "
                      f"total={dpy_counts['dpy_total_smells']}")
            else:
                dpy_counts = _empty_dpy_counts()
                dpy_smells = []

        if phase == "Coding":
            if baseline_counts_pe  is None: baseline_counts_pe  = pe_counts
            if baseline_counts_dpy is None: baseline_counts_dpy = dpy_counts
        if phase == "CodeReviewModification":
            postreview_counts_pe  = pe_counts
            postreview_counts_dpy = dpy_counts

        # Build base row — vN_* cols pre-filled as None, back-filled below
        row = {
            "project":              project_name,
            "turn_index":           turn_index,
            "phase":                phase,
            "role":                 role,
            "interlocutor":         interlocutor,
            "timestamp":            timestamp,
            "py_files":             py_file_count,
            "code_lines":           code_lines,
            "structural_smells":    pe_counts["structural_smells"],
            "code_smells":          pe_counts["code_smells"],
            "architectural_smells": pe_counts["architectural_smells"],
            "total_smells":         pe_counts["total_smells"],
            "dpy_implementation_smells": dpy_counts["dpy_implementation_smells"],
            "dpy_design_smells":         dpy_counts["dpy_design_smells"],
            "dpy_architecture_smells":   dpy_counts["dpy_architecture_smells"],
            "dpy_total_smells":          dpy_counts["dpy_total_smells"],
            "tokens_prompt":        turn.get("tokens_prompt",     0) or 0,
            "tokens_completion":    turn.get("tokens_completion",  0) or 0,
            "tokens_reasoning":     turn.get("tokens_reasoning",   0) or 0,
            "tokens_total":         turn.get("tokens_total",       0) or 0,
            "cost_usd":             turn.get("cost_usd",         0.0) or 0.0,
        }
        for version, _ in refactored_dirs:
            row.update(_empty_ref_cols(version))
        turn_rows.append(row)

        for smell in pe_smells:
            detail_rows.append({
                "project": project_name, "turn_index": turn_index,
                "phase": phase, "snapshot": f"turn_{turn_index}", **smell,
            })
        for smell in dpy_smells:
            detail_rows.append({
                "project": project_name, "turn_index": turn_index,
                "phase": phase, "snapshot": f"turn_{turn_index}", **smell,
            })

    # ── Refactored snapshots — one pass per version ───────────────────────────
    for version, ref_root in refactored_dirs:
        ref_src = os.path.join(ref_root, project_name)

        if not Path(ref_src).exists():
            print(f"  [{version}] Refactored dir not found: {ref_src} — skipping")
            continue

        ref_py_files = count_py_files_in_dir(ref_src)
        if ref_py_files == 0:
            print(f"  [{version}] No .py files in refactored dir — skipping")
            continue

        print(f"  [{version}] Refactored snapshot ({ref_py_files} .py files)...")

        # PyExamine — unique report stem per version
        ref_pe_stem = os.path.join(work_dir, f"{project_name}_{version}_refactored_report")
        ref_pe_counts, ref_pe_smells = run_pyexamine(ref_src, ref_pe_stem, config_path)
        print(f"    [pyexamine] structural={ref_pe_counts['structural_smells']}  "
              f"code={ref_pe_counts['code_smells']}  "
              f"architectural={ref_pe_counts['architectural_smells']}  "
              f"total={ref_pe_counts['total_smells']}")

        for smell in ref_pe_smells:
            detail_rows.append({
                "project": project_name, "turn_index": None,
                "phase": f"Refactored_{version}",
                "snapshot": f"refactored_{version}", **smell,
            })

        # DPy — unique output dir per version
        if dpy_bin_dir:
            ref_dpy_out = os.path.join(
                work_dir, f"{project_name}_{version}_refactored_dpy_output"
            )
            ref_dpy_counts, ref_dpy_smells = run_dpy(ref_src, ref_dpy_out, dpy_bin_dir)
            print(f"    [dpy]       implementation={ref_dpy_counts['dpy_implementation_smells']}  "
                  f"design={ref_dpy_counts['dpy_design_smells']}  "
                  f"architecture={ref_dpy_counts['dpy_architecture_smells']}  "
                  f"total={ref_dpy_counts['dpy_total_smells']}")

            for smell in ref_dpy_smells:
                detail_rows.append({
                    "project": project_name, "turn_index": None,
                    "phase": f"Refactored_{version}",
                    "snapshot": f"refactored_{version}", **smell,
                })
        else:
            ref_dpy_counts = _empty_dpy_counts()

        # Back-fill vN_* columns into every turn row for this project
        filled = _fill_ref_cols(
            version,
            ref_py_files,
            ref_pe_counts,
            ref_dpy_counts,
            baseline_counts_pe,
            postreview_counts_pe,
            baseline_counts_dpy,
            postreview_counts_dpy,
        )
        for row in turn_rows:
            row.update(filled)

    print(f"  Done — {len(turn_rows)} turns, {len(detail_rows)} smell instances")
    return turn_rows, detail_rows


# ============================================================
# SECTION 6 — Field list builder + Main
# ============================================================

BASE_TURN_FIELDS = [
    "project", "turn_index", "phase", "role", "interlocutor", "timestamp",
    "py_files", "code_lines",
    # PyExamine per-turn
    "structural_smells", "code_smells", "architectural_smells", "total_smells",
    # DPy per-turn
    "dpy_implementation_smells", "dpy_design_smells",
    "dpy_architecture_smells", "dpy_total_smells",
    # Tokens / cost
    "tokens_prompt", "tokens_completion", "tokens_reasoning",
    "tokens_total", "cost_usd",
]

DETAIL_FIELDS = [
    "project", "turn_index", "phase", "snapshot",
    "tool", "type", "name", "description", "file",
    "module_class", "line_number", "severity",
]


def build_turn_fields(versions: list[str]) -> list[str]:
    """Append vN_* column blocks after the base fields, one block per version."""
    fields = list(BASE_TURN_FIELDS)
    for version in versions:
        fields.extend(_ref_col_names(version))
    return fields


def main():
    parser = argparse.ArgumentParser(
        description="RQ3 v4: Per-turn + multi-version refactored smell analysis "
                    "(PyExamine + DPy)"
    )
    parser.add_argument("--pkl_dir",  required=True,
                        help="Directory containing .pkl project files")
    parser.add_argument("--config",   required=True,
                        help="Path to code_quality_config.yaml")
    parser.add_argument("--dpy_dir",  default=None,
                        help="Path to the DPy/ folder containing the DPy binary. "
                             "Omit to skip DPy analysis.")
    parser.add_argument("--output",   default="rq3_results.csv",
                        help="Output CSV path (default: rq3_results.csv)")
    parser.add_argument("--work_dir", default="rq3_workdir",
                        help="Working dir for snapshots/reports")
    parser.add_argument(
        "--refactored_dirs",
        nargs="+",
        default=[],
        metavar="DIR",
        help="One or more refactored code root dirs in version order "
             "(e.g. ./refactored_code ./refactored_code_v2 ./refactored_code_v3). "
             "Labelled v1, v2, v3 ... automatically.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    dpy_bin_dir = None
    if args.dpy_dir:
        dpy_bin_dir    = os.path.abspath(args.dpy_dir)
        dpy_executable = os.path.join(dpy_bin_dir, "DPy")
        if not os.path.isfile(dpy_executable):
            print(f"ERROR: DPy binary not found at {dpy_executable}")
            sys.exit(1)
        print(f"DPy binary     : {dpy_executable}")
    else:
        print("No --dpy_dir provided — DPy columns will be zero/empty")

    # Build [(version_label, abs_path), ...] — auto-label v1, v2, v3 ...
    refactored_dirs = [
        (f"v{i+1}", os.path.abspath(d))
        for i, d in enumerate(args.refactored_dirs)
    ]
    if refactored_dirs:
        print("Refactored versions:")
        for version, path in refactored_dirs:
            print(f"  {version} → {path}")
    else:
        print("No --refactored_dirs provided — refactored columns will be empty")

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
        result = process_pkl(
            str(pkl_path),
            args.work_dir,
            args.config,
            dpy_bin_dir,
            refactored_dirs,
        )
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

    versions    = [v for v, _ in refactored_dirs]
    turn_fields = build_turn_fields(versions)

    # ── Turn-level CSV ────────────────────────────────────────────────────────
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=turn_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_turn_rows)
    print(f"\nTurn-level CSV   → {args.output} ({len(all_turn_rows)} rows)")

    # ── Per-smell detail CSV ──────────────────────────────────────────────────
    if all_detail_rows:
        detail_path = args.output.replace(".csv", "_smells_detail.csv")
        with open(detail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DETAIL_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_detail_rows)
        print(f"Smell detail CSV → {detail_path} ({len(all_detail_rows)} rows)")
    else:
        print("Note: no smell detail CSV written (no smell output from either tool).")


if __name__ == "__main__":
    main()