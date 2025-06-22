# auth.py

import time
import webbrowser
from typing import Optional
from urllib.parse import urlparse
import tldextract
from authlib.integrations.requests_client import OAuth2Session
from invoke_agent import io

GLOBAL_NS     = "global"
EXPIRY_BUFFER = 60  # seconds before expiry to refresh

_current_user_id: Optional[str] = None

def set_current_user(user_id: str) -> None:
    """
    Call this once to switch all subsequent OAuth lookups
    into the given user namespace (non‐interactive mode).
    """
    global _current_user_id
    _current_user_id = user_id

def _ns() -> str:
    """
    Returns the active namespace: either the set user_id or GLOBAL_NS.
    """
    return _current_user_id if _current_user_id is not None else GLOBAL_NS

def _domain_of(url: str) -> str:
    host = urlparse(url).netloc
    ext  = tldextract.extract(host)
    return f"{ext.domain}.{ext.suffix}"


class APIKeyManager:
    """
    Manages API-key injection config and retrieval.

    Config (per domain) under "<GLOBAL_NS>/<domain>/api_key_cfg":
      - in:   "query" | "header" | "body"
      - name: parameter/header/field name

    Key itself stored under "<GLOBAL_NS>/<domain>/api_key": {"key": "..."}
    """

    def get_api_cfg(self, url: str) -> tuple[str, str]:
        """
        Returns (where, name), prompting if no config is found in dev.
        Raises if in user mode and config is missing.
        """
        ns     = GLOBAL_NS
        domain = _domain_of(url)
        io.io.notify(f"🔍 Loading API-key config for {domain}")

        cfg = io.io.load_credential(ns, domain, "api_key_cfg") or {}
        if not cfg:
            if _current_user_id is not None:
                raise ValueError(f"No API-key config for {domain} in user mode")
            io.io.notify(f"\n🛠️ No API-key config for {domain}. Let’s set it up.")
            where = io.io.prompt("Injection location (query/header/body) [query]: ")\
                     .strip().lower() or "query"
            name  = io.io.prompt("Parameter/header/field name [api_key]: ")\
                     .strip() or "api_key"
            cfg   = {"in": where, "name": name}
            io.io.save_credential(ns, domain, "api_key_cfg", cfg)
            io.io.notify(f"✅ Saved API-key config for {domain}")

        return cfg["in"], cfg["name"]

    def get_api_key(self, url: str) -> str:
        """
        Returns the API key string, prompting if not already stored in dev.
        Raises if in user mode and key is missing.
        """
        ns     = GLOBAL_NS
        domain = _domain_of(url)
        io.io.notify(f"🔍 Loading API key for {domain}")

        rec = io.io.load_credential(ns, domain, "api_key") or {}
        if not rec.get("key"):
            if _current_user_id is not None:
                raise ValueError(f"No API key for {domain} in user mode")
            key = io.io.prompt(f"🔑 Enter API key for {domain}: ").strip()
            io.io.save_credential(ns, domain, "api_key", {"key": key})
            io.io.notify(f"✅ Saved API key for {domain}")
        else:
            key = rec["key"]

        return key


