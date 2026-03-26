"""
RQ3 Pipeline v3: Per-Turn Smell Analysis + Refactored Code Comparison
=======================================================================
Now runs BOTH PyExamine and DPy on every snapshot (per-turn + refactored).

Prereqs:
  - Run with the python_smells_detector venv ACTIVE
  - Place pkls/ folder alongside this script (or pass --pkl_dir)
  - Pass --config pointing at code_quality_config.yaml
  - Pass --dpy_dir pointing at the DPy/ folder (contains the ./DPy binary)
  - Optionally place refactored code under --refactored_dir/project_name/

Caching behaviour:
  - PyExamine: if turn_XX_report.csv already exists → skipped
  - DPy:       if <project>_implementation_smells.json already exists in the
               per-turn dpy output dir → skipped
  - Same rules apply for the refactored snapshot.

Usage:
    python rq3_pipeline.py \\
        --pkl_dir        ./pkls \\
        --config         ./code_quality_config.yaml \\
        --dpy_dir        ./DPy \\
        --output         rq3_results.csv \\
        --work_dir       rq3_workdir \\
        --refactored_dir ./refactored_code

Output files:
  rq3_results.csv
      One row per turn.  Columns:
        project, turn_index, phase, role, interlocutor, timestamp,
        py_files, code_lines,
        -- PyExamine --
        structural_smells, code_smells, architectural_smells, total_smells,
        -- DPy --
        dpy_implementation_smells, dpy_design_smells,
        dpy_architecture_smells, dpy_total_smells,
        -- token / cost --
        tokens_prompt, tokens_completion, tokens_reasoning,
        tokens_total, cost_usd,
        -- Refactored: PyExamine --
        refactored_py_files,
        refactored_structural_smells, refactored_code_smells,
        refactored_architectural_smells, refactored_total_smells,
        delta_ref_vs_baseline_structural, delta_ref_vs_baseline_code,
        delta_ref_vs_baseline_architectural, delta_ref_vs_baseline_total,
        delta_ref_vs_postreview_structural, delta_ref_vs_postreview_code,
        delta_ref_vs_postreview_architectural, delta_ref_vs_postreview_total,
        -- Refactored: DPy --
        refactored_dpy_implementation_smells, refactored_dpy_design_smells,
        refactored_dpy_architecture_smells, refactored_dpy_total_smells,
        delta_ref_vs_baseline_dpy_implementation,
        delta_ref_vs_baseline_dpy_design,
        delta_ref_vs_baseline_dpy_architecture,
        delta_ref_vs_baseline_dpy_total,
        delta_ref_vs_postreview_dpy_implementation,
        delta_ref_vs_postreview_dpy_design,
        delta_ref_vs_postreview_dpy_architecture,
        delta_ref_vs_postreview_dpy_total

  rq3_results_smells_detail.csv
      One row per smell instance.
      Extra column:  tool  ("pyexamine" | "dpy")
      snapshot column values: "turn_N" (per-turn), "refactored"
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

# Maps the JSON filename suffix → canonical smell category key
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

    The project name DPy uses is the basename of src_dir — this determines
    the output filenames (e.g. turn_00_src_implementation_smells.json).

    Returns (counts_dict, smell_rows).
    Caches: if the implementation smells JSON already exists, skip re-running.
    """
    project_name = Path(src_dir).name
    os.makedirs(dpy_output_dir, exist_ok=True)

    # ── Cache check: implementation smells JSON is always produced (even when
    #    empty), so we use it as the sentinel ─────────────────────────────────
    sentinel = os.path.join(
        dpy_output_dir, f"{project_name}_implementation_smells.json"
    )
    if os.path.isfile(sentinel):
        print(f"    [dpy cached] {project_name}")
        return _parse_dpy_outputs(dpy_output_dir, project_name)

    # ── Run DPy ──────────────────────────────────────────────────────────────
    # Must cd into the DPy/ folder and run ./DPy from there.
    # cwd must be an absolute path; the executable is ./DPy relative to cwd.
    abs_dpy_bin_dir = os.path.abspath(dpy_bin_dir)
    cmd = [
        "./DPy", "analyze",
        "-i", os.path.abspath(src_dir),
        "-o", os.path.abspath(dpy_output_dir),
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            cwd=abs_dpy_bin_dir,      # cd into DPy/ before running
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print(f"    WARNING: DPy failed:\n"
              f"    {e.stderr.decode(errors='replace').strip()}")
        return _empty_dpy_counts(), []
    except FileNotFoundError:
        print(f"    ERROR: DPy binary not found at {dpy_executable}")
        sys.exit(1)

    return _parse_dpy_outputs(dpy_output_dir, project_name)


def _parse_dpy_outputs(dpy_output_dir: str, project_name: str) -> tuple[dict, list[dict]]:
    """
    Read all DPy JSON smell files for project_name from dpy_output_dir.
    Returns (counts_dict, smell_rows).
    """
    counts    = _empty_dpy_counts()
    smell_rows = []

    for category, suffix in DPY_SMELL_FILES.items():
        json_path = os.path.join(dpy_output_dir, f"{project_name}{suffix}")
        if not os.path.isfile(json_path):
            # Architecture (and ML) files are simply absent when nothing found
            continue
        try:
            with open(json_path, "r", encoding="utf-8", errors="replace") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"    WARNING: could not read {json_path}: {e}")
            continue

        if not isinstance(entries, list):
            continue

        count_key = f"dpy_{category}_smells"
        counts[count_key] = len(entries)

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
                "severity":     "",   # DPy does not emit severity
            })

    counts["dpy_total_smells"] = (
        counts["dpy_implementation_smells"]
        + counts["dpy_design_smells"]
        + counts["dpy_architecture_smells"]
    )
    return counts, smell_rows


