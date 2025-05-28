# 🔐 `auth.py` — API Key & OAuth Credential Manager

This module manages API authentication for Invoke. It handles both API key and OAuth token storage, prompting, injection, and refreshing — all stored securely in `.invoke/credentials.json`.

---

## 📁 Credential Storage

- **Location**: `.invoke/credentials.json`
- Automatically created if not present.
- Auto-added to `.gitignore` to avoid leaks.

---

## 📦 Import

```python
from invoke_agent.auth import APIKeyManager, OAuthManager, MachineManager
```

---

## 🔑 `APIKeyManager`

Handles API key retrieval and prompting. Used for any service requiring a static key in the query, header, or body.

### 🔧 Methods

#### `get_api_key(url: str) -> str`

- Looks up the domain from the URL.
- If no key is saved, prompts the user once.
- Saves for future use.

✅ Smart fallback. 🔐 Secure local storage.

---

## 🔐 `OAuthManager`

Handles **OAuth 2.0** tokens, including login flow and refresh.

### 🔧 Methods

#### `get_oauth_token(url: str) -> str`

- Returns the token for the domain.
- Prompts user for credentials if not saved.
- Refreshes the token if expired.

#### `refresh_token(domain: str) -> str`

- Automatically called when the token has expired.
- Saves new `access_token` and `expires_at`.

#### `_prompt_user_for_credentials(domain: str)`

- Asks the user for all required fields:
  - `client_id`, `client_secret`
  - `auth_url`, `token_url`
  - `redirect_uri`, `scopes`
- Opens the browser for login.
- Prompts for code and completes token exchange.

---

## 🧪 Example Credentials File

```json
{
  "googleapis.com": {
    "api_key": "AIz...",
    "oauth": {
      "client_id": "...",
      "access_token": "...",
      "refresh_token": "...",
      "expires_at": 1714080000
    }
  }
}

```
#### `get_oauth_token(url: str) -> str`

* Returns the machine‐to‐machine access token for the given service URL.
* Looks up stored credentials under the service’s base domain.
* If no credentials are found, prompts the user to enter `client_id`, `client_secret`, and `token_url`.
* If the stored token has expired, automatically calls `_refresh_token`.
* On success, logs a shortened preview and returns the valid `access_token`.

#### `_refresh_token(domain: str) -> str`

* Invoked internally when the current token is expired or missing.
* Sends a `POST` to the stored `token_url` using the **client credentials** grant.
* Required headers:

  * `Content-Type: application/x-www-form-urlencoded`
  * `Accept: application/json`
* On HTTP 200, parses `access_token` and `expires_in` from JSON.
* Updates the credentials store with the new `access_token` and `expires_at`.
* Persists the updated credentials file to disk.
* Logs success and returns the refreshed `access_token`.

#### `_prompt_user_for_credentials(domain: str)`

* Interactive setup helper when no machine credentials exist.
* Prompts the user for:

  * `Client ID`
  * `Client Secret`
  * `Token URL` (the OAuth2 token endpoint)
* Stores these under `credentials[domain]["machine"]` with empty token fields.
* Saves the credentials JSON to disk for future lookup.
* Logs confirmation once saved.

#### `_get_base_domain(url: str) -> str`

* Utility to extract the registrable domain (e.g. `api.example.com` → `example.com`).
* Uses `urlparse` and `tldextract` to reliably handle subdomains and public suffixes.

---

## 🧪 Example Credentials File

```json
{
  "example.com": {
    "machine": {
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_CLIENT_SECRET",
      "token_url": "https://auth.example.com/oauth2/token",
      "access_token": "eyJ…",
      "expires_at": 1714080000
    }
  }
}
```

---

## 💬 Prompt Handling

This module uses the `io.py` layer for prompting and logging. You can override it to plug in your own UI or Flask server.

### Custom `get_oauth_code()` Support

You can customize the OAuth code retrieval with:

```python
class CustomIOHandler(IOHandler):
    def get_oauth_code(self):
        # your custom logic (e.g. webhook listener)
        return wait_for_code()
```

Then set it with:

```python
from invoke_agent import io
io.set_io_handler(CustomIOHandler())
```

---

## 🧠 Design Highlights

| Feature                  | Description                          |
|--------------------------|--------------------------------------|
| 🔒 Local credential cache | No env vars required, all secure     |
| 🔁 Auto token refresh     | Transparent background refresh       |
| 🌍 Domain-based lookup    | Works seamlessly with any URL        |
| 🧩 Plug-and-play IO       | Replace CLI with custom UI handler   |

---