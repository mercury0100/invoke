# 🔐 `auth.py` — API Key & OAuth Credential Manager

This module manages API authentication for Invoke. It handles:

* **Static API keys** with configurable injection (`query`/`header`/`body`), always stored under a global namespace.
* **OAuth2 tokens** (both authorization‐code and client‐credentials) stored per‐user or in a global fallback.

All credentials live in `.invoke/credentials.json`, automatically created (and Git-ignored).

---

## 📦 Import

```python
from invoke_agent.auth import (
    APIKeyManager,
    OAuthManager,
    set_current_user
)
```

---

## 🔑 `APIKeyManager`

Handles API-key retrieval and injection config:

* **Global only** (no per-user scoping).
* Two new methods:

### `get_api_cfg(url: str) -> tuple[str, str]`

1. Looks up or prompts for injection config under the **global** namespace:

   * `in`: `"query"` | `"header"` | `"body"`
   * `name`: the param/header/field name
2. Saves to `.invoke/credentials.json` if missing.
3. Raises a `ValueError` in non-interactive (user) mode if missing.

### `get_api_key(url: str) -> str`

1. Retrieves the API key string under the **global** namespace.
2. Prompts once if unset (in dev).
3. Raises a `ValueError` in non-interactive (user) mode if missing.

---

## 🔐 `OAuthManager`

Manages all OAuth2 flows—authorization‐code **and** client-credentials—scoped per namespace:

* Call `set_current_user(user_id)` once to enable **per-user**, non-interactive mode.
* If unset, falls back to a single **global** namespace with interactive prompts.

### `get_oauth_token(url: str) -> str`

1. Determines the active namespace via `set_current_user` or `"global"`.
2. Loads or (in dev) prompts for `oauth_cfg`:

   ```jsonc
   {
     "grant_type":  "auth_code" | "machine",
     "auth_method": "post" | "basic",
     "client_id":   "...",
     "client_secret":"...",
     "authorize_url":"...",       // auth_code only
     "redirect_uri":"...",        // auth_code only
     "token_url":   "...",
     "scopes":      "...",
     "name":        "Authorization"
   }
   ```
3. Fetches or refreshes the token (using `authlib`), storing `{"token": {...}}`.
4. Returns `access_token` only—no header injection here.
5. Raises if config or token is missing in non-interactive (user) mode.

---

## ⚙️ Per-User Mode

```python
from invoke_agent.auth import set_current_user

# e.g. in a web request after authentication:
set_current_user(current_user.id)

# All OAuthManager calls now use credentials under that user_id namespace,
# and will never prompt interactively.
```

If you never call `set_current_user`, everything falls back to `"global"` with interactive prompts.

---

## 🗄️ Example Credentials File

```json
{
  "global": {
    "example.com": {
      "api_key_cfg": { "in": "query",  "name": "appid" },
      "api_key":     { "key": "XYZ123" }
    }
  },
  "alice": {
    "googleapis.com": {
      "oauth_cfg": {
        "grant_type":  "auth_code",
        "auth_method": "post",
        "client_id":   "…",
        "client_secret":"…",
        "authorize_url":"https://…",
        "redirect_uri":"urn:ietf:wg:oauth:2.0:oob",
        "token_url":   "https://…",
        "scopes":      "calendar",
        "name":        "Authorization"
      },
      "oauth": {
        "token": {
          "access_token":"…",
          "refresh_token":"…",
          "expires_at": 1714080000
        }
      }
    }
  }
}
```

---

## 🧠 Design Highlights

| Feature                  | Description                                               |
| ------------------------ | --------------------------------------------------------- |
| 🔒 Global API-keys       | One key per domain, no user scoping                       |
| 👤 Per-user OAuth tokens | Call `set_current_user()` to isolate credentials per user |
| 🔁 Auto token refresh    | Tokens refresh transparently before expiry                |
| 🌍 Domain-based lookup   | Works with any API’s base URL                             |
| 🧩 Plug-and-play IO      | Interactive prompts in dev, non-interactive in prod       |
