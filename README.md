# Agentic Debt Research Pipeline — RQ3

This pipeline analyses technical debt (code smells) introduced by multi-agent software systems (MAS), and evaluates whether a dedicated refactoring agent can mitigate it. It uses two smell detection tools — **PyExamine** and **DPy** — across per-turn snapshots and three independent refactoring runs (v1, v2, v3).

---

## Repository Layout

```
python_smells_detector/
├── pkls/                        # Input: one .pkl file per project
├── DPy/                         # DPy binary directory
│   ├── DPy                      # The DPy executable
├── refactored_code/             # Refactored output v1
├── refactored_code_v2/          # Refactored output v2
├── refactored_code_v3/          # Refactored output v3
├── rq3_workdir/                 # Working directory: per-turn snapshots and reports
├── code_quality_config.yaml     # PyExamine configuration
├── rq3_pipeline.py              # Main smell analysis pipeline
├── refactor_agent.py            # Refactoring agent (re-run to regenerate v2 and v3)
├── agentic_debt_pipeline.py     # Standalone RQ1 pipeline (PyExamine only, no refactoring)
├── rq3_analysis_v3.ipynb        # Analysis notebook (RQ1 + RQ3)
├── .env                         # API key (not committed)
└── venv/                        # Python virtual environment
```

---

## Prerequisites

### 1. Python virtual environment

The virtual environment must be active whenever you run any pipeline script, because PyExamine's `analyze_code_quality` command is installed inside it.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. PyExamine — installation

PyExamine is the primary smell detection tool. Install it from source into the venv.

```bash
# Clone the repository
git clone https://github.com/KarthikShivasankar/python_smells_detector.git
cd python_smells_detector

# Install in editable mode (inside your active venv)
pip install -e .
```

Verify the install worked:

```bash
analyze_code_quality --help
```

The `code_quality_config.yaml` from that repository is also required by the pipeline. It is already included in this repo root — if you need to reset it to defaults, copy it from the cloned PyExamine repo.

### 3. DPy binary

The `DPy` binary must be present at `./DPy/DPy` and be executable:

```bash
chmod +x ./DPy/DPy
```

DPy is a compiled binary (trial licence). It must be run from inside its own directory — the pipeline handles this automatically.

### 4. Environment variables

Create a `.env` file in the project root. This is only needed if you re-run the refactoring agent:

```
ANTHROPIC_API_KEY=your_key_here
```

Install the Python dependencies for the refactoring agent:

```bash
pip install anthropic langchain-anthropic python-dotenv
```

---

## Step 1 — Run the smell analysis pipeline

This runs both PyExamine and DPy on every per-turn snapshot and on all three refactored versions (v1, v2, v3) already present in the repo.

```bash
source venv/bin/activate

python rq3_pipeline.py \
    --pkl_dir         ./pkls \
    --config          ./code_quality_config.yaml \
    --dpy_dir         ./DPy \
    --output          rq3_results.csv \
    --work_dir        rq3_workdir \
    --refactored_dirs ./refactored_code ./refactored_code_v2 ./refactored_code_v3
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--pkl_dir` | Yes | Directory containing `.pkl` project files |
| `--config` | Yes | Path to `code_quality_config.yaml` |
| `--dpy_dir` | No | Path to the `DPy/` folder containing the binary. Omit to skip DPy analysis |
| `--output` | No | Output CSV path (default: `rq3_results.csv`) |
| `--work_dir` | No | Working directory for snapshots and reports (default: `rq3_workdir`) |
| `--refactored_dirs` | No | One or more refactored code root directories, space-separated. Auto-labelled v1, v2, v3 in order |

### Output files

| File | Description |
|---|---|
| `rq3_results.csv` | One row per turn. Per-turn smell counts from both tools, plus v1/v2/v3 refactored counts and deltas |
| `rq3_results_smells_detail.csv` | One row per smell instance. Used for smell-name breakdowns in the notebook |

### Caching behaviour

The pipeline caches all intermediate results in `rq3_workdir/`. Re-runs are safe:
- PyExamine is skipped for any turn whose report CSV already exists
- DPy is skipped for any turn whose `_implementation_smells.json` already exists
- The same caching applies to each refactored version snapshot

Since `rq3_workdir/` is committed to the repo, running the pipeline for the first time will mostly hit cache and complete quickly.

---

## Step 2 — Run the analysis notebook

