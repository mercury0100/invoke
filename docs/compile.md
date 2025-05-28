# 🛠️ `compile.py` — Render `agents.txt` from `agents.json`

This module transforms a structured `agents.json` schema into a human-readable, Markdown-style `agents.txt` file. Both developers and LLMs use the output to understand available endpoints, parameters, headers, and authentication.

---

## 📦 Import

```python
from invoke_agent.compile import render_agents_txt, merge_headers
```

---

## 🧰 `merge_headers(global_headers: dict, endpoint_headers: dict) -> dict`

Combine global headers with endpoint-specific overrides:

- **Global headers** apply to every endpoint.
- **Endpoint headers** override any matching global headers.

```python
from invoke_agent.compile import merge_headers

# Global and endpoint headers combined; endpoint wins on duplicates
merged = merge_headers(
    {"Accept": "application/json", "Cache-Control": "no-cache"},
    {"Cache-Control": "max-age=3600", "X-Custom": "value"}
)
# → {"Accept": "application/json", "Cache-Control": "max-age=3600", "X-Custom": "value"}
```

---

## ✨ `render_agents_txt(agent_json_str: str) -> str`

Parses the JSON text of an `agents.json` file and emits a Markdown-style specification. The output includes:

1. **Agent Header**
   - `# {Label}` — uses `"label"` or capitalized `"agent"`.  
   - `Base URL: {host}` (drops `https://`).  
   - `Auth Code:` (if top-level `"auth"` present).  
   - `Headers:` (if top-level `"headers"` present).

2. **Endpoint Blocks**  
   For each item in `"endpoints"`:

   - **Endpoint:** `{label or name}`  
   - **Description:** free-text `"description"`.  
   - **Method:** HTTP verb (GET, POST, etc.).  
   - **URL Template:** full URL with `{placeholders}` for path/query params.  
   - **Path Parameters:** list required path parameters (`"path_params"`).  
   - **Query Parameters:** list optional query parameters (`"query_params"`).  
   - **Body Parameters:** for write methods (`POST`, `PUT`, `PATCH`) based on `"body_params"`.  
   - **Headers:** merges global + endpoint headers via `merge_headers()`, with endpoint values overriding.  
   - **Examples:** one or more JSON call snippets.  
   - **Notes:** free-form bullet points.

3. **Formatting**  
   - `---` separators between sections  
   - Triple-backtick fenced blocks for examples  
   - Bullet lists for parameters and headers  

---

### 🔧 Example Input (`agents.json`)

```json
{
  "agent": "openweather",
  "label": "OpenWeatherMap API",
  "base_url": "https://api.openweathermap.org",
  "auth": {
    "type": "query",      // "query" | "header" | "body" | "oauth" | "machine"
    "format": "appid",
    "code": "your_api_key"
  },
  "headers": {
    "Accept": "application/json",
    "Cache-Control": "no-cache"
  },
  "endpoints": [
    {
      "name": "Current Weather",
      "description": "Get current weather data.",
      "method": "GET",
      "path": "/data/2.5/weather",
      "query_params": { "q": "London" },
      "headers": { "Cache-Control": "max-age=3600" },
      "examples": [
        {
          "url": "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY",
          "parameters": {"q": "London"}
        }
      ],
      "notes": ["Use `units=metric` for Celsius."]
    }
  ]
}
```

### 📄 Example Output (`agents.txt`)

```txt
# OpenWeatherMap API
Base URL: api.openweathermap.org
Auth Code: query::appid
Headers:
- Accept: application/json
- Cache-Control: no-cache

## ✉️ OpenWeatherMap API ##
---
Endpoint: Current Weather
Description: Get current weather data.
Method: GET
URL Template: https://api.openweathermap.org/data/2.5/weather?q={q}

Query Parameters (optional):
- q: London

Headers:
- Accept: application/json
- Cache-Control: max-age=3600

Examples:
```json
{
  "method": "GET",
  "url": "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY",
  "auth_code": "query::appid",
  "parameters": {"q": "London"}
}
```
Notes:
- Use `units=metric` for Celsius.

---
