import json
import os
import time
import requests
import webbrowser
from urllib.parse import urlparse, urlencode
import tldextract

from invoke_agent import io

gitignore_path = ".gitignore"
config_path = ".invoke"

CREDENTIALS_PATH = os.path.join(os.getcwd(), config_path, "credentials.json")
os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

# Add to .gitignore if not already present
if os.path.exists(gitignore_path):
    with open(gitignore_path, "r") as f:
        lines = f.read().splitlines()
    if config_path not in lines:
        with open(gitignore_path, "a") as f:
            f.write(f"\n{config_path}\n")
else:
    with open(gitignore_path, "w") as f:
        f.write(f"{config_path}\n")

# --- JSON utilities ---
def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(file_path, "w") as f:
            json.dump({}, f)
        return {}

def save_json_file(file_path: str, data: dict) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# --- API Key Manager ---
class APIKeyManager:
    def __init__(self):
        self.credentials = load_json_file(CREDENTIALS_PATH)

    def get_api_key(self, url):
        domain = self._get_base_domain(url)
        io.io.notify(f"🔍 Looking for API key for: {domain}")

        if domain not in self.credentials or "api_key" not in self.credentials[domain]:
            return self._prompt_user_for_api_key(domain)

        key = self.credentials[domain]["api_key"]
        io.io.notify(f"✅ Retrieved API key for {domain}: {key[:5]}********")
        return key

    def _prompt_user_for_api_key(self, domain):
        key = io.io.prompt(f"🔑 Enter API key for {domain}: ").strip()
        if not key:
            io.io.notify("⚠️ No API key entered. Request will fail.")
            return None
        if domain not in self.credentials:
            self.credentials[domain] = {}
        self.credentials[domain]["api_key"] = key
        save_json_file(CREDENTIALS_PATH, self.credentials)
        io.io.notify(f"✅ API key saved for {domain}!")
        return key

    def _get_base_domain(self, url):
        parsed = urlparse(url)
        ext = tldextract.extract(parsed.netloc)
        return f"{ext.domain}.{ext.suffix}"

# --- OAuth Manager ---
class OAuthManager:
    def __init__(self):
        self.credentials = load_json_file(CREDENTIALS_PATH)

    def get_oauth_token(self, url):
        domain = self._get_base_domain(url)
        io.io.notify(f"🔍 Checking OAuth token for: {domain}")
        creds = self.credentials.get(domain, {}).get("oauth")

        if not creds:
            self._prompt_user_for_credentials(domain)
            creds = self.credentials.get(domain, {}).get("oauth")
            if not creds:
                raise ValueError("❌ OAuth setup failed.")

        if time.time() >= creds.get("expires_at", 0):
            return self.refresh_token(domain)

        io.io.notify(f"✅ Token for {domain}: {creds['access_token'][:5]}********")
        return creds["access_token"]

    def refresh_token(self, domain):
        creds = self.credentials[domain]["oauth"]
        io.io.notify(f"🔄 Refreshing token for {domain}...")
        res = requests.post(
            creds["token_url"],
            data={
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "refresh_token": creds["refresh_token"],
                "grant_type": "refresh_token"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if res.status_code != 200:
            raise ValueError(f"❌ Token refresh failed: {res.text}")

        token_data = res.json()
        creds["access_token"] = token_data["access_token"]
        creds["expires_at"] = time.time() + token_data["expires_in"]
        self.credentials[domain]["oauth"] = creds
        save_json_file(CREDENTIALS_PATH, self.credentials)
        io.io.notify(f"✅ Token refreshed for {domain}.")
        return creds["access_token"]

    def _prompt_user_for_credentials(self, domain):
        io.io.notify("\n🌐 Enter OAuth details for", domain)
        client_id = io.io.prompt("Client ID: ").strip()
        client_secret = io.io.prompt("Client Secret: ").strip()
        auth_url = io.io.prompt("Auth URL: ").strip()
        token_url = io.io.prompt("Token URL: ").strip()
        redirect_uri = io.io.prompt("Redirect URI: ").strip()
        scopes = io.io.prompt("Scopes (space-separated): ").strip()

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scopes,
            "access_type": "offline"
        }
        full_auth_url = f"{auth_url}?{urlencode(auth_params)}"
        io.io.notify(f"\n🔗 Open this URL to authenticate:\n{full_auth_url}")
        webbrowser.open(full_auth_url)

        code = io.io.get_oauth_code().strip()
        io.io.notify("⏳ Exchanging code for token...")
        res = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if res.status_code != 200:
            io.io.notify(f"❌ Failed to get token: {res.text}")
            return
        token_data = res.json()
        self.credentials.setdefault(domain, {})["oauth"] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_url": auth_url,
            "token_url": token_url,
            "redirect_uri": redirect_uri,
            "scopes": scopes,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "expires_at": time.time() + token_data["expires_in"]
        }
        save_json_file(CREDENTIALS_PATH, self.credentials)
        io.io.notify(f"✅ OAuth credentials saved for {domain}.")

    def _get_base_domain(self, url):
        parsed = urlparse(url)
        ext = tldextract.extract(parsed.netloc)
        return f"{ext.domain}.{ext.suffix}"

# --- Machine Manager ---
class MachineManager:
    def __init__(self):
        self.credentials = load_json_file(CREDENTIALS_PATH)

    def get_oauth_token(self, url):
        domain = self._get_base_domain(url)
        io.io.notify(f"🤖 Checking machine token for: {domain}")
        creds = self.credentials.get(domain, {}).get("machine")

        if not creds:
            self._prompt_user_for_credentials(domain)
            creds = self.credentials.get(domain, {}).get("machine")
            if not creds:
                raise ValueError("❌ Machine credential setup failed.")

        if time.time() >= creds.get("expires_at", 0):
            return self._refresh_token(domain)

        io.io.notify(f"✅ Token for {domain}: {creds['access_token'][:5]}********")
        return creds["access_token"]

    def _refresh_token(self, domain):
        creds = self.credentials[domain]["machine"]
        io.io.notify(f"🔄 Fetching new token for {domain}...")

        res = requests.post(
            creds["token_url"],
            data={
                "grant_type": "client_credentials",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"]
            },
            headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
            }
        )

        if res.status_code != 200:
            raise ValueError(f"❌ Token request failed: {res.text}")

        token_data = res.json()
        creds["access_token"] = token_data["access_token"]
        creds["expires_at"] = time.time() + token_data["expires_in"]
        self.credentials[domain]["machine"] = creds
        save_json_file(CREDENTIALS_PATH, self.credentials)
        io.io.notify(f"✅ Machine token refreshed for {domain}.")
        return creds["access_token"]

    def _prompt_user_for_credentials(self, domain):
        io.io.notify(f"\n🛠️  Enter machine-to-machine credentials for {domain}")
        client_id = io.io.prompt("Client ID: ").strip()
        client_secret = io.io.prompt("Client Secret: ").strip()
        token_url = io.io.prompt("Token URL: ").strip()

        self.credentials.setdefault(domain, {})["machine"] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "token_url": token_url,
            "access_token": "",
            "expires_at": 0
        }
        save_json_file(CREDENTIALS_PATH, self.credentials)
        io.io.notify(f"✅ Machine credentials saved for {domain}.")

    def _get_base_domain(self, url):
        parsed = urlparse(url)
        ext = tldextract.extract(parsed.netloc)
        return f"{ext.domain}.{ext.suffix}"