Open `rq3_analysis_v3.ipynb` in Google Colab or Jupyter and run cells in order. When prompted, upload:

1. `rq3_results.csv`
2. `rq3_results_smells_detail.csv`

### Notebook structure

| Section | Content |
|---|---|
| Setup (cells 1–3b) | Install dependencies, imports, load CSVs |
| **RQ1** | Smell accumulation trend, category composition, phase-level delta, interlocutor responsibility |
| **RQ3 — Code Reviewer** | Baseline vs post-review comparison, Wilcoxon test, Cliff's delta, trajectory analysis, heatmap |
| **RQ3 v2 — Refactoring Agent** | Three-version comparison, cross-version consistency, DPy analysis, summary table |

---

## Re-running the refactoring agent (optional)

The three refactored codebases (v1, v2, v3) are already committed to the repository. You only need to re-run the agent if you want to regenerate them — for example, to test a different prompt or model.

The agent calls Claude (claude-haiku-4-5) once per `.py` file and applies the following refactoring rules to each file independently:

- Apply DRY — eliminate duplicate logic
- Break down long functions (>40 lines) into smaller focused ones
- Add clear docstrings and inline comments for complex logic
- Replace magic numbers with named constants
- Replace bare `except` clauses with specific exception types
- Replace `print()` calls with proper logging
- Improve variable naming where unclear

> **Note:** v1 (`refactored_code/`) is treated as already complete and will not be regenerated. The agent only produces v2 and v3.

```bash
source venv/bin/activate
python refactor_agent.py
```

Each version reads from the same original last-turn snapshot in `rq3_workdir/` — the runs are fully independent, not chained. Caching is per-output-directory: if a project already has `.py` files in `refactored_code_v2/` it will be skipped. Delete the output directory to force a full re-run.

**Expected runtime:** 20–60 minutes for 30 projects, depending on file count and API rate limits. The agent handles rate limit errors automatically with retry logic.

---

## Output column reference

### Per-turn columns (PyExamine)

| Column | Description |
|---|---|
| `structural_smells` | High cyclomatic complexity, too many branches, deep inheritance, etc. |
| `code_smells` | Feature envy, divergent change, temporary field, shotgun surgery, etc. |
| `architectural_smells` | Improper API usage, orphan modules, cyclic dependencies, etc. |
| `total_smells` | Sum of the above three |

### Per-turn columns (DPy)

| Column | Description |
|---|---|
| `dpy_implementation_smells` | Long statements, complex methods, magic numbers, empty catch blocks |
| `dpy_design_smells` | Broken modularisation, multifaceted abstraction |
| `dpy_architecture_smells` | Architecture-level issues (often zero) |
| `dpy_total_smells` | Sum of the above three |

### Refactored version columns

For each version `vN` (v1, v2, v3) the following columns are added. The pattern applies to both PyExamine and DPy variants:

| Column | Description |
|---|---|
| `vN_refactored_total_smells` | Total smells in the refactored snapshot |
| `vN_delta_ref_vs_baseline_total` | Refactored minus baseline (negative = improvement) |
| `vN_delta_ref_vs_postreview_total` | Refactored minus post-review (negative = improvement) |

The same pattern applies for `_structural_`, `_code_`, `_architectural_`, and `_dpy_*` variants.

---

## Troubleshooting

**`analyze_code_quality` not found**
The venv is not active. Run `source venv/bin/activate` before running any script.

**`NotADirectoryError: [Errno 20] Not a directory: './DPy/DPy'`**
Pass the folder containing the binary, not the binary itself: `--dpy_dir ./DPy`, not `--dpy_dir ./DPy/DPy`.

**DPy parse errors in logs (SyntaxError)**
DPy logs parse errors for files with syntax issues and continues. These are warnings, not failures — the affected file is skipped and other files in the project are still analysed.

**Rate limit errors during refactoring**
The refactoring agent has built-in retry logic with automatic waits. If interrupted, re-run the script — already-completed projects are skipped automatically.

**Missing refactored columns in CSV**
Ensure all three directories are passed to `--refactored_dirs` and each contains at least one `.py` file per project. Projects with no `.py` files are skipped and their columns will be empty in the CSV.

**PyExamine config not found**
Make sure `code_quality_config.yaml` is in the project root. If missing, copy it from the [PyExamine repository](https://github.com/KarthikShivasankar/python_smells_detector).