class OAuthManager:
    """
    Single manager for both authorization-code and client-credentials OAuth flows.

    Config (per domain) under "<user_ns>/<domain>/oauth_cfg":
      - grant_type:  "auth_code" | "machine"
      - auth_method: "post" | "basic"
      - client_id, client_secret
      - authorize_url, redirect_uri   (for auth_code)
      - token_url, scopes
      - name: header name for injection (default "Authorization")

    Token payload stored under the same namespace:
      "<user_ns or global>/<domain>/oauth": {"token": {...}}
    """

    def __init__(self):
        self.name = "oauth"

    def get_oauth_token(self, url: str) -> str:
        """
        Returns a valid access token, fetching or refreshing as needed.
        Machine-flow tokens always live under the GLOBAL_NS; auth-code tokens
        use the namespace set by set_current_user().
        Raises if in user mode and config is missing.
        """
        user_ns = _ns()
        domain  = _domain_of(url)
        io.io.notify(f"🔍 Checking OAuth token for {domain} (user namespace={user_ns})")

        # Load config from user namespace
        cfg = io.io.load_credential(user_ns, domain, f"{self.name}_cfg") or {}

        # Prompt for config if missing
        if not cfg:
            if user_ns != GLOBAL_NS and _current_user_id is not None:
                raise ValueError(f"No OAuth config for {domain} in user mode")
            cfg = self._prompt_cfg(domain)

        # Determine namespace for storing tokens
        ns_for_creds = GLOBAL_NS if cfg.get("grant_type") == "machine" else user_ns

        # Load stored token
        rec   = io.io.load_credential(ns_for_creds, domain, self.name) or {}
        token = rec.get("token")

        # Fetch or refresh if missing/expired
        if not token or time.time() >= token["expires_at"] - EXPIRY_BUFFER:
            token = self._fetch_or_refresh(token, cfg)
            io.io.save_credential(ns_for_creds, domain, self.name, {"token": token})

        return token["access_token"]

    def _prompt_cfg(self, domain: str) -> dict:
        io.io.notify(f"\n🔧 No OAuth config for {domain}. Let’s set it up.")
        grant  = io.io.prompt("Grant type (auth_code/machine) [auth_code]: ")\
                     .strip().lower() or "auth_code"
        method = io.io.prompt("Auth method (post/basic) [post]: ")\
                     .strip().lower() or "post"

        client_id     = io.io.prompt("Client ID: ").strip()
        client_secret = io.io.prompt("Client Secret: ").strip()
        scopes        = io.io.prompt("Scopes (space-separated): ").strip()

        authorize_url = ""
        redirect_uri  = ""
        if grant == "auth_code":
            authorize_url = io.io.prompt("Authorize URL: ").strip()
            redirect_uri  = io.io.prompt("Redirect URI: ").strip()
        token_url = io.io.prompt("Token URL: ").strip()

        cfg = {
            "grant_type":    grant,            # "auth_code" or "machine"
            "auth_method":   method,           # "post" or "basic"
            "client_id":     client_id,
            "client_secret": client_secret,
            "authorize_url": authorize_url,
            "redirect_uri":  redirect_uri,
            "token_url":     token_url,
            "scopes":        scopes,
            "name":          "Authorization",
        }
        io.io.save_credential(_ns(), domain, f"{self.name}_cfg", cfg)
        io.io.notify(f"✅ Saved OAuth config for {domain}")
        return cfg

    def _fetch_or_refresh(self, token: Optional[dict], cfg: dict) -> dict:
        sess = OAuth2Session(
            client_id                   = cfg["client_id"],
            client_secret               = cfg["client_secret"],
            scope                       = cfg["scopes"],
            redirect_uri                = cfg.get("redirect_uri") or None,
            token_endpoint_auth_method  = (
                "client_secret_post"
                if cfg["auth_method"] == "post"
                else "client_secret_basic"
            )
        )

        if token and token.get("refresh_token"):
            # Refresh existing token
            params = {
                "url":            cfg["token_url"],
                "refresh_token":  token["refresh_token"],
            }
            if cfg["auth_method"] == "post":
                params.update({
                    "client_id":     cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                })
            new_token = sess.refresh_token(**params)
        else:
            # Initial fetch
            if cfg["grant_type"] == "machine":
                params = {
                    "url":        cfg["token_url"],
                    "grant_type": "client_credentials",
                }
                if cfg["auth_method"] == "post":
                    params.update({
                        "client_id":     cfg["client_id"],
                        "client_secret": cfg["client_secret"],
                    })
                new_token = sess.fetch_token(**params)
            else:
                # auth_code flow
                uri, _ = sess.create_authorization_url(cfg["authorize_url"])
                io.io.notify(f"\n🔗 Open to authenticate:\n{uri}")
                webbrowser.open(uri)
                code = io.io.get_oauth_code().strip()
                params = {
                    "url":               cfg["token_url"],
                    "code":              code,
                    "grant_type":        "authorization_code",
                    "include_client_id": False,
                }
                if cfg["auth_method"] == "post":
                    params.update({
                        "client_id":     cfg["client_id"],
                        "client_secret": cfg["client_secret"],
                    })
                new_token = sess.fetch_token(**params)

        new_token["expires_at"] = time.time() + new_token.get("expires_in", 0)
        return new_token