def _dpy_module_class(entry: dict) -> str:
    """Combine Module + Class into a single module_class string for the detail CSV."""
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
# SECTION 4 — Per-project processing
# ============================================================

def process_pkl(
    pkl_path: str,
    work_root: str,
    config_path: str,
    dpy_bin_dir: Optional[str],
    refactored_dir: Optional[str],
) -> Optional[tuple[list[dict], list[dict]]]:
    """
    Process one project .pkl file.

    For each turn, runs both PyExamine and DPy (with caching).
    For the refactored snapshot (if --refactored_dir provided), same tools.
    Computes deltas vs baseline (first Coding turn) and vs post-review
    (last CodeReviewModification turn) for both tools.

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

    # Baseline = first Coding turn; post-review = last CodeReviewModification
    baseline_counts_pe   = None   # pyexamine
    postreview_counts_pe = None
    baseline_counts_dpy  = None   # dpy
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
            # ── PyExamine ────────────────────────────────────────────────────
            pe_counts, pe_smells = run_pyexamine(snap_src, report_stem, config_path)
            print(f"    [pyexamine] structural={pe_counts['structural_smells']}  "
                  f"code={pe_counts['code_smells']}  "
                  f"architectural={pe_counts['architectural_smells']}  "
                  f"total={pe_counts['total_smells']}")

            # ── DPy ──────────────────────────────────────────────────────────
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

        # Track baseline and post-review
        if phase == "Coding":
            if baseline_counts_pe  is None: baseline_counts_pe  = pe_counts
            if baseline_counts_dpy is None: baseline_counts_dpy = dpy_counts
        if phase == "CodeReviewModification":
            postreview_counts_pe  = pe_counts   # last one wins
            postreview_counts_dpy = dpy_counts

        turn_rows.append({
            "project":              project_name,
            "turn_index":           turn_index,
            "phase":                phase,
            "role":                 role,
            "interlocutor":         interlocutor,
            "timestamp":            timestamp,
            "py_files":             py_file_count,
            "code_lines":           code_lines,
            # PyExamine counts
            "structural_smells":    pe_counts["structural_smells"],
            "code_smells":          pe_counts["code_smells"],
            "architectural_smells": pe_counts["architectural_smells"],
            "total_smells":         pe_counts["total_smells"],
            # DPy counts
            "dpy_implementation_smells": dpy_counts["dpy_implementation_smells"],
            "dpy_design_smells":         dpy_counts["dpy_design_smells"],
            "dpy_architecture_smells":   dpy_counts["dpy_architecture_smells"],
            "dpy_total_smells":          dpy_counts["dpy_total_smells"],
            # Tokens / cost
            "tokens_prompt":        turn.get("tokens_prompt",     0) or 0,
            "tokens_completion":    turn.get("tokens_completion",  0) or 0,
            "tokens_reasoning":     turn.get("tokens_reasoning",   0) or 0,
            "tokens_total":         turn.get("tokens_total",       0) or 0,
            "cost_usd":             turn.get("cost_usd",         0.0) or 0.0,
            # Refactored columns — back-filled after refactored analysis below
            "refactored_py_files":                          None,
            "refactored_structural_smells":                 None,
            "refactored_code_smells":                       None,
            "refactored_architectural_smells":              None,
            "refactored_total_smells":                      None,
            "delta_ref_vs_baseline_structural":             None,
            "delta_ref_vs_baseline_code":                   None,
            "delta_ref_vs_baseline_architectural":          None,
            "delta_ref_vs_baseline_total":                  None,
            "delta_ref_vs_postreview_structural":           None,
            "delta_ref_vs_postreview_code":                 None,
            "delta_ref_vs_postreview_architectural":        None,
            "delta_ref_vs_postreview_total":                None,
            "refactored_dpy_implementation_smells":         None,
            "refactored_dpy_design_smells":                 None,
            "refactored_dpy_architecture_smells":           None,
            "refactored_dpy_total_smells":                  None,
            "delta_ref_vs_baseline_dpy_implementation":     None,
            "delta_ref_vs_baseline_dpy_design":             None,
            "delta_ref_vs_baseline_dpy_architecture":       None,
            "delta_ref_vs_baseline_dpy_total":              None,
            "delta_ref_vs_postreview_dpy_implementation":   None,
            "delta_ref_vs_postreview_dpy_design":           None,
            "delta_ref_vs_postreview_dpy_architecture":     None,
            "delta_ref_vs_postreview_dpy_total":            None,
        })

        # Detail rows — tag each with its tool
        for smell in pe_smells:
            detail_rows.append({
                "project":    project_name,
                "turn_index": turn_index,
                "phase":      phase,
                "snapshot":   f"turn_{turn_index}",
                **smell,
            })
        for smell in dpy_smells:
            detail_rows.append({
                "project":    project_name,
                "turn_index": turn_index,
                "phase":      phase,
                "snapshot":   f"turn_{turn_index}",
                **smell,
            })

    # ── Refactored snapshot ───────────────────────────────────────────────────
    ref_pe_counts  = None
    ref_dpy_counts = None
    ref_py_files   = 0

    if refactored_dir:
        ref_src = os.path.join(refactored_dir, project_name)

        if not Path(ref_src).exists():
            print(f"  Refactored dir not found: {ref_src} — skipping refactored snapshot")
        else:
            ref_py_files = count_py_files_in_dir(ref_src)

            if ref_py_files == 0:
                print(f"  Refactored dir has no .py files — skipping")
                ref_pe_counts  = _empty_pyexamine_counts()
                ref_dpy_counts = _empty_dpy_counts()
            else:
                print(f"  Refactored snapshot ({ref_py_files} .py files)...")

                # PyExamine on refactored
                ref_pe_stem = os.path.join(work_dir, f"{project_name}_refactored_report")
                ref_pe_counts, ref_pe_smells = run_pyexamine(
                    ref_src, ref_pe_stem, config_path
                )
                print(f"    [pyexamine] structural={ref_pe_counts['structural_smells']}  "
                      f"code={ref_pe_counts['code_smells']}  "
                      f"architectural={ref_pe_counts['architectural_smells']}  "
                      f"total={ref_pe_counts['total_smells']}")

                for smell in ref_pe_smells:
                    detail_rows.append({
                        "project":    project_name,
                        "turn_index": None,
                        "phase":      "Refactored",
                        "snapshot":   "refactored",
                        **smell,
                    })

                # DPy on refactored
                if dpy_bin_dir:
                    ref_dpy_out = os.path.join(work_dir, f"{project_name}_refactored_dpy_output")
                    ref_dpy_counts, ref_dpy_smells = run_dpy(
                        ref_src, ref_dpy_out, dpy_bin_dir
                    )
                    print(f"    [dpy]       implementation={ref_dpy_counts['dpy_implementation_smells']}  "
                          f"design={ref_dpy_counts['dpy_design_smells']}  "
                          f"architecture={ref_dpy_counts['dpy_architecture_smells']}  "
                          f"total={ref_dpy_counts['dpy_total_smells']}")

                    for smell in ref_dpy_smells:
                        detail_rows.append({
                            "project":    project_name,
                            "turn_index": None,
                            "phase":      "Refactored",
                            "snapshot":   "refactored",
                            **smell,
                        })
                else:
                    ref_dpy_counts = _empty_dpy_counts()

    # ── Back-fill refactored columns into every turn row ─────────────────────
    def _delta(ref_val, base_val):
        if base_val is None or ref_val is None:
            return None
        return ref_val - base_val

    if ref_pe_counts is not None or ref_dpy_counts is not None:
        for row in turn_rows:
            # PyExamine refactored
            if ref_pe_counts is not None:
                row["refactored_py_files"]               = ref_py_files
                row["refactored_structural_smells"]      = ref_pe_counts["structural_smells"]
                row["refactored_code_smells"]            = ref_pe_counts["code_smells"]
                row["refactored_architectural_smells"]   = ref_pe_counts["architectural_smells"]
                row["refactored_total_smells"]           = ref_pe_counts["total_smells"]

                b = baseline_counts_pe
                row["delta_ref_vs_baseline_structural"]    = _delta(ref_pe_counts["structural_smells"],    b["structural_smells"])    if b else None
                row["delta_ref_vs_baseline_code"]          = _delta(ref_pe_counts["code_smells"],          b["code_smells"])          if b else None
                row["delta_ref_vs_baseline_architectural"] = _delta(ref_pe_counts["architectural_smells"], b["architectural_smells"]) if b else None
                row["delta_ref_vs_baseline_total"]         = _delta(ref_pe_counts["total_smells"],         b["total_smells"])         if b else None

                p = postreview_counts_pe
                row["delta_ref_vs_postreview_structural"]    = _delta(ref_pe_counts["structural_smells"],    p["structural_smells"])    if p else None
                row["delta_ref_vs_postreview_code"]          = _delta(ref_pe_counts["code_smells"],          p["code_smells"])          if p else None
                row["delta_ref_vs_postreview_architectural"] = _delta(ref_pe_counts["architectural_smells"], p["architectural_smells"]) if p else None
                row["delta_ref_vs_postreview_total"]         = _delta(ref_pe_counts["total_smells"],         p["total_smells"])         if p else None

            # DPy refactored
            if ref_dpy_counts is not None:
                row["refactored_dpy_implementation_smells"] = ref_dpy_counts["dpy_implementation_smells"]
                row["refactored_dpy_design_smells"]         = ref_dpy_counts["dpy_design_smells"]
                row["refactored_dpy_architecture_smells"]   = ref_dpy_counts["dpy_architecture_smells"]
                row["refactored_dpy_total_smells"]          = ref_dpy_counts["dpy_total_smells"]

                b = baseline_counts_dpy
                row["delta_ref_vs_baseline_dpy_implementation"] = _delta(ref_dpy_counts["dpy_implementation_smells"], b["dpy_implementation_smells"]) if b else None
                row["delta_ref_vs_baseline_dpy_design"]         = _delta(ref_dpy_counts["dpy_design_smells"],         b["dpy_design_smells"])         if b else None
                row["delta_ref_vs_baseline_dpy_architecture"]   = _delta(ref_dpy_counts["dpy_architecture_smells"],   b["dpy_architecture_smells"])   if b else None
                row["delta_ref_vs_baseline_dpy_total"]          = _delta(ref_dpy_counts["dpy_total_smells"],          b["dpy_total_smells"])          if b else None

                p = postreview_counts_dpy
                row["delta_ref_vs_postreview_dpy_implementation"] = _delta(ref_dpy_counts["dpy_implementation_smells"], p["dpy_implementation_smells"]) if p else None
                row["delta_ref_vs_postreview_dpy_design"]         = _delta(ref_dpy_counts["dpy_design_smells"],         p["dpy_design_smells"])         if p else None
                row["delta_ref_vs_postreview_dpy_architecture"]   = _delta(ref_dpy_counts["dpy_architecture_smells"],   p["dpy_architecture_smells"])   if p else None
                row["delta_ref_vs_postreview_dpy_total"]          = _delta(ref_dpy_counts["dpy_total_smells"],          p["dpy_total_smells"])          if p else None

    print(f"  Done — {len(turn_rows)} turns, {len(detail_rows)} smell instances")
    return turn_rows, detail_rows


# ============================================================
# SECTION 5 — Main
# ============================================================

TURN_FIELDS = [
    "project", "turn_index", "phase", "role", "interlocutor", "timestamp",
    "py_files", "code_lines",
    # PyExamine
    "structural_smells", "code_smells", "architectural_smells", "total_smells",
    # DPy
    "dpy_implementation_smells", "dpy_design_smells",
    "dpy_architecture_smells", "dpy_total_smells",
    # Tokens / cost
    "tokens_prompt", "tokens_completion", "tokens_reasoning",
    "tokens_total", "cost_usd",
    # Refactored — PyExamine
    "refactored_py_files",
    "refactored_structural_smells", "refactored_code_smells",
    "refactored_architectural_smells", "refactored_total_smells",
    "delta_ref_vs_baseline_structural", "delta_ref_vs_baseline_code",
    "delta_ref_vs_baseline_architectural", "delta_ref_vs_baseline_total",
    "delta_ref_vs_postreview_structural", "delta_ref_vs_postreview_code",
    "delta_ref_vs_postreview_architectural", "delta_ref_vs_postreview_total",
    # Refactored — DPy
    "refactored_dpy_implementation_smells", "refactored_dpy_design_smells",
    "refactored_dpy_architecture_smells", "refactored_dpy_total_smells",
    "delta_ref_vs_baseline_dpy_implementation", "delta_ref_vs_baseline_dpy_design",
    "delta_ref_vs_baseline_dpy_architecture", "delta_ref_vs_baseline_dpy_total",
    "delta_ref_vs_postreview_dpy_implementation", "delta_ref_vs_postreview_dpy_design",
    "delta_ref_vs_postreview_dpy_architecture", "delta_ref_vs_postreview_dpy_total",
]

DETAIL_FIELDS = [
    "project", "turn_index", "phase", "snapshot",
    "tool", "type", "name", "description", "file",
    "module_class", "line_number", "severity",
]


def main():
    parser = argparse.ArgumentParser(
        description="RQ3 v3: Per-turn + refactored smell analysis (PyExamine + DPy)"
    )
    parser.add_argument("--pkl_dir",        required=True,
                        help="Directory containing .pkl project files")
    parser.add_argument("--config",         required=True,
                        help="Path to code_quality_config.yaml")
    parser.add_argument("--dpy_dir",        default=None,
                        help="Path to the DPy/ folder containing the DPy binary "
                             "(e.g. ./DPy).  Omit to skip DPy analysis.")
    parser.add_argument("--output",         default="rq3_results.csv",
                        help="Output CSV path (default: rq3_results.csv)")
    parser.add_argument("--work_dir",       default="rq3_workdir",
                        help="Working dir for snapshots/reports (default: rq3_workdir)")
    parser.add_argument("--refactored_dir", default=None,
                        help="Root dir containing refactored_code/project_name/ folders")
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

    pkl_files = sorted(Path(args.pkl_dir).glob("*.pkl"))
    if not pkl_files:
        print(f"No .pkl files found in: {args.pkl_dir}")
        sys.exit(1)

    print(f"Found {len(pkl_files)} project(s)")
    if args.refactored_dir:
        print(f"Refactored dir : {args.refactored_dir}")
    else:
        print("No --refactored_dir provided — refactored columns will be empty")

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
            args.refactored_dir,
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

    # ── Turn-level CSV ────────────────────────────────────────────────────────
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TURN_FIELDS)
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