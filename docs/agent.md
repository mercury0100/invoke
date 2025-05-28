# `InvokeAgent`

The `InvokeAgent` class is the primary interface between your LLM and real-world APIs. It manages chat history, tools, and agent memory, turning natural-language queries into structured API calls via tool-calling agents.

---

## 📦 Import

```python
from invoke_agent.agent import InvokeAgent
```

---

## 🚀 Quickstart

```python
from langchain_openai import ChatOpenAI
from invoke_agent.agent import InvokeAgent

llm = ChatOpenAI(model="gpt-4o")
agent = InvokeAgent(llm, agents=["open-meteo"])

response = agent.chat("What's the weather in Berlin?")
print(response)
```

* **No `agents` arg**? If you have an `agents_map.yaml` in your working directory, it will be auto-loaded.
* **Pass explicit file paths or URLs** (no `{name: path}` needed):

  ```python
  agent = InvokeAgent(llm, agents=[
      "./custom/calendar.json",
      "https://example.com/my_agents.txt",
      "google-calendar"
  ])
  ```

---

## 🧠 Constructor

```python
InvokeAgent(
    llm: BaseChatModel,
    agents: Optional[Union[str, List[Union[str, dict]]]] = None,
    tools: Optional[List[BaseTool]] = None,
    context: Optional[str] = None,
    verbose: bool = False,
)
```

### Parameters

| Parameter | Description                                                              |
| --------- | ------------------------------------------------------------------------ |
| `llm`     | A LangChain-compatible chat model (e.g., `ChatOpenAI`, `ChatAnthropic`). |
| `agents`  |                                                                          |

* `None` (default): loads `agents_map.yaml` if present, otherwise no integrations.
* `str`: path to a YAML map file.
* `List[Union[str, dict]]`: each entry may be:

  * A built-in alias (`"google-calendar"`),
  * A bare file path or URL (infers name from JSON or filename),
  * An explicit mapping `{ "alias": "path_or_url" }`. |
    \| `tools`   | Optional extra tools (defaults to `[api_executor]`). |
    \| `context` | Optional custom system prompt; if omitted, uses the internal `DEFAULT_CONTEXT`. Integrations are still appended afterward. |
    \| `verbose` | Whether to log intermediate steps (context building, tool calls, etc.). |

---

## 🧩 How It Works

1. **Context Assembly**
   Calls `build_context()` with your `context` (or default) and `agents` list/YAML.
2. **Agent Wiring**
   Uses LangChain’s `create_tool_calling_agent` plus your tools (defaults to `api_executor`).
3. **Chat History**
   Maintains `SystemMessage`, `HumanMessage`, and `AIMessage` history for multi-turn coherence.
4. **Tool Execution**
   When the LLM emits a function call (`api_executor`), it performs the HTTP request and feeds back the result.

---

## 💬 Chat

```python
response = agent.chat("Book me a meeting at 2pm next Friday.")
```

Returns the model’s final answer (after any necessary API calls). Each call updates the internal history.

---

## 🛠️ Tool Injection

To add custom tools:

```python
from my_custom_tools import my_tool

agent = InvokeAgent(
    llm,
    agents=["open-meteo"],
    tools=[api_executor, my_tool]
)
```

---
