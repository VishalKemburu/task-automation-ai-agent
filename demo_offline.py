"""
demo_offline.py
----------------
A rule-based stand-in for agent.py that needs no API key. It demonstrates the
same plan -> call tool -> observe -> respond loop using simple keyword
matching instead of an LLM to decide which tool(s) to call. Useful for
running/demoing the project offline or in an interview without internet
access to an LLM API.
"""

import re
from tools import calculator, knowledge_search, file_lookup

PERCENT_OF_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
MATH_PATTERN = re.compile(r"[-+*/().\d\s]{3,}")


def plan_subtasks(request: str):
    """Very simple planner: decide which tool(s) this request needs."""
    subtasks = []
    lower = request.lower()

    # "X% of Y" phrasing -> convert to an arithmetic expression
    percent_match = PERCENT_OF_PATTERN.search(request)
    if percent_match:
        pct, base = percent_match.groups()
        subtasks.append(("calculator", {"expression": f"({pct}/100)*{base}"}))
    else:
        # Does the request contain a math expression?
        math_match = MATH_PATTERN.search(request)
        if math_match and any(ch.isdigit() for ch in math_match.group()) and any(op in math_match.group() for op in "+-*/"):
            subtasks.append(("calculator", {"expression": math_match.group().strip()}))

    # Does it ask to read a file?
    file_match = re.search(r"file (\S+)", lower)
    if file_match:
        subtasks.append(("file_lookup", {"filename": file_match.group(1)}))

    # Otherwise, treat it as a knowledge lookup
    if not subtasks:
        subtasks.append(("knowledge_search", {"query": request}))

    return subtasks


def run_agent_offline(user_request: str, verbose: bool = True) -> str:
    subtasks = plan_subtasks(user_request)
    tool_funcs = {
        "calculator": calculator,
        "knowledge_search": knowledge_search,
        "file_lookup": file_lookup,
    }

    results = []
    for name, args in subtasks:
        if verbose:
            print(f"[agent] Sub-task -> calling '{name}' with {args}")
        result = tool_funcs[name](**args)
        results.append((name, result))

    # Combine results into a single response
    lines = [f"- {name}: {result}" for name, result in results]
    return "Combined result:\n" + "\n".join(lines)


if __name__ == "__main__":
    print("=== Task Automation AI Agent (offline demo mode) ===")
    print("Try things like:")
    print("  - 'What is (12 + 8) * 3?'")
    print("  - 'Tell me about agentic ai'")
    print("  - 'Read file notes.txt'\n")

    while True:
        try:
            request = input("Enter a task (or 'quit'): ").strip()
        except EOFError:
            break
        if request.lower() in {"quit", "exit"}:
            break
        if not request:
            continue
        print(run_agent_offline(request))
        print()
