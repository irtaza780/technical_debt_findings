import os
import glob
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

# ─────────────────────────────────────────────
# CONFIG — paste your Groq API key here
# ─────────────────────────────────────────────
GROQ_API_KEY = "INSERT KEY HERE"
PROJECT_FOLDER = "./rq3_workdir/BudgetTracker_DefaultOrganization_20250909155642/turn_06_src"  # path to the folder you want to refactor
# ─────────────────────────────────────────────


# ── LLM Setup ────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0,
)


# ── Tools ─────────────────────────────────────

@tool
def list_python_files(folder: str) -> str:
    """Lists all Python files in the given project folder recursively."""
    files = glob.glob(os.path.join(folder, "**/*.py"), recursive=True)
    if not files:
        return f"No Python files found in '{folder}'."
    return "\n".join(files)


@tool
def read_file(filepath: str) -> str:
    """Reads and returns the content of a Python file."""
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    with open(filepath, "r") as f:
        return f.read()


@tool
def detect_code_smells(code: str) -> str:
    """
    Analyzes Python code and returns a list of detected code smells
    such as long functions, duplicate logic, magic numbers, missing error
    handling, overly complex conditionals, and unused variables.
    """
    smells = []
    lines = code.split("\n")

    # Long functions (more than 40 lines)
    in_function = False
    func_start = 0
    func_name = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("def "):
            if in_function and (i - func_start) > 40:
                smells.append(
                    f"⚠️  Long function '{func_name}' "
                    f"({i - func_start} lines) starting at line {func_start + 1}"
                )
            in_function = True
            func_start = i
            func_name = stripped.split("(")[0].replace("def ", "")

    # Magic numbers
    import re
    magic_numbers = re.findall(r'\b(?<!\.)\d{2,}\b', code)
    if magic_numbers:
        unique = list(set(magic_numbers))[:5]
        smells.append(f"⚠️  Possible magic numbers found: {unique}")

    # Missing docstrings
    func_lines = [l for l in lines if l.strip().startswith("def ")]
    for fl in func_lines:
        idx = lines.index(fl)
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        if not next_line.startswith('"""') and not next_line.startswith("'''"):
            fname = fl.strip().split("(")[0].replace("def ", "")
            smells.append(f"⚠️  Function '{fname}' is missing a docstring")

    # Bare excepts
    if "except:" in code:
        smells.append("⚠️  Bare 'except:' clause found — too broad, catches everything including SystemExit")

    # Print statements (should use logging in production)
    print_count = code.count("print(")
    if print_count > 3:
        smells.append(f"⚠️  {print_count} print() statements found — consider using logging instead")

    if not smells:
        return "✅ No obvious code smells detected."
    return "\n".join(smells)


@tool
def refactor_and_add_docs(filepath: str) -> str:
    """
    Reads a Python file, then uses the LLM to rewrite it with:
    - Refactored functions (cleaner, shorter, DRY)
    - Docstrings added to all functions and classes
    - Inline comments for complex logic
    Returns the refactored code as a string.
    """
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"

    with open(filepath, "r") as f:
        original_code = f.read()

    refactor_prompt = f"""You are an expert Python developer specializing in code quality.

Refactor the following Python code to:
1. Reduce technical debt
2. Apply DRY (Don't Repeat Yourself) principles
3. Break down long functions into smaller focused ones
4. Add clear docstrings to every function and class
5. Add inline comments for any complex or non-obvious logic
6. Replace magic numbers with named constants
7. Use proper exception handling instead of bare excepts
8. Replace print() with logging where appropriate

Return ONLY the refactored Python code. No explanations, no markdown, just clean Python.

Original code:
{original_code}
"""

    response = llm.invoke(refactor_prompt)
    return response.content


@tool
def save_refactored_file(filepath: str, refactored_code: str) -> str:
    """
    Saves the refactored code to a new file with '_refactored' added to the filename.
    For example: my_module.py → my_module_refactored.py
    """
    base, ext = os.path.splitext(filepath)
    new_path = f"{base}_refactored{ext}"
    with open(new_path, "w") as f:
        f.write(refactored_code)
    return f"✅ Saved refactored file to: {new_path}"


tools = [list_python_files, read_file, detect_code_smells, refactor_and_add_docs, save_refactored_file]


# ── Prompt ────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior Python engineer specializing in code quality and technical debt reduction.

Your job is to refactor a Python project folder. Follow these steps for EACH file:
1. Use list_python_files to find all .py files in the project folder
2. For each file:
   a. Use read_file to read its contents
   b. Use detect_code_smells to identify issues
   c. Use refactor_and_add_docs to generate a clean refactored version
   d. Use save_refactored_file to save the result
3. After processing all files, give a summary of:
   - How many files were processed
   - The main issues found across the project
   - What was improved

Be thorough. Process every single file you find."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# ── Agent ─────────────────────────────────────
agent_executor = create_react_agent(llm, tools)

# ── Run ───────────────────────────────────────
if __name__ == "__main__":
    print("\n🤖 Refactoring Agent Starting...\n")
    result = agent_executor.invoke({
        "messages": [("human", f"Please scan and refactor all Python files in the folder: {PROJECT_FOLDER}")]
    })
    print("\n─────────────────────────────────")
    print("📋 FINAL SUMMARY:")
    print(result["messages"][-1].content)
