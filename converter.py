"""
n8n Workflow to Python Converter
Converts n8n JSON workflow files into executable Python scripts.

Usage:
    python converter.py workflow.json
    python converter.py workflow.json -o my_script.py
    python converter.py workflow.json --verbose
"""

import json
import argparse
import os
import sys
from datetime import datetime


# ─────────────────────────────────────────
#  STEP 1: Read & parse the JSON file
# ─────────────────────────────────────────

def load_workflow(filepath):
    """Read an n8n JSON file and return it as a Python dictionary."""
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    if not filepath.endswith(".json"):
        print(f"[WARNING] File does not have .json extension: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON: {e}")
            sys.exit(1)

    return data


# ─────────────────────────────────────────
#  STEP 2: Extract nodes and connections
# ─────────────────────────────────────────

def extract_nodes(workflow_data):
    """
    n8n workflows have a 'nodes' list.
    Each node has: name, type, parameters, position, etc.
    Returns a clean list of node dicts.
    """
    nodes = workflow_data.get("nodes", [])
    clean_nodes = []
    for node in nodes:
        clean_nodes.append({
            "name":       node.get("name", "Unnamed"),
            "type":       node.get("type", "unknown"),
            "parameters": node.get("parameters", {}),
            "disabled":   node.get("disabled", False),
        })
    return clean_nodes


def extract_connections(workflow_data):
    """
    Connections define the flow: which node sends data to which.
    Returns a list of (from_node, to_node) tuples.
    """
    connections = workflow_data.get("connections", {})
    edges = []
    for source_node, outputs in connections.items():
        main_outputs = outputs.get("main", [])
        for output_group in main_outputs:
            if output_group:
                for target in output_group:
                    target_node = target.get("node", "")
                    if target_node:
                        edges.append((source_node, target_node))
    return edges


# ─────────────────────────────────────────
#  STEP 3: Helper utilities
# ─────────────────────────────────────────

def _safe_name(name):
    """Convert 'HTTP Request 1' → valid Python variable 'http_request_1'."""
    safe = name.lower().strip()
    safe = safe.replace(" ", "_").replace("-", "_").replace("/", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    if safe and safe[0].isdigit():
        safe = "node_" + safe
    return safe or "node"


# ─────────────────────────────────────────
#  STEP 4: Generator functions (one per node type)
#  Each function receives the node dict and returns a list of Python lines.
# ─────────────────────────────────────────

def _gen_http_request(node):
    p       = node["parameters"]
    method  = p.get("method", "GET").upper()
    url     = p.get("url", "https://example.com")
    headers = p.get("headerParameters", {}).get("parameters", [])
    var     = _safe_name(node["name"])

    lines = [
        f"# [{node['name']}] HTTP Request",
        f"import requests",
        f"",
        f"headers_{var} = {{",
    ]
    for h in headers:
        lines.append(f"    \"{h.get('name', '')}\": \"{h.get('value', '')}\",")
    lines += [
        f"}}",
        f"response_{var} = requests.{method.lower()}(",
        f"    \"{url}\",",
        f"    headers=headers_{var}",
        f")",
        f"data_{var} = response_{var}.json()",
        f"print(f\"[{node['name']}] Status: {{response_{var}.status_code}}\")",
    ]
    return lines


def _gen_code_node(node):
    p        = node["parameters"]
    language = p.get("language", "javaScript")
    code     = p.get("jsCode", p.get("pythonCode", "# No code found"))

    lines = [f"# [{node['name']}] Code Node (original language: {language})"]
    if language == "python":
        lines += ["# --- BEGIN original Python code ---"]
        lines += code.splitlines()
        lines += ["# --- END original Python code ---"]
    else:
        lines += [
            "# Original code was JavaScript — rewrite in Python:",
            "# ---",
        ]
        for line in code.splitlines():
            lines.append(f"# {line}")
        lines.append("# ---")
    return lines


def _gen_function_node(node):
    return _gen_code_node(node)


def _gen_set_node(node):
    p     = node["parameters"]
    fields = p.get("values", {})
    var   = _safe_name(node["name"])
    lines = [f"# [{node['name']}] Set Node — assign values"]
    lines.append(f"{var} = {{")
    for dtype, items in fields.items():
        for item in (items if isinstance(items, list) else []):
            key   = item.get("name", "key")
            value = item.get("value", "")
            lines.append(f"    \"{key}\": {json.dumps(value)},")
    lines.append("}")
    return lines


def _gen_if_node(node):
    var = _safe_name(node["name"])
    return [
        f"# [{node['name']}] IF Node — conditional branch",
        f"condition_{var} = True  # TODO: replace with your actual condition",
        f"if condition_{var}:",
        f"    pass  # true branch",
        f"else:",
        f"    pass  # false branch",
    ]


def _gen_switch_node(node):
    var = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Switch Node — multiple branches",
        f"switch_value_{var} = None  # TODO: replace with actual value",
        f"if switch_value_{var} == 'case1':",
        f"    pass",
        f"elif switch_value_{var} == 'case2':",
        f"    pass",
        f"else:",
        f"    pass  # default",
    ]


