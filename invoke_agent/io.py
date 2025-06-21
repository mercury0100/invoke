import os
import json
from typing import Optional, Dict, Any

CONFIG_DIR       = os.path.join(os.getcwd(), ".invoke")
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, "credentials.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Ensure .invoke is git-ignored
GITIGNORE = os.path.join(os.getcwd(), ".gitignore")
if os.path.exists(GITIGNORE):
    with open(GITIGNORE) as f:
        lines = f.read().splitlines()
    if CONFIG_DIR not in lines:
        with open(GITIGNORE, "a") as f:
            f.write(f"\n{CONFIG_DIR}\n")
else:
    with open(GITIGNORE, "w") as f:
        f.write(f"{CONFIG_DIR}\n")


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

    def _load_all(self) -> Dict[str, Any]:
        try:
            with open(CREDENTIALS_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_all(self, data: Dict[str, Any]) -> None:
        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def load_credential(
        self, namespace: str, domain: str, cred_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a stored credential record by (namespace, domain, cred_type).
        Returns the dict you saved, or None if missing.
        """
        all_creds = self._load_all()
        return (
            all_creds
            .get(namespace, {})
            .get(domain, {})
            .get(cred_type)
        )

    def save_credential(
        self, namespace: str, domain: str, cred_type: str, record: Dict[str, Any]
    ) -> None:
        """
        Persist a credential record by (namespace, domain, cred_type).
        """
        all_creds = self._load_all()
        all_creds.setdefault(namespace, {}) \
                 .setdefault(domain, {})[cred_type] = record
        self._save_all(all_creds)


io = IOHandler()

def set_io_handler(custom_handler: IOHandler):
    """
    Override the global io instance with your own handler.
    You can subclass IOHandler and override any subset of methods.
    """
    global io
    io = custom_handler
