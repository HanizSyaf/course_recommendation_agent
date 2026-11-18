import json
import urllib.request
import urllib.error

BASE = "http://host.docker.internal:11434/api/chat"

MODELS = [
    "gemma4:12b-65k",
    "hermes3:8b-65k",
    "qwen3.5:4b-65k",
    "mistral-nemo:12b-65k",
    "llama3.1:8b-65k",
    "deepseek-r1:8b-65k",
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_id",
            "description": "Look up a user's internal ID by their display name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The user's display name."}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_order",
            "description": "Look up a user's latest order by their internal user ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The internal user ID."}
                },
                "required": ["user_id"],
            },
        },
    },
]


def chat(model, messages, tools, num_predict=200):
    body = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "options": {"num_predict": num_predict, "temperature": 0.0},
    }
    req = urllib.request.Request(
        BASE,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode("utf-8", "replace")[:500]}
    except Exception as e:
        return {"error": repr(e)}


def tool_call_calls(msg):
    """Return list of tool calls from an assistant message, or empty list."""
    if not isinstance(msg, dict):
        return []
    return msg.get("tool_calls", []) or []


def run_model(model):
    result = {"model": model, "step1_tool_calls": 0, "step2_tool_calls": 0,
              "repeated": False, "step1_calls_detail": [], "step2_calls_detail": [],
              "error": None, "step1_content": "", "step2_content": ""}

    # Step 1: ask a question that requires a chained lookup
    r1 = chat(model, [
        {"role": "user", "content": "What is the latest order for the user named Alice Rivera?"}
    ], TOOLS)

    if "error" in r1:
        result["error"] = r1["error"]
        return result

    msg1 = r1.get("message", {})
    result["step1_content"] = msg1.get("content", "") or ""
    calls1 = tool_call_calls(msg1)
    result["step1_tool_calls"] = len(calls1)
    result["step1_calls_detail"] = [c.get("function", {}).get("name") for c in calls1]

    if not calls1:
        # No tool call at all — cannot be repeated
        return result

    # Build tool result messages and call again (step 2)
    messages2 = [
        {"role": "user", "content": "What is the latest order for the user named Alice Rivera?"},
        msg1,
    ]
    for c in calls1:
        fn = c.get("function", {})
        name = fn.get("name")
        args = fn.get("arguments", {})
        # Fabricate deterministic results
        if name == "get_user_id":
            tool_result = "user_id: U-99421"
        elif name == "get_user_order":
            tool_result = "Order #55821: 2x Noise-Cancelling Headphones, shipped 2026-11-15."
        else:
            tool_result = "ok"
        messages2.append({
            "role": "tool",
            "content": tool_result,
            "tool_call_id": c.get("id", "call_1"),
            "name": name,
        })

    r2 = chat(model, messages2, TOOLS)
    if "error" in r2:
        result["error"] = r2["error"]
        return result

    msg2 = r2.get("message", {})
    result["step2_content"] = msg2.get("content", "") or ""
    calls2 = tool_call_calls(msg2)
    result["step2_tool_calls"] = len(calls2)
    result["step2_calls_detail"] = [c.get("function", {}).get("name") for c in calls2]
    result["repeated"] = len(calls2) > 0
    return result


if __name__ == "__main__":
    out = []
    for m in MODELS:
        out.append(run_model(m))
    print(json.dumps(out, indent=2))
