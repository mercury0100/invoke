## 🧠 agents.json Specification

This document outlines the full specification for `agents.json` files used in the Invoke Framework.
It provides structure, field types, examples, and rationale.

---

## 📄 Overview

`agents.json` is a structured JSON file that defines how AI agents can safely interact with an external API. It serves as a source of truth for translating natural language into executable HTTP requests.

Each file corresponds to a single service or API, and defines:

- Metadata and authentication  
- Global headers (optional)  
- A list of tool‑callable endpoints, each with:
  - URL template (with `{}` placeholders)  
  - Parameter names + descriptions  
  - Per‑endpoint headers (override globals)  
  - Examples to guide LLM inference  

---

## 🧱 Top‑Level Structure

```json
{
  "agent": "openweather",
  "label": "OpenWeatherMap API",
  "base_url": "https://api.openweathermap.org/data/2.5",
  "auth": {
    "type": "query",      // "query" | "header" | "body" | "oauth" | "machine"
    "format": "appid",
    "code": "i"
  },
  "headers": {
    "Accept": "application/json",
    "Cache-Control": "no-cache"
  },
  "endpoints": [ ... ]
}
```

| Field       | Type     | Required | Description                                                                                 |
|-------------|----------|:--------:|---------------------------------------------------------------------------------------------|
| `agent`     | string   | ✅       | Machine‑readable identifier. Must match the JSON field used by `"agent"` when rendering docs.|
| `label`     | string   | ✅       | Human‑readable name (shown in rendered `agents.txt`).                                       |
| `base_url`  | string   | ✅       | Common URL prefix for all endpoints. `render_agents_txt()` will strip `https://` when displaying. |
| `auth`      | object   | ❌       | Default auth scheme for all endpoints. See below for types.                                  |
| `headers`   | object   | ❌       | Default HTTP headers applied to every request. Per‑endpoint `headers` override these.         |
| `endpoints` | array    | ✅       | List of endpoint definitions (see next section).                                             |

### 🔐 `auth` Object

Defines where and how to insert credentials for each call:

```jsonc
"auth": {
  "type": "query",    // options: "query" | "header" | "body" | "oauth" | "machine"
  "format": "Bearer",// e.g. "Bearer", "token", "appid"
  "code": "i"       // credential identifier for Invoke or local auth
}
```

- **query**: Add as `?format=token`  
- **header**: Add as `Authorization: format token`  
- **body**: Inject into JSON body  
- **oauth**: Invoke-managed OAuth flow  
- **machine**: Machine‑to‑machine credential (e.g., client‑ID/secret)

---

## 🔽 Endpoint Fields

Each endpoint definition must include the following keys:

```json
{
  "name": "get_weather",
  "label": "☀️ Current Weather",
  "description": "Retrieve current weather by city name.",
  "method": "GET",
  "path": "/weather",
  "path_params": { "cityId": "Numeric city identifier" },
  "query_params": { "q": "City name, e.g. \"London\"" },
  "body_params": { "mode": "Optional JSON mode for response" },
  "headers": { "X-Custom-Header": "custom value" },
  "auth_code": "query::appid",
  "examples": [
    {
      "url": "https://...weather?q=London&appid=KEY",
      "parameters": { "q": "London" }
    }
  ],
  "notes": ["City name is required"]
}
```

| Field           | Type            | Required | Description                                                                                         |
|-----------------|-----------------|:--------:|-------------------------------------------------------------------------------------------------------------------|
| `name`          | string          | ✅       | Internal identifier for the endpoint.                                                                |
| `label`         | string          | ✅       | Friendly name (shown in `agents.txt`). Include emoji for clarity.                                      |
| `description`   | string          | ✅       | One-sentence summary of what this endpoint does.                                                       |
| `method`        | string          | ✅       | HTTP verb, case-insensitive (GET, POST, PUT, PATCH, DELETE).                                          |
| `path`          | string          | ✅       | Relative path from `base_url`, with `{param}` placeholders.                                           |
| `path_params`   | object          | ❌       | Mapping `paramName` → `description`. Required to fill path placeholders.                               |
| `query_params`  | object          | ❌       | Mapping `paramName` → `description`. Rendered as `?key={key}&…`. Can be omitted by the LLM if unneeded. |
| `body_params`   | object          | ❌       | Mapping `paramName` → `description`. Used only for write methods (POST/PUT/PATCH).                     |
| `headers`       | object          | ❌       | Per-endpoint headers. These **override** any top-level `headers`.                                      |
| `auth_code`     | string          | ❌       | Override for default `auth`. E.g. `"oauth::Bearer"`.                                                 |
| `examples`      | array of object | ✅ᴿ    | Real-world call snippets. Include at least one to guide the LLM.                                       |
| `notes`         | array of string | ❌       | Developer hints, caveats, or usage tips.                                                              |

ᕀ _Highly recommended_ – strengthens LLM’s ability to generate correct calls.

---

## ✅ Best Practices

- **Param descriptions**: Describe all `path_params`, `query_params`, and `body_params` as name→description, never example values.  
- **Examples**: Supply real example values under `examples.parameters`.  
- **Header overrides**: Use per-endpoint `headers` only when needed; they override global headers.  
- **Auth**: Only override `auth_code` for endpoints requiring a different scheme.  
- **Labels**: Use clear labels + emoji for human readability.  

---

## 🛠 Sample Agent File

See the [examples](../notebooks/agents) folder or try the [visual editor](https://invoke.network/create-agents-txt) to build your own spec.