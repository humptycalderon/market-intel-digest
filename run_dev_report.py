"""
Dev Team Product Report — weekly synthesis of market signals into
actionable product recommendations for the development team.

Runs after the market intelligence digest (Mondays at 9am).

Usage:
  python run_dev_report.py                 # full run: markdown + Notion + Slack
  python run_dev_report.py --no-notion     # skip Notion
  python run_dev_report.py --no-slack      # skip Slack
  python run_dev_report.py --no-arxiv      # skip arXiv (faster)
  python run_dev_report.py --days 7        # look back N days (default: 7)
  python run_dev_report.py --out report.md # custom output file
"""

import os
import sys
import logging
import argparse
from datetime import date
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

from intelligence.sources import hn_intel, arxiv_intel, rss_intel
from intelligence import dev_synthesizer, notion_digest, slack_report


def main():
    parser = argparse.ArgumentParser(description="Generate dev team product report")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--no-arxiv", action="store_true", help="Skip arXiv source")
    parser.add_argument("--no-rss", action="store_true", help="Skip RSS feeds")
    parser.add_argument("--no-notion", action="store_true", help="Skip Notion publish")
    parser.add_argument("--no-slack", action="store_true", help="Skip Slack delivery")
    parser.add_argument("--out", default=f"dev_report_{date.today()}.md", help="Output markdown file")
    args = parser.parse_args()

    all_items = []

    # --- Hacker News ---
    log.info("Collecting HN signals …")
    hn_items = hn_intel.fetch(days_back=args.days)
    all_items.extend(hn_items)

    # --- arXiv ---
    if not args.no_arxiv:
        log.info("Collecting arXiv signals …")
        arxiv_items = arxiv_intel.fetch(days_back=args.days)
        all_items.extend(arxiv_items)
    else:
        log.info("arXiv: skipped")

    # --- RSS ---
    if not args.no_rss:
        log.info("Collecting RSS signals …")
        rss_items = rss_intel.fetch(days_back=args.days)
        all_items.extend(rss_items)
    else:
        log.info("RSS: skipped")

    log.info(f"Total signals: {len(all_items)} items collected")

    if not all_items:
        log.warning("No signals found. Check your network or expand the date range with --days.")
        sys.exit(0)

    # --- Synthesize with Claude ---
    # Pass the directory where digest_*.md files are saved so the
    # synthesizer can load the latest digest for additional context.
    digest_dir = os.path.dirname(os.path.abspath(__file__))
    report = dev_synthesizer.synthesize(all_items, digest_dir=digest_dir)
    if not report:
        log.error("Synthesis failed. Check ANTHROPIC_API_KEY.")
        sys.exit(1)

    # --- Save markdown ---
    today = date.today().isoformat()
    header = f"# Dev Team Product Report — {today}\n\n"
    full_content = header + report

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(full_content)
    log.info(f"Report saved to {args.out}")

    # --- Print to terminal ---
    print("\n" + "=" * 70)
    print(full_content)
    print("=" * 70 + "\n")

    # --- Notion ---
    if not args.no_notion:
        page_url = notion_digest.push(report, run_date=today, title_prefix="Dev Report")
        if page_url:
            print(f"Notion page: {page_url}")
    else:
        log.info("Notion publish: skipped")

    # --- Slack ---
    if not args.no_slack:
        slack_report.send(report, date_str=today)
    else:
        log.info("Slack delivery: skipped")


if __name__ == "__main__":
    main()
