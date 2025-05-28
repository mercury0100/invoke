# 🧠 `core.py` — Invoke API Execution Engine

The `core` module powers the low-level API request system for Invoke. It manages authentication injection, formats outgoing requests, and handles JSON and non-JSON responses — including routing through a Cloudflare Worker.

---

## 📦 Import

```python
from invoke_agent.core import api_executor, execute_api_call
```

---

## 🔧 `api_executor` (LangChain Tool)

```python
@tool
def api_executor(method: str, url: str, auth_code: str, parameters: Optional[dict] = None) -> str
```

This is the main tool used by Invoke Agents. It wraps `execute_api_call()` in a LangChain-compatible format and allows LLMs to perform structured tool calls.

- `method`: HTTP verb (e.g. GET, POST).
- `url`: Full target URL.
- `auth_code`: e.g. `query::key`, `oauth::Bearer`, etc.
- `parameters`: Query/body parameters as a dict.

---

## ⚙️ `execute_api_call`

```python
def execute_api_call(task: Dict[str, Any]) -> Dict[str, Any]
```

The workhorse behind all API calls. It:
- Injects API keys or OAuth tokens.
- Handles parameter placement for GET/POST.
- Routes the request via Cloudflare (if using hosted integrations).
- Returns a clean JSON result or descriptive error message.

**Expected `task` format:**

```json
{
  "method": "GET",
  "url": "https://api.example.com/v1/info",
  "auth_code": "query::key",
  "parameters": {
    "user_id": "1234"
  }
}
```

---

## 🛠️ `route_api_request`

```python
def route_api_request(...)
```

This function packages and sends API calls through a secure [Cloudflare Worker](https://developers.cloudflare.com/workers/), abstracting away network-level complexity and enabling server-side logging, security, and rate-limiting.

It accepts:
- Headers, method, URL
- Optional OAuth/API key injection
- Reconstructs the payload on the Cloudflare side

---

## ⚠️ `extract_error_message`

```python
def extract_error_message(response) -> str
```

Tries to cleanly extract the most relevant error string from a failed API response. It handles:
- Common error fields (`error.message`, `message`, etc.)
- Non-JSON responses (fallback to plain text)

---

## 🧪 Built-In Defaults

- ✅ OAuth and API key injection via `auth_code` (e.g. `oauth::Bearer`).
- ✅ Cloudflare-based routing.
- ✅ JSON + text content support (fallbacks included).
- ✅ Response truncation (5k characters max).

---

## 🗝️ Auth Strategy

| Format        | Meaning                     |
|---------------|-----------------------------|
| `query::key`  | Adds API key to query string |
| `header::key` | Adds API key to headers      |
| `oauth::Bearer` | Adds OAuth Bearer token to headers |
| `body::key`   | Injects API key in payload   |
| `machine::Bearer`   | Adds Machine token to headers   |

Use `auth_code` in your `agents.json` to control this automatically.

---