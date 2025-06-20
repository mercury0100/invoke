import os
import yaml
import json
import requests
from datetime import datetime
from typing import Optional, Union, Dict, Any, List

from invoke_agent.compile import render_agents_txt
from invoke_agent import io

# Constants
INVOKE_AGENT_BASE_URL = "https://invoke.network/api/agents-txt"
AGENTS_MAP_PATH = os.path.expanduser("./agents_map.yaml")

def get_current_datetime() -> str:
    now = datetime.now().astimezone()  # Attaches local timezone info
    human_readable = now.strftime("%A, %B %d, %Y at %I:%M %p")
    timezone_str = now.tzname()

    return f"""
The current date and time is {human_readable}.
The local timezone is {timezone_str}.
"""

# Default system context block
DEFAULT_CONTEXT = f"""
{get_current_datetime()}
You are an assistant with access to the Invoke Network, a dynamic HTTP execution framework for AI Agents.
You must output JSON-structured actions using the format shown below.

---

**Example API call:**
```json
{{
  "method": "GET",
  "url": "https://www.example.com/data",
  "auth_code": "example::auth::code",
  "parameters": {{}},
  "headers": {{}}
}}
```
If you are asked to perform a task involving the web, assume it is through this framework.
Reason through steps and chain together actions to complete complex tasks.
The framework takes care of API keys, OAuth credentials and OAuth flow.
If the user needs to login, return the full oauth link as a string to the user.
Once a request has been fulfilled, return a final answer to the user.
Do not announce actions, just do them. Seek confirmation if unsure.

---

Here are your current integrations:
"""


def load_agents_map(
    source: Optional[Union[str, List[Union[str, dict]]]] = None
    ) -> Dict[str, str]:
    """
    Load agent definitions as name->text:
    - If source is a list, use those entries.
    - If source is a string, treat it as a path to a YAML file.
    - If source is None and agents_map.yaml exists, load it.
    - Otherwise return {}.
    Supports built-in aliases, local files, remote URLs, and explicit mappings.
    """
    # Determine raw entries
    if isinstance(source, list):
        raw_entries = source
    elif isinstance(source, str):
        if os.path.exists(source):
            with open(source, 'r') as f:
                raw_entries = yaml.safe_load(f) or []
        else:
            return {}
    else:
        # source is None
        if os.path.exists(AGENTS_MAP_PATH):
            with open(AGENTS_MAP_PATH, 'r') as f:
                raw_entries = yaml.safe_load(f) or []
        else:
            raw_entries = []

    agents: Dict[str, str] = {}
    for entry in raw_entries:
        if isinstance(entry, dict):
            name, path = next(iter(entry.items()))
        elif isinstance(entry, str) and (os.path.exists(entry) or entry.startswith(('http://','https://'))):
            # infer name from JSON or filename
            if entry.endswith(('.json', '.txt')):
                name = os.path.splitext(os.path.basename(entry))[0]
            else:
                name = entry.replace('/', '_')
            path = entry
        else:
            # built-in alias
            name = entry
            path = f"{INVOKE_AGENT_BASE_URL}/{entry}"

        try:
            if path.startswith(('http://','https://')):
                resp = requests.get(path)
                resp.raise_for_status()
                content = resp.text
            else:
                with open(path, 'r') as f:
                    content = f.read()

            # Render JSON to agents.txt if needed
            try:
                json.loads(content)
                agents[name] = render_agents_txt(content)
            except json.JSONDecodeError:
                agents[name] = content

        except Exception as e:
            io.io.notify(f"Failed to load '{name}' from '{path}': {e}")

    return agents


def build_context(
    base_prompt: str = '',
    agents: Optional[Union[str, List[Union[str, dict]]]] = None
    ) -> str:
    """
    Build the full system prompt for the agent:
    - Use `base_prompt` if provided, else DEFAULT_CONTEXT.
    - Load agents via load_agents_map(source=agents).
    - Append each integration's text under a header.
    """
    prompt = base_prompt or DEFAULT_CONTEXT
    agents_dict = load_agents_map(source=agents)
    integrations_text = "\n\n".join(f"# {name}\n{body}" for name, body in agents_dict.items())
    return f"{prompt}\n\n{integrations_text}"
