# n8n Workflow to Python Converter

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![n8n](https://img.shields.io/badge/n8n-compatible-orange?logo=n8n)](https://n8n.io)

> Convert n8n automation workflow JSON files into clean, executable Python scripts — instantly.

---

## What it does

You have an n8n workflow like this:

```
[Schedule] → [HTTP Request] → [Send Slack Message]
```

Run one command:

```bash
python converter.py my_workflow.json
```

And get a ready-to-run Python file:

```python
import schedule, time, requests
from slack_sdk import WebClient

def run_every_day_at_9am():
    response = requests.get("https://api.example.com/data")
    data = response.json()

    client = WebClient(token=os.getenv('SLACK_TOKEN'))
    client.chat_postMessage(channel="#general", text=str(data))

schedule.every().hour.do(run_every_day_at_9am)
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Supported Node Types

| Category   | Nodes |
|------------|-------|
| Triggers   | Manual, Schedule, Webhook |
| Logic      | IF, Switch, Merge, Set |
| HTTP       | HTTP Request |
| Code       | Code, Function |
| Services   | Slack, Gmail, Airtable, PostgreSQL, MySQL, Notion |
| AI / LLM   | OpenAI, Anthropic/Claude |
| Everything else | Generic fallback with TODO comments |

---

## Installation

```bash
git clone https://github.com/yourusername/n8n-workflow-to-python
cd n8n-workflow-to-python
pip install -r requirements.txt
```

No external libraries are needed for the converter itself — only for the *generated* scripts (e.g. `requests`, `slack-sdk`, etc.).

---

## Usage

**Basic:**
```bash
python converter.py workflow.json
```

**Custom output filename:**
```bash
python converter.py workflow.json -o my_automation.py
```

**Verbose mode** (shows all nodes and connections before converting):
```bash
python converter.py workflow.json --verbose
```

**Help:**
```bash
python converter.py --help
```

---

## Quick Start Example

1. Try the included example:

```bash
python converter.py examples/slack_alert.json --verbose
```

2. This produces `slack_daily_alert.py` — open it, fill in your credentials, run it.

---

## How It Works

The converter has 6 steps:

1. **Load** — reads the JSON file with `json.load()`
2. **Extract nodes** — parses each node's `name`, `type`, and `parameters`
3. **Extract connections** — builds the execution flow from node to node
4. **Map types** — looks up each node type in a templates dictionary
5. **Generate code** — calls the matching generator function per node
6. **Write file** — outputs a complete, formatted Python script

Each n8n node type has its own generator function (e.g. `_gen_http_request`, `_gen_slack_node`). Adding support for a new node type means adding one function.

---

## Environment Variables

Generated scripts use `os.getenv()` for credentials. Create a `.env` file:

```bash
SLACK_TOKEN=xoxb-your-token
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
GMAIL_USER=you@gmail.com
GMAIL_PASSWORD=your-app-password
AIRTABLE_TOKEN=pat-your-token
DATABASE_URL=postgresql://user:pass@localhost/db
NOTION_TOKEN=secret_your-token
```

Install `python-dotenv` and the script loads it automatically:
```bash
pip install python-dotenv
```

---

## Project Structure

```
n8n-workflow-to-python/
├── converter.py        ← Main converter (single file, no dependencies)
├── requirements.txt    ← Optional packages for generated scripts
├── examples/
│   └── slack_alert.json  ← Sample n8n workflow to test with
└── README.md
```

---

## Contributing

Want to add support for more node types? It's easy:

1. Add a new function `_gen_yournode(node)` that returns a list of Python code lines
2. Add it to the `NODE_TEMPLATES` dict with the node's type string

Example:
```python
def _gen_telegram_node(node):
    return [
        "# Telegram — send message",
        "import requests",
        f"requests.post(f'https://api.telegram.org/bot{{os.getenv(\"TELEGRAM_TOKEN\")}}/sendMessage', ...)",
    ]

NODE_TEMPLATES["n8n-nodes-base.telegram"] = _gen_telegram_node
```

---

## License

MIT © 2024

---

*Built to make 2055+ n8n workflows accessible as Python code.*