def _gen_merge_node(node):
    var = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Merge Node — combines data from branches",
        f"merged_{var} = []  # append data from each branch here",
    ]


def _gen_webhook_trigger(node):
    p    = node["parameters"]
    path = p.get("path", "webhook")
    var  = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Webhook Trigger",
        f"# Workflow starts when HTTP hits: /{path}",
        f"# Use Flask or FastAPI to receive webhooks in Python:",
        f"from flask import Flask, request as flask_request",
        f"app = Flask(__name__)",
        f"",
        f"@app.route('/{path}', methods=['POST', 'GET'])",
        f"def handle_{var}():",
        f"    data = flask_request.json",
        f"    print(f'Received: {{data}}')",
        f"    return {{'status': 'ok'}}",
    ]


def _gen_schedule_trigger(node):
    p   = node["parameters"]
    rule = p.get("rule", {})
    var  = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Schedule Trigger",
        f"# Schedule config: {json.dumps(rule)}",
        f"import schedule, time",
        f"",
        f"def run_{var}():",
        f"    print('Running scheduled workflow...')",
        f"    # Your workflow logic here",
        f"",
        f"schedule.every().hour.do(run_{var})  # adjust interval as needed",
        f"",
        f"while True:",
        f"    schedule.run_pending()",
        f"    time.sleep(60)",
    ]


def _gen_manual_trigger(node):
    return [
        f"# [{node['name']}] Manual Trigger",
        f"# No special trigger needed — just call main() in Python.",
    ]


def _gen_slack_node(node):
    p       = node["parameters"]
    channel = p.get("channel", "#general")
    text    = p.get("text", "Hello from Python!")
    var     = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Slack — send message",
        f"from slack_sdk import WebClient",
        f"",
        f"slack_client_{var} = WebClient(token=os.getenv('SLACK_TOKEN'))",
        f"slack_client_{var}.chat_postMessage(",
        f"    channel=\"{channel}\",",
        f"    text=\"{text}\"",
        f")",
    ]


def _gen_gmail_node(node):
    p       = node["parameters"]
    to      = p.get("toList", ["recipient@example.com"])
    subject = p.get("subject", "No Subject")
    var     = _safe_name(node["name"])
    to_str  = ", ".join(to) if isinstance(to, list) else str(to)
    return [
        f"# [{node['name']}] Gmail — send email",
        f"import smtplib",
        f"from email.mime.text import MIMEText",
        f"",
        f"msg_{var} = MIMEText('Your email body here')",
        f"msg_{var}['Subject'] = \"{subject}\"",
        f"msg_{var}['From']    = os.getenv('GMAIL_USER')",
        f"msg_{var}['To']      = \"{to_str}\"",
        f"",
        f"with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:",
        f"    server.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_PASSWORD'))",
        f"    server.send_message(msg_{var})",
    ]


def _gen_airtable_node(node):
    p    = node["parameters"]
    table = p.get("table", "MyTable")
    base  = p.get("application", "YOUR_BASE_ID")
    var   = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Airtable",
        f"from pyairtable import Table",
        f"",
        f"airtable_{var} = Table(os.getenv('AIRTABLE_TOKEN'), \"{base}\", \"{table}\")",
        f"records_{var}  = airtable_{var}.all()",
    ]


