"""
tools.py
--------
Defines the concrete tools the agent can call. Each tool is a plain Python
function plus a JSON-schema description (used for LLM function calling).
"""

import ast
import operator as op
import os
import re

# ---------------------------------------------------------------------------
# 1. Calculator tool — safe arithmetic evaluation (no eval()).
# ---------------------------------------------------------------------------
_ALLOWED_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod, ast.FloorDiv: op.floordiv,
}


def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression, e.g. '(12 + 8) * 3'."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# ---------------------------------------------------------------------------
# 2. Knowledge-base search tool — searches a small local FAQ dataset.
#    (Stands in for a real web-search tool without needing external API keys.)
# ---------------------------------------------------------------------------
_KNOWLEDGE_BASE = [
    {"topic": "python", "text": "Python is a high-level, interpreted programming language known for readable syntax."},
    {"topic": "sql", "text": "SQL (Structured Query Language) is used to query and manage data in relational databases."},
    {"topic": "agentic ai", "text": "An agentic AI system plans, calls tools, and takes multi-step actions to complete a goal, rather than just answering in one shot."},
    {"topic": "function calling", "text": "Function calling lets an LLM choose a predefined tool/function and its arguments, which the calling program then executes."},
    {"topic": "gitam", "text": "GITAM Institute of Technology and Management is a university in Visakhapatnam, Andhra Pradesh, India."},
    {"topic": "deloitte", "text": "Deloitte is a multinational professional services network offering audit, consulting, and analyst roles."},
    {"topic": "flytbase", "text": "FlytBase builds drone automation and autonomy software, including agentic AI systems for drone-in-a-box operations."},
]


_STOPWORDS = {"what", "is", "the", "a", "an", "tell", "me", "about", "of", "in", "on", "to", "for"}


def knowledge_search(query: str) -> str:
    """Search a small local knowledge base for a topic and return the best match."""
    clean_query = re.sub(r"[^\w\s]", " ", query.lower())
    words = [w for w in clean_query.split() if w not in _STOPWORDS]
    scored = []
    for entry in _KNOWLEDGE_BASE:
        text_words = set(re.sub(r"[^\w\s]", " ", entry["text"].lower()).split())
        topic_words = set(entry["topic"].split())
        score = sum(1 for w in words if w in text_words or w in topic_words)
        if score > 0:
            scored.append((score, entry))
    if not scored:
        return "No relevant results found in the knowledge base."
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]["text"]


# ---------------------------------------------------------------------------
# 3. File lookup tool — reads a file from the local ./data folder.
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def file_lookup(filename: str) -> str:
    """Read and return the contents of a file inside the local data/ folder."""
    safe_name = os.path.basename(filename)  # prevent path traversal
    path = os.path.join(DATA_DIR, safe_name)
    if not os.path.exists(path):
        available = os.listdir(DATA_DIR) if os.path.isdir(DATA_DIR) else []
        return f"File '{safe_name}' not found. Available files: {available}"
    with open(path, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Tool registry — used by both the real LLM agent and the offline demo agent.
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "knowledge_search": knowledge_search,
    "file_lookup": file_lookup,
}

# JSON-schema tool definitions in Anthropic's tool-use format.
TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression and return the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "A math expression, e.g. '(12 + 8) * 3'"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "knowledge_search",
        "description": "Search a small local knowledge base for information on a topic (python, sql, agentic ai, function calling, gitam, deloitte, flytbase).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic or question to search for"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "file_lookup",
        "description": "Read the contents of a file from the local data/ folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name of the file inside data/, e.g. 'notes.txt'"}
            },
            "required": ["filename"],
        },
    },
]
