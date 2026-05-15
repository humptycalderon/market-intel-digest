# market-intel-digest

Weekly AI market intelligence system that monitors HN, arXiv, and RSS feeds,
synthesizes signals with Claude Opus 4.6, and delivers structured briefings
to the team automatically every Monday.

## What runs weekly

| Time | Job | Output |
|------|-----|--------|
| 7am Monday | Market intel digest | Telegram channel |
| 9am Monday | Dev team product report | Notion + Slack |

## Setup

\`\`\`bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # add your keys
\`\`\`

## Usage

\`\`\`bash
# Market intelligence digest
python run_digest.py

# Dev team product report
python run_dev_report.py
\`\`\`

See \`.env.example\` for required API keys.
