import json
import requests
from urllib.parse import urlparse, urlencode, parse_qsl
import tldextract
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import yaml

from langchain_core.tools import tool

from invoke_agent.auth import APIKeyManager, OAuthManager, MachineManager

# Global references
load_dotenv()
invoke_api_key = os.getenv("INVOKE_API_KEY")
api_key_manager = APIKeyManager()
oauth_manager = OAuthManager()
machine_manager = MachineManager()

# Handle non-JSON responses appropriately
MAX_CHARS = 50000

def extract_error_message(response):
    try:
        # Try to parse JSON response
        data = response.json()

        # Common patterns
        if "error" in data:
            if isinstance(data["error"], dict):
                return data["error"].get("message", str(data["error"]))
            return str(data["error"])
        elif "message" in data:
            return data["message"]

        # Fallback if JSON has no standard error/message
        return json.dumps(data)

    except Exception:
        # Fallback for non-JSON response
        return response.text
        
def route_api_request(method, url, headers=None, params=None, data=None,
                      auth_type="none", auth_name="none", invoke_flag="o", invoke_key='none', timeout=10):
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
        "auth_name": auth_name,
        "invoke_flag": invoke_flag,
        "invoke_key": invoke_key
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

# --- The execute_api_call Function with Modularization, Flexible Injection, and Non-JSON Handling ---
def execute_api_call(task: Dict[str, Any]) -> Dict[str, Any]:
    global api_key_manager, oauth_manager
    """Extracts required fields, injects authentication tokens, executes API calls, and handles non-JSON responses."""
    try:
        # Step 1: There is No Step One
        
        # Step 2: Extract required fields
        method = task.get("method", "GET").upper()
        url = task.get("url")
        params = task.get("parameters", {})
        auth_code = task.get("auth_code", "none")  # Default to 'none'
        
        if not url:
            return {"error": "❌ No URL provided in the action."}

        default_headers = {"Content-Type": "application/json"}
        headers = task.get("headers", {})
        headers = {**default_headers, **headers}
        
        auth_type = None
        auth_name = None
        invoke_flag = None
        if auth_code != 'none':
            auth_code = auth_code.split('::')
            auth_type = auth_code[0]
            auth_name = auth_code[1]
            try:
                invoke_flag = auth_code[2]
            except IndexError:
                invoke_flag = None
        
            # Local Integrations
            if invoke_flag != 'i':
                # Step 4: API Key Injection (only if auth_type is 'query', 'header', or 'body')
                if auth_type in ("query", "header", "body"):
                    api_key = api_key_manager.get_api_key(url)
                    parsed_url = urlparse(url)
                    query_params = dict(parse_qsl(parsed_url.query))
                    if auth_type == "query":
                        query_params[auth_name] = api_key
                    elif auth_type == "header":
                        headers["Authorization"] = f"Bearer {api_key}"
                    elif auth_type == "body":
                        params[auth_name] = api_key
                    # Rebuild the URL with updated query parameters
                    url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(query_params, doseq=True)}"

                # Step 4.3333: OAuth Token Injection (only if auth_type is 'oauth')
                if auth_type == "oauth":
                    try:
                        oauth_token = oauth_manager.get_oauth_token(url)
                        headers["Authorization"] = f"{auth_name} {oauth_token}"
                    except ValueError:
                        return {"error": "❌ OAuth token retrieval failed."}
                
                # Step 4.6667: Machine Token Injection (only if auth_type is 'machine')
                if auth_type == "machine":
                    try:
                        machine_token = machine_manager.get_oauth_token(url)
                        headers["Authorization"] = f"{auth_name} {machine_token}"
                    except ValueError:
                        return {"error": "❌ Machine token retrieval failed."}

        # Step 5: For GET requests, merge parameters into the URL
        if method == "GET":
            parsed_url = urlparse(url)
            query_params = dict(parse_qsl(parsed_url.query))
            query_params.update(params)
            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(query_params, doseq=True)}"
            payload = None
        else:
            payload = json.dumps(params)

        # Step 6: Execute the API Request
        if invoke_flag != 'i':
            response = requests.request(method, url, headers=headers, data=payload, timeout=10)
        else:
            response = route_api_request(method,
                                     url,
                                     headers=headers,
                                     data=payload,
                                     auth_type=auth_type,
                                     auth_name=auth_name,
                                     invoke_flag=invoke_flag,
                                     invoke_key=invoke_api_key,
                                     timeout=10)


        if response.ok:
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                text = response.text[:MAX_CHARS]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"partial_response": text, "note": "⚠️ Truncated invalid JSON"}
            else:
                return {
                    "content_type": content_type,
                    "text": response.text[:MAX_CHARS],
                    "status_code": response.status_code
                }
        else:
            return {"error": f"❌ HTTP {response.status_code} -+- 💀 ERR0R: {extract_error_message(response)}"}

    except json.JSONDecodeError:
        return {"error": "❌ Invalid JSON format received"}
    except requests.exceptions.Timeout:
        return {"error": "⏳ Request timed out"}
    except Exception as e:
        return {"error": f"⚠️ {str(e)}"}
    
# Tool definition
@tool
def api_executor(method: str, url: str, auth_code: str, parameters: Optional[dict] = None, headers: Optional[dict] = None) -> str:
    """Execute HTTP requests using the Invoke framework."""
    return execute_api_call({
        "method": method,
        "url": url,
        "auth_code": auth_code,
        "parameters": parameters or {},
        "headers": headers or {}
    })