def _gen_postgres_node(node):
    p     = node["parameters"]
    query = p.get("query", "SELECT * FROM your_table LIMIT 10")
    var   = _safe_name(node["name"])
    return [
        f"# [{node['name']}] PostgreSQL",
        f"import psycopg2",
        f"",
        f"conn_{var} = psycopg2.connect(os.getenv('DATABASE_URL'))",
        f"cur_{var}  = conn_{var}.cursor()",
        f"cur_{var}.execute(\"\"\"{query}\"\"\")",
        f"rows_{var} = cur_{var}.fetchall()",
        f"cur_{var}.close()",
        f"conn_{var}.close()",
    ]


def _gen_mysql_node(node):
    p     = node["parameters"]
    query = p.get("query", "SELECT * FROM your_table LIMIT 10")
    var   = _safe_name(node["name"])
    return [
        f"# [{node['name']}] MySQL",
        f"import mysql.connector",
        f"",
        f"conn_{var} = mysql.connector.connect(",
        f"    host=os.getenv('MYSQL_HOST'),",
        f"    user=os.getenv('MYSQL_USER'),",
        f"    password=os.getenv('MYSQL_PASSWORD'),",
        f"    database=os.getenv('MYSQL_DATABASE')",
        f")",
        f"cur_{var} = conn_{var}.cursor()",
        f"cur_{var}.execute(\"{query}\")",
        f"rows_{var} = cur_{var}.fetchall()",
    ]


def _gen_notion_node(node):
    p     = node["parameters"]
    db_id = p.get("databaseId", {})
    if isinstance(db_id, dict):
        db_id = db_id.get("value", "YOUR_DATABASE_ID")
    var   = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Notion",
        f"from notion_client import Client",
        f"",
        f"notion_{var} = Client(auth=os.getenv('NOTION_TOKEN'))",
        f"results_{var} = notion_{var}.databases.query(database_id=\"{db_id}\")",
    ]


def _gen_openai_node(node):
    p      = node["parameters"]
    model  = p.get("model", "gpt-4o")
    if isinstance(model, dict):
        model = model.get("value", "gpt-4o")
    prompt = p.get("prompt", "Your prompt here")
    if isinstance(prompt, dict):
        prompt = prompt.get("value", "Your prompt here")
    var    = _safe_name(node["name"])
    return [
        f"# [{node['name']}] OpenAI",
        f"from openai import OpenAI",
        f"",
        f"openai_client_{var} = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))",
        f"response_{var} = openai_client_{var}.chat.completions.create(",
        f"    model=\"{model}\",",
        f"    messages=[{{\"role\": \"user\", \"content\": \"{prompt}\"}}]",
        f")",
        f"output_{var} = response_{var}.choices[0].message.content",
        f"print(output_{var})",
    ]


def _gen_anthropic_node(node):
    var = _safe_name(node["name"])
    return [
        f"# [{node['name']}] Anthropic / Claude",
        f"import anthropic",
        f"",
        f"anthropic_client_{var} = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))",
        f"message_{var} = anthropic_client_{var}.messages.create(",
        f"    model=\"claude-3-5-sonnet-20241022\",",
        f"    max_tokens=1024,",
        f"    messages=[{{\"role\": \"user\", \"content\": \"Your prompt here\"}}]",
        f")",
        f"output_{var} = message_{var}.content[0].text",
    ]


def _gen_generic_node(node):
    """Fallback for any node type not explicitly supported."""
    short_type = node["type"].split(".")[-1]
    var = _safe_name(node["name"])
    return [
        f"# [{node['name']}] {node['type']}",
        f"# TODO: Implement '{short_type}' logic",
        f"# Parameters: {json.dumps(node['parameters'])}",
        f"{var}_result = None  # replace with real implementation",
    ]


# ─────────────────────────────────────────
#  STEP 5: Mapping table  (defined AFTER functions)
# ─────────────────────────────────────────

