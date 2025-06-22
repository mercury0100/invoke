# Codename: Invoke

![logo](./img/invoke-spellbook-logo.png)

Invoke is a lightweight framework that connects LLMs with real-world APIs using natural language and structured tool calls.

![25-second demo](./img/demo.gif)

See the full demo [here](https://www.youtube.com/watch?v=CQISrRpyigs).

[![GitHub stars](https://img.shields.io/github/stars/mercury0100/invoke?style=social)](https://github.com/mercury0100/invoke/stargazers)


---

## 📦 Installation

```bash
pip install invoke-agent
```

---

## 🚀 Quickstart

```python
from langchain_openai import ChatOpenAI
from invoke_agent.agent import InvokeAgent

# Use GPT-4.1 for best results
llm = ChatOpenAI(model="gpt-4.1")  
# Pass built-in aliases, file paths, or URLs; or omit to auto-load agents_map.yaml
invoke = InvokeAgent(llm, agents=["google-calendar", "./custom/weather.json"])

while True:
    user_input = input("📝 You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    response = invoke.chat(user_input)
    print("\n🤖", response)
```

[Youtube tutorial](https://www.youtube.com/watch?v=DtAbD-3ZSi8)

---

## 🔗 LangChain Integration

For full control you can integrate with LangChain directly:

```python
from invoke_agent.core import api_executor
from invoke_agent.context import build_context
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Define your LLM
llm = ChatOpenAI(model="gpt-4.1")

# Build a prompt template
prompt = ChatPromptTemplate.from_messages([
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Create the agent
agent = create_tool_calling_agent(llm=llm, tools=[api_executor], prompt=prompt)
executor = AgentExecutor(agent=agent, tools=[api_executor], verbose=True)

# Invoke with context containing your integrations
result = executor.invoke({
    "input": "What's the weather in Paris?",
    "chat_history": build_context(agents=["open-meteo"])
})
print(result["output"])
```

---

## 🛠️ Features

- 🌐 Access any HTTP API using natural language.
- 🔑 Automatic OAuth and API key management.
- 🧩 Flexible integrations via JSON, or TXT definitions.
- 🤖 Works with any LangChain-compatible LLM (we recommend GPT-4.1).

---

## 📑 Defining Integrations

You can specify integrations via the `agents` parameter:

- **Built-in aliases:** e.g. `"google-calendar"`, `"open-meteo"`  
- **File paths or URLs:** direct references to `.json` or `.txt` definitions  
- **Explicit mappings:** `{ "my-calendar": "./calendar.json" }`

```python
# All valid:
invoke = InvokeAgent(llm, agents=[
  "google-calendar",
  "https://example.com/my_agents.txt",
  {"custom-weather": "./agents/weather.json"}
])

# Or omit to load './agents_map.yaml' if present:
invoke = InvokeAgent(llm)
```

---

## 📘 agents.json / agents.txt

- **agents.json** is a structured schema defining tool names, URLs, methods, parameters, headers, and auth.  
- **agents.txt** is the Markdown-rendered version produced by `render_agents_txt()`, used in the system prompt.

```json
{
  "agent": "gmail",
  "label": "Gmail API",
  "base_url": "https://www.googleapis.com",
  "auth": {"type": "oauth", "code": "i"},
  "endpoints": [ /* ... */ ]
}
```

---

## 🔐 Authorization

- **None**: no auth.  
- **api_key**: `api_key` (Locally-managed API key)  
- **oauth**: `oauth::i` (Invoke-managed OAuth flow)  

Override per-endpoint using `auth_code`. When specified, it **overrides** the top-level `auth`.

---

## ✅ Usage Patterns

- **Auto YAML**: omit `agents` to load `agents_map.yaml` if available.  
- **Explicit list**: pass aliases, file paths, or mappings.  
- **Custom context**: override system prompt via `context` argument.

## 📚 Invoke Documentation

Here’s how the pieces fit together:

```  
      ┌─────────┐        ┌─────────────┐
      │ auth.py │───────▶︎│   core.py   │
      └─────────┘        └──────┬──────┘
                                │
                                ▼
      ┌───────────┐      ┌─────────────┐
      │context.py │─────▶︎│   agent.py  │
      └───────────┘      └─────────────┘         
           ▲                                      
           │                                      
      ┌────────────┐     ┌─────────────┐ 
      │compile.py  │◀︎────┤ agents.json │
      └────────────┘     └─────────────┘
```

Each file plays a specific role:

| Module | Description |
|--------|-------------|
| [`agent.md`](./docs/agent.md) | How to instantiate and use the `InvokeAgent` |
| [`core.md`](./docs/core.md) | Core logic for API execution |
| [`io.md`](./docs/io.md) | Interface for prompts, logs, and OAuth code entry |
| [`context.md`](./docs/context.md) | Builds runtime context using `agents.json` and templates |
| [`compile.md`](./docs/compile.md) | Converts `agents.json` into readable `agents.txt` |
| [`auth.md`](./docs/auth.md) | Guide to adding custom OAuth logic (e.g. Flask server) |
| [`agents_json.md`](./docs/agents_json.md) | Full schema spec for `agents.json`, with examples |

---

## 🚀 Getting Started

Jump right in with [example notebooks](./notebooks) to run your first agent with OpenAI, Claude, or Mistral.

Want to integrate a new API? Head to [agents_json.md](./docs/agents_json.md), add your agents.json and follow the prompts.

Need OAuth? See [auth.md](./docs/auth.md) or override [`io.get_oauth_code()`](./io.md).

## ⚙️ Ready to deploy? Use Per-User Mode

```python
from invoke_agent.auth import set_current_user

# Set namespace before running queries:
set_current_user('current_user_id')
```

**All OAuthManager calls now use credentials under that user_id namespace, and will never prompt interactively.**

---

> ⚠️ **BETA SOFTWARE — NOT FOR PRODUCTION**
>
> This project is in **active development** and provided as-is, for **testing and evaluation purposes only**.
> Use at your own risk. The author is **not liable** for any bugs, breakage, data loss, security issues, or
> cosmic anomalies that may arise from using this code.

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Status: Beta](https://img.shields.io/badge/status-beta-yellow)