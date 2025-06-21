import json
from urllib.parse import quote_plus

def merge_headers(global_headers: dict, endpoint_headers: dict) -> dict:
    """
    Combine global and endpoint-specific headers into a single dict.
    Endpoint headers override any global headers with the same name.
    
    Args:
        global_headers (dict): Headers defined at the top level (applies to all endpoints).
        endpoint_headers (dict): Headers defined for this specific endpoint.
    
    Returns:
        dict: The merged headers.
    """
    headers = {}
    # Start with globals…
    if global_headers:
        headers.update(global_headers)
    # …then overlay endpoint-specific overrides
    if endpoint_headers:
        headers.update(endpoint_headers)
    return headers

def render_agents_txt(agent_json_str: str) -> str:
    """
    Render an 'agents.txt' description from a JSON specification.
    This output guides an LLM: it shows the base URL, authentication,
    headers, and for each endpoint, the URL template plus parameter
    names/descriptions, so the LLM knows what to fill in.
    
    Args:
        agent_json_str (str): The raw JSON text of agents.json.
    
    Returns:
        str: A multi-line string in Markdown-like format.
    """
    # Parse the JSON string into a Python dict
    agent = json.loads(agent_json_str)

    # ── Top‑level sanity checks ─────────────────────────────────────────────
    # Ensure required top-level keys are present
    if "base_url" not in agent:
        raise ValueError("agents.json must include a 'base_url'")
    if "endpoints" not in agent or not isinstance(agent["endpoints"], list):
        raise ValueError("agents.json must include an 'endpoints' list")

    # Determine the human-readable label for this agent
    label = agent.get("label") or agent.get("agent", "").capitalize()

    # This list will accumulate each line of our output
    lines = []

    # ── Header section ─────────────────────────────────────────────────────
    # Title of the agent
    lines.append(f"# {label}")
    # Base URL (stripping the 'https://')
    lines.append(f"Base URL: {agent['base_url'].replace('https://', '')}")

    # Handle default authentication, if provided
    default_auth = agent.get("auth") or {}
    default_auth_code = None
    if default_auth:
        # Join type, format, and code into a single string e.g. "Bearer::Token::abc123"
        parts = [default_auth.get("type"), default_auth.get("code")]
        default_auth_code = "::".join(filter(None, parts))
        lines.append(f"Auth Code: {default_auth_code}")

    # Render any global headers
    global_headers = agent.get("headers", {})
    if global_headers:
        lines.append("Headers:")
        for header_name, header_value in global_headers.items():
            lines.append(f"- {header_name}: {header_value}")

    # Blank line for readability
    lines.append("")
    # Separator and label
    lines.append(f"## ✉️ {label} ##")
    lines.append("---")
    lines.append("")

    # ── Example‑call builder ────────────────────────────────────────────────
    def build_example_call(method: str, url: str,
                           auth_code: str = None,
                           parameters: dict = None,
                           headers: dict = None) -> dict:
        """
        Construct the minimal JSON object that the LLM will emit when making a call.
        
        Args:
            method (str): HTTP verb, e.g. "GET" or "POST".
            url (str): Fully-resolved URL including any {placeholders}.
            auth_code (str, optional): Authentication code string.
            parameters (dict, optional): Body or query parameters for the call.
            headers (dict, optional): Any HTTP headers.
        
        Returns:
            dict: A JSON-serializable dict representing the call.
        """
        call = {"method": method, "url": url}
        if auth_code:
            call["auth_code"] = auth_code
        if headers:
            call["headers"] = headers
        if parameters:
            call["parameters"] = parameters
        return call

    # ── Iterate over each endpoint definition ───────────────────────────────
    for ep in agent["endpoints"]:
        # Ensure each endpoint has the minimal required keys
        for required in ("name", "method", "path"):
            if required not in ep:
                raise ValueError(f"Each endpoint must include '{required}'")

        # Human-readable name for the endpoint
        name        = ep.get("label", ep["name"])
        # Normalize HTTP method to uppercase
        method      = ep["method"].upper()
        # URL path template, e.g. "/users/{userId}"
        path        = ep["path"]
        # Parameter definitions: dicts mapping name → description
        path_params = ep.get("path_params", {})   # required path parameters
        qparams     = ep.get("query_params", {})  # optional query parameters
        body_params = ep.get("body_params", {})   # body schema for writes

        # Merge headers (global + any endpoint-specific overrides)
        ep_headers  = merge_headers(global_headers, ep.get("headers", {}))
        # Determine if this endpoint overrides auth
        auth_code   = ep.get("auth_code", default_auth_code)

        # Build the URL template string, preserving {placeholders}
        base_url = agent["base_url"].rstrip("/")
        template = f"{base_url}{path}"
        # If query parameters exist, append "?key={key}&..."
        if qparams:
            sep    = "&" if "?" in template else "?"
            qp_str = "&".join(f"{k}={{{k}}}" for k in qparams.keys())
            template = f"{template}{sep}{qp_str}"

        # ── Render the endpoint block ────────────────────────────────────────
        lines.append(f"Endpoint: {name}")
        lines.append(f"Description: {ep.get('description', '')}")
        lines.append(f"Method: {method}")
        lines.append(f"URL Template: {template}")

        # List out each path parameter with its description
        if path_params:
            lines.append("Path Parameters:")
            for param_name, param_desc in path_params.items():
                lines.append(f"- {param_name}: {param_desc}")

        # List out each query parameter with its description
        if qparams:
            lines.append("Query Parameters (optional):")
            for param_name, param_desc in qparams.items():
                lines.append(f"- {param_name}: {param_desc}")

        # Render combined headers for this endpoint
        if ep_headers:
            lines.append("Headers:")
            for header_name, header_value in ep_headers.items():
                lines.append(f"- {header_name}: {header_value}")

        # List body parameters (for POST, PUT, PATCH)
        if body_params and method in ("POST", "PUT", "PATCH"):
            lines.append("Body Parameters:")
            for param_name, param_desc in body_params.items():
                lines.append(f"- {param_name}: {param_desc}")

        # Render any explicit examples provided in the JSON
        for ex in ep.get("examples", []):
            # Example may override URL, headers, auth_code, and supply actual values
            ex_url     = ex.get("url", template)
            ex_params  = ex.get("parameters")
            ex_headers = ex.get("headers", ep_headers)
            ex_auth    = ex.get("auth_code", auth_code)
            call       = build_example_call(method, ex_url, ex_auth, ex_params, ex_headers)

            lines.append("Examples:")
            lines.append("```json")
            lines.append(json.dumps(call, indent=2, ensure_ascii=False))
            lines.append("```")

        # Any free-form notes about this endpoint
        if ep.get("notes"):
            lines.append("Notes:")
            for note in ep["notes"]:
                lines.append(f"- {note}")

        # Separator between endpoints
        lines.append("---")
        lines.append("")

    # Join all lines into a single string to return
    return "\n".join(lines)
