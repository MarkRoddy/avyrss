#!/usr/bin/env python3
"""
Offline operations management script for AvyRSS.

This script provides commands for:
- Downloading forecasts
- Generating RSS feeds
- Generating the HTML index page
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.avalanche import AvalancheConfig
from app.forecasts import download_forecast_for_zone, download_all_forecasts
from app.rss import generate_feed_for_zone, generate_all_feeds
from app.html_generator import generate_index_html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_full_update(args):
    """Download forecasts and generate feeds for all zones."""
    logger.info("Starting full update...")

    config = AvalancheConfig(args.config)

    # Download forecasts
    logger.info("Step 1/2: Downloading forecasts for all zones...")
    download_results = download_all_forecasts(config, base_dir=args.forecasts_dir)

    # Generate feeds
    logger.info("Step 2/2: Generating RSS feeds for all zones...")
    feed_results = generate_all_feeds(
        config,
        base_url=args.base_url,
        forecasts_dir=args.forecasts_dir,
        feeds_dir=args.feeds_dir
    )

    # Print summary
    print("\n" + "="*60)
    print("FULL UPDATE COMPLETE")
    print("="*60)
    print(f"Forecasts downloaded: {download_results['success']}/{download_results['total']}")
    print(f"RSS feeds generated:  {feed_results['success']}/{feed_results['total']}")
    print("="*60)


def cmd_download_forecast(args):
    """Download forecast for a single zone."""
    config = AvalancheConfig(args.config)

    logger.info(f"Downloading forecast for {args.center}/{args.zone}...")

    success, message, file_path = download_forecast_for_zone(
        args.center,
        args.zone,
        config,
        base_dir=args.forecasts_dir
    )

    if success:
        print(f"✓ {message}")
        print(f"  Saved to: {file_path}")
    else:
        print(f"✗ {message}", file=sys.stderr)
        sys.exit(1)


def cmd_generate_feed(args):
    """Generate RSS feed for a single zone."""
    config = AvalancheConfig(args.config)

    logger.info(f"Generating RSS feed for {args.center}/{args.zone}...")

    try:
        file_path = generate_feed_for_zone(
            args.center,
            args.zone,
            config,
            base_url=args.base_url,
            forecasts_dir=args.forecasts_dir,
            feeds_dir=args.feeds_dir
        )
        print(f"✓ RSS feed generated successfully")
        print(f"  Saved to: {file_path}")
    except Exception as e:
        print(f"✗ Error generating feed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_generate_index(args):
    """Generate the HTML index page."""
    config = AvalancheConfig(args.config)

    logger.info("Generating HTML index page...")

    try:
        output_path = generate_index_html(
            config,
            output_path=args.output,
            base_url=args.base_url
        )
        print(f"✓ HTML index page generated successfully")
        print(f"  Saved to: {output_path}")
    except Exception as e:
        print(f"✗ Error generating index: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AvyRSS offline operations management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full update - download all forecasts and generate all feeds
  %(prog)s full-update

  # Download forecast for a specific zone
  %(prog)s download-forecast northwest-avalanche-center snoqualmie-pass

  # Generate RSS feed for a specific zone (without downloading new forecast)
  %(prog)s generate-feed northwest-avalanche-center snoqualmie-pass

  # Generate the HTML index page
  %(prog)s generate-index
        """
    )

    # Global arguments
    parser.add_argument(
        '--config',
        default='avalanche_centers.yaml',
        help='Path to avalanche centers config file (default: avalanche_centers.yaml)'
    )
    parser.add_argument(
        '--forecasts-dir',
        default='forecasts',
        help='Directory for storing forecasts (default: forecasts)'
    )
    parser.add_argument(
        '--feeds-dir',
        default='feeds',
        help='Directory for storing RSS feeds (default: feeds)'
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL for RSS feeds (default: http://localhost:5000)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # full-update command
    parser_full = subparsers.add_parser(
        'full-update',
        help='Download forecasts and generate feeds for all zones'
    )
    parser_full.set_defaults(func=cmd_full_update)

    # download-forecast command
    parser_download = subparsers.add_parser(
        'download-forecast',
        help='Download forecast for a specific zone'
    )
    parser_download.add_argument('center', help='Avalanche center slug')
    parser_download.add_argument('zone', help='Zone slug')
    parser_download.set_defaults(func=cmd_download_forecast)

    # generate-feed command
    parser_gen_feed = subparsers.add_parser(
        'generate-feed',
        help='Generate RSS feed for a specific zone'
    )
    parser_gen_feed.add_argument('center', help='Avalanche center slug')
    parser_gen_feed.add_argument('zone', help='Zone slug')
    parser_gen_feed.set_defaults(func=cmd_generate_feed)

    # generate-index command
    parser_index = subparsers.add_parser(
        'generate-index',
        help='Generate the HTML index page'
    )
    parser_index.add_argument(
        '--output',
        default='index.html',
        help='Output path for the HTML file (default: index.html)'
    )
    parser_index.set_defaults(func=cmd_generate_index)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
