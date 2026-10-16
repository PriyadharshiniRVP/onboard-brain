import os
import json
from openai import OpenAI
from dotenv import load_dotenv

try:
    from src.tools import TOOLS, TOOL_FUNCTIONS
except ImportError:
    from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are Onboarding Brain, an assistant for new employees at Acme Corp.

You have a set of tools that query the company's knowledge graph. Always use a tool to find information — never answer from your own knowledge.

IMPORTANT RULES:
1. Before answering any question about a process or document, you MUST call is_doc_stale on the relevant document to check if it's outdated.
2. When is_doc_stale returns results, look for the CLOSED ticket — that's the one that made the change. Open tickets are just flags that the doc is outdated.
3. If the doc is stale, tell the user:
   - That the doc is outdated
   - What the newer ticket changed it to
   - The person who made the change (the author of the CLOSED ticket)
4. Never recommend a process based on a stale document. Always prefer the newer information from the closed ticket.

Be concise. Three or four sentences is enough."""


def run_agent(question: str, verbose: bool = True):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    # First call: let the model pick a tool
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    message = response.choices[0].message
    messages.append(message)

    if not message.tool_calls:
        return {"answer": message.content, "path": []}

    path = []
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        if verbose:
            print(f"[agent] calling {tool_name}({tool_args})")

        func = TOOL_FUNCTIONS.get(tool_name)
        if not func:
            result = {"error": f"unknown tool {tool_name}"}
        else:
            try:
                result = func(**tool_args)
            except Exception as e:
                result = {"error": str(e)}

        path.append({"tool": tool_name, "args": tool_args, "result": result})

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": json.dumps(result, default=str)
        })

    # Second call: model writes the final answer
    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )

    answer = final_response.choices[0].message.content
    return {"answer": answer, "path": path}


if __name__ == "__main__":
    q = "How do I deploy to production?"
    print(f"\nQuestion: {q}\n")
    result = run_agent(q)
    print(f"\nAnswer: {result['answer']}")
    print(f"\nPath taken:")
    for step in result["path"]:
        print(f"  → {step['tool']}({step['args']})")
        for row in step["result"]:
            print(f"      {row}")