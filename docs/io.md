# 🧩 `io.py` — Customizable I/O & Credential Persistence for Invoke

The `io.py` module defines:

* A **pluggable I/O interface** for prompts, notifications, and OAuth code retrieval
* A **simple file‐based store** for API keys and OAuth configs/tokens
* Automatic creation and git‐ignore of the `.invoke/credentials.json` file

---

## 📦 Import

```python
from invoke_agent import io, set_io_handler
```

---

## 📁 Credential File Setup

* **Directory**: `./.invoke/` (created automatically)
* **File**: `./.invoke/credentials.json`
* On first run, `.invoke/` is added to your project’s `.gitignore` if not already present.

---

# 🧱 `IOHandler` Class

Override any of these methods to customize CLI behavior or storage:

```python
class IOHandler:

    # ─── Basic I/O ────────────────────────────────────────────────────────────
    def prompt(self, message: str) -> str:
        """
        Ask the developer for input (e.g. API keys, OAuth codes).
        Defaults to Python’s built-in input().
        """
        return input(message)

    def notify(self, message: str) -> None:
        """
        Log or display messages (e.g. “✅ Saved!”).
        Defaults to print().
        """
        print(message)

    def get_oauth_code(self) -> str:
        """
        Obtain an OAuth authorization code after user consent.
        Defaults to prompt(), but you can override to use a local web server.
        """
        return self.prompt("\n🔑 Enter the auth code: ")

    # ─── Credential Store Helpers ────────────────────────────────────────────
    def _load_all(self) -> Dict[str, Any]:
        """Internal: read and parse the entire credentials JSON file."""
        try:
            with open(CREDENTIALS_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_all(self, data: Dict[str, Any]) -> None:
        """Internal: overwrite the credentials JSON file with `data`."""
        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def load_credential(
        self,
        namespace: str,
        domain: str,
        cred_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a stored credential record.
        
        - `namespace`: either `"global"` or a user ID (set via auth.set_current_user)  
        - `domain`: the API’s base domain, e.g. `"example.com"`  
        - `cred_type`: e.g. `"api_key"`, `"api_key_cfg"`, `"oauth_cfg"`, or `"oauth"`
        
        Returns the saved dict, or `None` if not found.
        """
        all_creds = self._load_all()
        return (
            all_creds
            .get(namespace, {})
            .get(domain, {})
            .get(cred_type)
        )

    def save_credential(
        self,
        namespace: str,
        domain: str,
        cred_type: str,
        record: Dict[str, Any]
    ) -> None:
        """
        Persist a credential record.
        
        Creates any missing nesting for `namespace` → `domain` → `cred_type`.
        """
        all_creds = self._load_all()
        all_creds.setdefault(namespace, {}) \
                 .setdefault(domain, {})[cred_type] = record
        self._save_all(all_creds)
```

---

## 🌍 Global Instance

```python
io = IOHandler()
```

All SDK components use `io.prompt()`, `io.notify()`, `io.get_oauth_code()`, `io.load_credential()` and `io.save_credential()` via this singleton.

---

## 🔧 `set_io_handler(custom_handler: IOHandler)`

Swap in your own handler to integrate with GUIs, webhooks, or test harnesses:

```python
from invoke_agent.io import IOHandler, set_io_handler

class MyIO(IOHandler):
    def prompt(self, msg):
        # custom UI code here
        return my_ui_input(msg)

set_io_handler(MyIO())
```

After this, **all** `io.*` calls use your `MyIO` implementation.

---

## ⚙️ How It All Ties Together

1. **APIKeyManager** and **OAuthManager** call

   ```python
   io.load_credential(ns, domain, cred_type)
   ```

   to fetch stored keys or tokens.
2. If missing (and in dev mode), they call

   ```python
   io.prompt(…)
   io.save_credential(ns, domain, cred_type, record)
   ```
3. In production/user mode (when `set_current_user` has been called), missing entries cause an error instead of prompting.

This ensures **seamless** CLI defaults in development, and **robust**, non-interactive behavior in per-user production environments.


---

## 💡 Use Case: Flask-Based OAuth

You can override `get_oauth_code` to return the code captured from a local Flask server:

```python
class OAuthWithFlask(IOHandler):
    def get_oauth_code(self):
        import time
        from flask import Flask, request

        code_container = {"code": None}
        app = Flask(__name__)

        @app.route("/oauth")
        def capture():
            code_container["code"] = request.args.get("code")
            return "✅ You can close this tab now."

        import threading
        threading.Thread(target=lambda: app.run(port=8080)).start()

        while code_container["code"] is None:
            time.sleep(0.5)

        return code_container["code"]
```

---

## 🧠 Why This Matters

This pattern allows you to:

- Keep the Invoke SDK CLI-friendly by default
- Build advanced integrations (browser UIs, IDE extensions, headless bots)
- Support silent mode, debugging, or OAuth automation

---