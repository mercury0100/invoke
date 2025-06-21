import json
import requests
from urllib.parse import urlparse, urlencode, parse_qsl
import tldextract
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os

from langchain_core.tools import tool
from invoke_agent.auth import APIKeyManager, OAuthManager, _ns

load_dotenv()
invoke_api_key  = os.getenv("INVOKE_API_KEY")
api_key_manager = APIKeyManager()
oauth_manager   = OAuthManager()

MAX_CHARS = 50000  # maximum length of response text we keep

def extract_error_message(response: requests.Response) -> str:
    """Extract message from JSON error or fallback to raw text."""
    try:
        data = response.json()
        if "error" in data:
            err = data["error"]
            return err.get("message", str(err)) if isinstance(err, dict) else str(err)
        if "message" in data:
            return data["message"]
        return json.dumps(data)
    except Exception:
        return response.text
    
def route_api_request(method, url, headers=None, params=None, data=None,
                      auth_type="none", invoke_flag="o", invoke_key='none', ns=None, timeout=10):
    """
    Routes an API request through a Cloudflare Worker.
    
    Instead of directly calling the target URL, this function packages
    the request parameters into a JSON object using a standardized schema,
    and then sends that JSON to the Cloudflare endpoint.
    
    The Cloudflare Worker then reconstructs the final request.
    """
    #Extract main domain and query params
    extracted = tldextract.extract(url)
    main_domain = f"{extracted.domain}.{extracted.suffix}"
    
    if invoke_flag == 'i':
        invoke_key = invoke_key
    
    # Standardize the request into a JSON payload
    request_payload = {
        "method": method.upper(),
        "url": url,
        "headers": headers or {},
        "query": params or {},
        "body": data,  # could be None or a string/dict (if dict, Cloudflare Worker may need to re-serialize)
        "main_domain": main_domain,
        "auth_type": auth_type,
        "invoke_flag": invoke_flag,
        "invoke_key": invoke_key,
        "ns": ns,
    }
    
    # Define your Cloudflare Worker endpoint URL.
    cf_endpoint = "https://wandering-tooth.cooper-c79.workers.dev/"
    
    # Set the request headers for the call to Cloudflare (ensuring JSON content)
    cf_headers = {"Content-Type": "application/json"}
    
    # Convert the standardized request to JSON
    payload = json.dumps(request_payload)
    
    # Send the standardized request to the Cloudflare endpoint
    response = requests.request("POST", cf_endpoint, headers=cf_headers, data=payload, timeout=timeout)
    
    return response

def execute_api_call(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    1) “There is No Step One”
    2) Extract fields from `task`
    3) Parse auth_code into auth_type & invoke_flag
    4) Inject auth (api_key or oauth)
    5) Build URL vs payload
    6) Send via requests or Cloudflare Worker
    7) Parse JSON or return raw text
    8) Handle HTTP and parsing errors
    """
    try:
        # Step 1: There is No Step One

        # Step 2: Extract required fields
        method    = task.get("method", "GET").upper()
        url       = task.get("url")
        params    = task.get("parameters", {}) or {}
        headers   = {"Content-Type": "application/json", **(task.get("headers") or {})}
        auth_code = task.get("auth_code", "none")

        if not url:
            return {"error": "❌ No URL provided in the action."}

        # Step 3: Parse auth_code
        parts       = auth_code.split("::", 1)
        auth_type   = parts[0]
        invoke_flag = parts[1] if len(parts) > 1 else None
        
        if auth_type not in ("none", "api_key", "oauth"):
            return {"error": f"❌ Unsupported auth_type: {auth_type!r}. Must be one of none, api_key, oauth."}
        
        if invoke_flag != 'i':
            # Step 4: Auth injection
            if auth_type == "api_key":
                key = api_key_manager.get_api_key(url)
                where, name = api_key_manager.get_api_cfg(url)
                if where == "query":
                    params[name] = key
                elif where == "header":
                    headers[name] = key
                else:  # "body"
                    params[name] = key

            elif auth_type == "oauth":
                try:
                    token = oauth_manager.get_oauth_token(url)
                except Exception as e:
                    return {"error": f"❌ OAuth token retrieval failed: {e}"}
                headers["Authorization"] = f"Bearer {token}"

        # Step 5: Build URL vs payload
        if method == "GET":
            parsed = urlparse(url)
            q = dict(parse_qsl(parsed.query))
            q.update(params)
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(q, doseq=True)}"
            body = None
        else:
            body = json.dumps(params)

        # Step 6: Execute the request
        if invoke_flag == "i":
            response = route_api_request(
                method=method,
                url=url,
                headers=headers,
                params=params if method == "GET" else None,
                data=body,
                auth_type=auth_type,
                invoke_flag=invoke_flag,
                invoke_key=invoke_api_key,
                ns=_ns(),
                timeout=10
            )
        else:
            response = requests.request(method, url, headers=headers, data=body, timeout=10)

        # Step 7: Handle successful response
        if response.ok:
            content_type = response.headers.get("Content-Type", "").lower()
            text = response.text[:MAX_CHARS]
            if "application/json" in content_type:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"partial_response": text, "note": "⚠️ Truncated invalid JSON"}
            else:
                return {
                    "content_type": content_type,
                    "text": text,
                    "status_code": response.status_code
                }

        # Step 8: HTTP error status
        return {
            "error": f"❌ HTTP {response.status_code} – {extract_error_message(response)}"
        }

    except json.JSONDecodeError:
        return {"error": "❌ Invalid JSON format received."}
    except requests.exceptions.Timeout:
        return {"error": "⏳ Request timed out."}
    except Exception as e:
        return {"error": f"⚠️ Unexpected error: {e}"}


@tool
def api_executor(
    method: str,
    url: str,
    auth_code: str,
    parameters: Optional[dict] = None,
    headers: Optional[dict] = None
) -> Any:
    """Execute HTTP requests using the Invoke framework."""
    return execute_api_call({
        "method":     method,
        "url":        url,
        "auth_code":  auth_code,
        "parameters": parameters or {},
        "headers":    headers or {}
    })