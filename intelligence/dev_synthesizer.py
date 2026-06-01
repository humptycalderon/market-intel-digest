"""
Dev team synthesizer: translates market signals and prospect pain points
into product-focused insights and recommendations for the development team.
"""

import os
import glob
import logging
import anthropic
from datetime import datetime

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a product intelligence analyst for an AI data platform that supplies \
high-consistency human evaluators and longitudinal behavioral data. The primary \
growth focus is agent evaluation: companies building or deploying AI agents that \
need human evaluators to assess multi-step trajectories, verify agent output \
quality, and validate compatibility claims that automated metrics cannot judge. \
RLHF and LLM benchmarking remain the foundation. Physical AI and robotics are \
a high-priority subset of agent evaluation — not a separate category.

Your job is to translate raw market signals — HN discussions, arXiv papers, \
RSS articles, and scored prospect data — into a concise, actionable report \
for the internal development team.

Focus on:
- Agent evaluation gaps: where automated metrics fall short and human judgment \
  is required — especially for multi-step plans, tool use, and trajectory quality
- Emerging research in agent benchmarking, RLHF, and agentic workflow evaluation
- Recurring pain points around agent output trust, verification, and accountability
- Physical AI signals as a subset: robotics policy compatibility, embodied AI \
  evaluation, and agent-generated claim verification needing domain-expert humans
- What competitors or alternative approaches are gaining traction
- Concrete, specific product recommendations (not vague suggestions)

Tone: direct, technical, internal. No marketing language. \
Write as if briefing a senior engineer who has 10 minutes."""

REPORT_PROMPT = """\
Below are this week's market signals. Synthesize them into a dev team product report.

SIGNALS:
{signals}

LATEST MARKET DIGEST (for additional context):
{digest}

---

Produce the following sections. Be specific — cite sources, name pain points, \
reference papers or discussions where relevant.

## Feature Demand
What capabilities are prospects and the research community repeatedly asking for \
that we do or don't yet offer? Rank by frequency/urgency.

## Research Pipeline
2–3 arXiv or newsletter findings that will affect our roadmap in the next \
1–3 months. What should engineering be aware of before it becomes mainstream?

## Unmet Data Quality Gaps
What evaluation, annotation, or consistency problems keep surfacing that \
our platform could solve but hasn't fully addressed yet?

## Competitive Landscape
What alternatives (tools, approaches, labs building in-house) are gaining \
traction? Where are we differentiated and where are we at risk?

## Product Recommendations
Exactly 3 concrete, actionable recommendations for the dev team this week. \
Format each as: [Priority: High/Medium/Low] — What to build/change and why."""


def _load_latest_digest(digest_dir="."):
    """Load the most recent digest markdown file for context."""
    pattern = os.path.join(digest_dir, "digest_*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        return "No digest available."
    try:
        with open(files[0]) as f:
            return f.read()[:3000]
    except Exception:
        return "Could not load digest."


def _format_signals(items):
    """Format signal items into a readable block for the prompt."""
    if not items:
        return "No signals collected."
    lines = []
    for item in items[:60]:  # cap to avoid token overflow
        source = item.get("source", "unknown").upper()
        title = item.get("title", "")[:120]
        text = item.get("text") or item.get("abstract", "")
        text = text[:300] if text else ""
        url = item.get("url", "")
        lines.append(f"[{source}] {title}\n  {text}\n  {url}\n")
    return "\n".join(lines)


def synthesize(items, digest_dir=".", api_key=None):
    """
    Synthesize market signals into a dev team product report.
    Returns the report as a markdown string.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set — cannot synthesize report")
        return None

    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    digest_text = _load_latest_digest(digest_dir)
    signals_text = _format_signals(items)

    prompt = REPORT_PROMPT.format(signals=signals_text, digest=digest_text)

    log.info(f"Synthesizing dev report from {len(items)} signals with Claude Opus 4.6 …")
    try:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()

        text_blocks = [
            block.text for block in message.content
            if hasattr(block, "text")
        ]
        report = "\n\n".join(text_blocks).strip()
        log.info("Dev report synthesis complete.")
        return report

    except Exception as e:
        log.error(f"Dev report synthesis failed: {e}")
        return None
