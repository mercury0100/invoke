# 🧠 `context.py` — Dynamic Context Builder for Invoke Agents

This module assembles the full system prompt for your Invoke agent by embedding:

- 📅 Current date & time  
- 🧭 Framework instructions & base prompt  
- 🤖 Tool definitions from built-in, local or remote `agents.txt` / `agents.json`  

It supports:  
- **Built-in aliases** (e.g. `"google-maps"`)  
- **Bare file paths or URLs** (auto-infers name from JSON metadata or filename)  
- **Explicit `{name: path}` mappings**  
- **Optional `agents_map.yaml`** (only loaded when you don’t supply an `agents` list)

---

## 📦 Import

```python
from invoke_agent.context import build_context, load_agents_map
````

---

## 🧠 `build_context()`

```python
def build_context(
    base_prompt: str = '',
    agents: Optional[Union[str, List[Union[str, dict]]]] = None
) -> str
```

Constructs the agent’s **system prompt** by:

1. Using `base_prompt` (if provided), otherwise the built-in `DEFAULT_CONTEXT` block.
2. Loading any integrations via `load_agents_map(source=agents)`.
3. Appending each integration under a `# {name}` header.

### 🔧 Usage

* **Explicit list**

  ```python
  ctx = build_context(
      base_prompt="You're my assistant.",
      agents=["google-maps", "./my_weather.json"]
  )
  ```
* **Auto-load `agents_map.yaml`**

  ```python
  # If no `agents` arg is given and you have an `agents_map.yaml`, it will be used:
  ctx = build_context()
  ```

---

## 🧩 Agent Loading: `load_agents_map()`

```python
def load_agents_map(
    source: Optional[Union[str, List[Union[str, dict]]]] = None
) -> Dict[str, str]
```

Returns a mapping `{ name: agents_txt_content }`, by:

1. **If** `source` is a `list`: iterate its entries.
2. **Elif** `source` is a `str` pointing to a file: load that YAML.
3. **Else** (no `source`): if `./agents_map.yaml` exists, load it; otherwise return `{}`.

Each *entry* in the list may be:

* **Built-in alias** (e.g. `"google-calendar"`)
* **Bare path/URL** (e.g. `"./agents/foo.json"`, `"https://…/bar.txt"`)

  * *Name is inferred* from the JSON `"agent"` field or the file basename.
* **Explicit mapping** `{ "my-calendar": "./calendar.json" }`

If a resource is JSON, it’s passed through `render_agents_txt()` to produce human-readable text.

---

## ✍️ `DEFAULT_CONTEXT`

A built-in system prompt you can override by passing your own `base_prompt`. It includes:

* Current date & time
* Framework usage guidelines
* Example JSON call
* OAuth & error-handling instructions
* “Do not announce actions, just do them. Seek confirmation if unsure.”

---

## 🔥 Design Highlights

| Feature             | Behavior                                                            |
| ------------------- | ------------------------------------------------------------------- |
| 🌐 Built-in aliases | Fetches from `https://invoke.network/api/agents-txt/{alias}`        |
| 📁 Local & remote   | Load `.json`/`.txt` files by path or URL; infer names automatically |
| 🔁 JSON → TXT       | Auto-render `agents.json` schemas into human-readable form          |
| 🗂️ Optional YAML   | Only reads `agents_map.yaml` when **no** `agents` argument given    |
| 📅 Time-aware       | Embeds the current timestamp on each context build                  |

---

**Note:** If you want a completely custom system prompt, pass your own `context` string to `InvokeAgent`—`build_context()` will still append integrations afterward.
