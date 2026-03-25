import os
import glob
import re
import time
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
RQ3_WORKDIR       = "./rq3_workdir"
OUTPUT_DIR        = "./refactored_code"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")
# ─────────────────────────────────────────────


# ── LLM Setup ────────────────────────────────
llm = ChatAnthropic(
    model="claude-haiku-4-5",    # cheapest + fastest, still great for refactoring
    api_key=ANTHROPIC_API_KEY,
    temperature=0,
    max_tokens=4096,
)


# ─────────────────────────────────────────────
# RATE LIMIT HELPER
# ─────────────────────────────────────────────

def parse_wait_seconds(error_message: str) -> int:
    hours   = re.search(r'(\d+)h',      error_message)
    minutes = re.search(r'(\d+)m(?!s)', error_message)
    seconds = re.search(r'([\d.]+)s',   error_message)
    millis  = re.search(r'(\d+)ms',     error_message)

    total = 0
    if hours:   total += int(hours.group(1)) * 3600
    if minutes: total += int(minutes.group(1)) * 60
    if seconds: total += float(seconds.group(1))
    if millis and not seconds: total += int(millis.group(1)) / 1000

    return max(int(total) + 10, 30) if total > 0 else 30


def refactor_with_retry(code: str, max_retries: int = 5) -> str:
    """Call Claude directly — no agent, no tools, just one LLM call per file."""
    prompt = f"""You are an expert Python developer specializing in code quality.

Refactor the following Python code to:
1. Apply DRY — eliminate duplicate logic
2. Break down long functions (>40 lines) into smaller focused ones
3. Add clear docstrings to every function and class
4. Add inline comments for complex logic
5. Replace magic numbers with named constants at the top of the file
6. Replace bare except clauses with specific exception types
7. Replace print() with proper logging
8. Improve variable naming where unclear

IMPORTANT: Return ONLY the refactored Python code. No explanations, no markdown fences, no preamble. Just valid Python.

Original code:
{code}
"""
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err.lower() or "overloaded" in err.lower():
                wait = parse_wait_seconds(err)
                print(f"   ⏳ Rate limit, waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                for remaining in range(wait, 0, -10):
                    print(f"   ⏰ Resuming in {remaining}s...", end="\r")
                    time.sleep(min(10, remaining))
                print("   ✅ Resuming.                    ")
            else:
                raise e
    return None


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_all_projects(workdir: str) -> list[str]:
    return [
        os.path.join(workdir, d)
        for d in sorted(os.listdir(workdir))
        if os.path.isdir(os.path.join(workdir, d))
    ]


def get_last_turn_folder(project_path: str) -> str | None:
    turn_folders = [
        d for d in os.listdir(project_path)
        if os.path.isdir(os.path.join(project_path, d))
        and d.startswith("turn_")
        and d.endswith("_src")
    ]
    if not turn_folders:
        return None
    turn_folders.sort(key=lambda x: int(x.split("_")[1]))
    return os.path.join(project_path, turn_folders[-1])


def already_refactored(project_name: str, output_dir: str) -> bool:
    """Only skip if output folder exists AND has actual .py files in it."""
    project_out = os.path.join(output_dir, project_name)
    if not os.path.isdir(project_out):
        return False
    py_files = glob.glob(os.path.join(project_out, "**/*.py"), recursive=True)
    return len(py_files) > 0


def get_relative_output_path(source_root: str, filepath: str, output_dir: str) -> str:
    """
    Maps source file to output path preserving relative structure.
    e.g. ./rq3_workdir/Game/turn_04_src/utils/helpers.py
      -> ./refactored_code/Game/utils/helpers.py
    """
    rel = os.path.relpath(filepath, source_root)
    return os.path.join(output_dir, rel)


# ─────────────────────────────────────────────
# MAIN RUNNER — pure Python loop, no agent
# ─────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    projects  = get_all_projects(RQ3_WORKDIR)
    print(f"\n🔍 Found {len(projects)} projects in {RQ3_WORKDIR}\n")

    skipped   = []
    processed = []

    for project_path in projects:
        project_name = os.path.basename(project_path)

        # ── Skip if already done ──
        if already_refactored(project_name, OUTPUT_DIR):
            print(f"⏭️  Skipping '{project_name}' — already refactored.")
            skipped.append(project_name)
            continue

        # ── Find last turn ──
        last_turn = get_last_turn_folder(project_path)
        if not last_turn:
            print(f"⚠️  No turn_XX_src in '{project_name}' — skipping.")
            skipped.append(project_name)
            continue

        # ── Find all .py files ──
        py_files = glob.glob(os.path.join(last_turn, "**/*.py"), recursive=True)
        py_files = [f for f in py_files if os.path.isfile(f)]

        if not py_files:
            print(f"⚠️  No .py files in '{project_name}' last turn — skipping.")
            skipped.append(project_name)
            continue

        output_project_dir = os.path.join(OUTPUT_DIR, project_name)
        turn_name = os.path.basename(last_turn)

        print(f"\n🤖 {project_name}")
        print(f"   Turn   : {turn_name}")
        print(f"   Files  : {len(py_files)}")

        project_ok = True

        for filepath in py_files:
            filename = os.path.relpath(filepath, last_turn)
            print(f"   📄 {filename} ... ", end="", flush=True)

            # Read
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                original_code = f.read()

            if not original_code.strip():
                print("empty, skipped.")
                continue

            # Refactor (1 LLM call per file)
            refactored = refactor_with_retry(original_code)

            if refactored is None:
                print("❌ failed after retries.")
                project_ok = False
                break

            # Save
            dest = get_relative_output_path(last_turn, filepath, output_project_dir)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(refactored)

            print("✅")

        if project_ok:
            processed.append(project_name)
        else:
            # Clean up incomplete output so it reruns next time
            import shutil
            out = os.path.join(OUTPUT_DIR, project_name)
            if os.path.isdir(out):
                shutil.rmtree(out)
                print(f"   🧹 Cleaned up incomplete output for '{project_name}'")
            skipped.append(project_name)

    # ── Final summary ──
    print("\n" + "═" * 50)
    print("✅ ALL DONE")
    print(f"   Processed : {len(processed)} projects")
    print(f"   Skipped   : {len(skipped)} projects")
    if skipped:
        print(f"   Skipped   : {skipped}")
    print(f"\n📁 Output: {os.path.abspath(OUTPUT_DIR)}")
    print("═" * 50)