"""
agent.py
--------
The agent's decision loop: send the user's request + available tools to the
LLM, execute whichever tool(s) it chooses, feed results back, and repeat
until the model gives a final answer (no more tool calls).

Requires an ANTHROPIC_API_KEY environment variable to actually call the LLM.
If no key is set, see demo_offline.py for a rule-based stand-in that shows
the same architecture without needing API access.
"""

import os
import json
import anthropic

from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = "claude-sonnet-4-5"
SYSTEM_PROMPT = (
    "You are a task automation agent. Break the user's request into sub-tasks "
    "as needed, and call the available tools to gather information or compute "
    "results. Once you have everything you need, give a single clear final "
    "answer that combines the tool results. Do not call a tool you don't need."
)


def run_agent(user_request: str, max_steps: int = 6, verbose: bool = True) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    messages = [{"role": "user", "content": user_request}]

    for step in range(max_steps):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Collect any tool calls the model made in this turn
        tool_calls = [block for block in response.content if block.type == "tool_use"]

        if not tool_calls:
            # No more tools needed -> final answer
            final_text = "".join(block.text for block in response.content if block.type == "text")
            if verbose:
                print(f"[step {step + 1}] Final answer.")
            return final_text

        # Record the assistant's turn (including its tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        # Execute each requested tool and build the tool_result messages
        tool_results = []
        for call in tool_calls:
            fn = TOOL_FUNCTIONS.get(call.name)
            if verbose:
                print(f"[step {step + 1}] Agent calls tool '{call.name}' with input {call.input}")
            try:
                result = fn(**call.input) if fn else f"Unknown tool: {call.name}"
            except Exception as e:
                result = f"Tool error: {e}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return "Max steps reached without a final answer."


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Run 'python3 demo_offline.py' instead for a "
              "no-API-key demo, or set the key and re-run this script.")
    else:
        request = input("Enter a task for the agent: ")
        answer = run_agent(request)
        print("\n=== Final Answer ===")
        print(answer)
