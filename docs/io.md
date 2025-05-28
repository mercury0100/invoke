# 🧩 `io.py` — Customizable I/O Hooks for Invoke

The `io.py` module defines a pluggable interface for **developer interaction**, used by the Invoke framework to:

- Prompt for user input (e.g. API keys)
- Notify the user (e.g. logs, progress)
- Capture OAuth authorization codes

This interface can be extended or overridden by developers to plug in custom UIs, CLI prompts, or OAuth servers.

---

## 🚀 Basic Usage

```python
from invoke_agent import io

api_key = io.prompt("🔑 Enter your API key: ")
io.notify("✅ API key saved!")
```

---

## 🧱 `IOHandler` Class

This is the base I/O class. Override it to customize the way prompts, logs, and OAuth flows behave.

```python
class IOHandler:
    def prompt(self, message: str) -> str:
        """General-purpose prompt (e.g. asking for an API key)."""
        return input(message)

    def notify(self, message: str) -> None:
        """General-purpose notification or logging."""
        print(message)

    def get_oauth_code(self) -> str:
        """
        Handle OAuth code retrieval for a given service.

        Override this in a custom IOHandler to support
        browser-based flows, Flask endpoints, etc.
        """
        return self.prompt("\n🔑 Enter the auth code: ")
```

---

## 🌍 `io` — The Global Instance

```python
io = IOHandler()
```

Invoke uses this global `io` object across the framework for all interaction. This ensures consistent behavior and easy customization.

---

## 🔧 `set_io_handler(custom_handler: IOHandler)`

Replace the global `io` object with your own handler.

```python
from invoke_agent.io import IOHandler, set_io_handler

class MyIO(IOHandler):
    def prompt(self, msg):
        return "my-key"

    def get_oauth_code(self):
        # Use a Flask server or webhook
        return "code-from-server"

set_io_handler(MyIO())
```

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