NODE_TEMPLATES = {
    # HTTP
    "n8n-nodes-base.httpRequest": _gen_http_request,

    # Code
    "n8n-nodes-base.code":     _gen_code_node,
    "n8n-nodes-base.function": _gen_function_node,

    # Logic
    "n8n-nodes-base.set":    _gen_set_node,
    "n8n-nodes-base.if":     _gen_if_node,
    "n8n-nodes-base.switch": _gen_switch_node,
    "n8n-nodes-base.merge":  _gen_merge_node,

    # Triggers
    "n8n-nodes-base.webhook":         _gen_webhook_trigger,
    "n8n-nodes-base.scheduleTrigger": _gen_schedule_trigger,
    "n8n-nodes-base.manualTrigger":   _gen_manual_trigger,

    # Services
    "n8n-nodes-base.slack":    _gen_slack_node,
    "n8n-nodes-base.gmail":    _gen_gmail_node,
    "n8n-nodes-base.airtable": _gen_airtable_node,
    "n8n-nodes-base.postgres": _gen_postgres_node,
    "n8n-nodes-base.mysql":    _gen_mysql_node,
    "n8n-nodes-base.notion":   _gen_notion_node,

    # AI
    "@n8n/n8n-nodes-langchain.openAi":          _gen_openai_node,
    "@n8n/n8n-nodes-langchain.lmChatOpenAi":    _gen_openai_node,
    "@n8n/n8n-nodes-langchain.lmChatAnthropic": _gen_anthropic_node,
}


# ─────────────────────────────────────────
#  STEP 6: Build the complete Python script
# ─────────────────────────────────────────

def generate_python_script(workflow_data, verbose=False):
    """Converts the workflow dict into a full Python script string."""
    name        = workflow_data.get("name", "Unnamed Workflow")
    nodes       = extract_nodes(workflow_data)
    connections = extract_connections(workflow_data)

    if verbose:
        print(f"\n📋 Workflow: {name}")
        print(f"   Nodes ({len(nodes)}):")
        for n in nodes:
            status = "⚠️  disabled" if n["disabled"] else "✅"
            print(f"   {status} {n['name']:30s}  ({n['type']})")
        print(f"\n   Connections ({len(connections)}):")
        for src, dst in connections:
            print(f"   {src} → {dst}")
        print()

    lines = [
        '"""',
        f"Auto-generated Python script from n8n workflow: {name}",
        f"Generated by: n8n-workflow-to-python",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Nodes: {len(nodes)}",
        "",
        "⚠️  This is a starting point — review and adjust before running.",
        '"""',
        "",
        "import os",
        "import json",
        "",
        "# Optional: load .env file  (pip install python-dotenv)",
        "try:",
        "    from dotenv import load_dotenv",
        "    load_dotenv()",
        "except ImportError:",
        "    pass",
        "",
        "",
        "def main():",
        f"    print('Starting: {name}')",
        "",
    ]

    for i, node in enumerate(nodes):
        sep = "─" * 50
        lines.append(f"    # {sep}")
        lines.append(f"    # Node {i+1}/{len(nodes)}: {node['name']}")
        lines.append(f"    # Type: {node['type']}")
        lines.append(f"    # {sep}")

        if node["disabled"]:
            lines.append(f"    # (disabled — skipped)")
            lines.append("")
            continue

        gen_func   = NODE_TEMPLATES.get(node["type"], _gen_generic_node)
        node_lines = gen_func(node)
        for code_line in node_lines:
            lines.append(f"    {code_line}")
        lines.append("")

    if connections:
        lines.append("    # ── Execution flow ──")
        for src, dst in connections:
            lines.append(f"    # {src}  →  {dst}")
        lines.append("")

    lines += [
        "    print('Done!')",
        "",
        "",
        "if __name__ == '__main__':",
        "    main()",
        "",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────
#  STEP 7: CLI (argparse)
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert an n8n workflow JSON file to a Python script.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python converter.py my_workflow.json
  python converter.py my_workflow.json -o output.py
  python converter.py my_workflow.json --verbose
        """
    )
    parser.add_argument("input",  help="n8n workflow JSON file")
    parser.add_argument("-o", "--output",  default=None,
                        help="Output .py file (default: <workflow_name>.py)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print node/connection details")

    args = parser.parse_args()

    workflow_data = load_workflow(args.input)
    python_code   = generate_python_script(workflow_data, verbose=args.verbose)

    if args.output:
        output_path = args.output
    else:
        workflow_name = workflow_data.get("name", "workflow")
        output_path   = f"{_safe_name(workflow_name)}.py"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(python_code)

    print(f"✅  Converted!  →  {output_path}")
    print(f"    Nodes processed: {len(workflow_data.get('nodes', []))}")
    print(f"    Run with: python {output_path}")


if __name__ == "__main__":
    main()
