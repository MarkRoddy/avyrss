"""
RSS feed generation for avalanche forecasts.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

from feedgen.feed import FeedGenerator

from app.avalanche import AvalancheConfig
from app.forecasts import get_recent_forecasts

logger = logging.getLogger(__name__)


def extract_forecast_info(forecast_data: Dict, zone_name: str = None) -> Dict:
    """
    Extract relevant information from a forecast data structure.

    Args:
        forecast_data: The full forecast data dict (with request_time, forecast, etc)
        zone_name: Optional zone name to include in the title

    Returns:
        Dictionary with extracted info: title, date, bottom_line, url, danger_level
    """
    forecast = forecast_data.get('forecast', {})

    # Handle empty or error forecasts
    if not forecast:
        return {
            'title': 'No forecast available',
            'date': datetime.fromisoformat(forecast_data['request_time'].rstrip('Z')),
            'bottom_line': 'Forecast data not available.',
            'url': None,
            'danger_level': None
        }

    # Extract published date
    published_time = forecast.get('published_time')
    if published_time:
        date = datetime.fromisoformat(published_time.rstrip('Z'))
    else:
        date = datetime.fromisoformat(forecast_data['request_time'].rstrip('Z'))

    # Extract bottom line
    bottom_line = forecast.get('bottom_line', 'No bottom line available.')

    # Extract forecast URL from forecast_zone
    forecast_url = None
    forecast_zones = forecast.get('forecast_zone', [])
    if forecast_zones and len(forecast_zones) > 0:
        forecast_url = forecast_zones[0].get('url')

    # Extract danger level (if available)
    danger = forecast.get('danger', [])
    danger_level = None
    danger_level_text = None
    if danger and len(danger) > 0:
        # Get the most recent danger rating
        danger_level = danger[0].get('lower', 'Unknown')

        # Map numeric danger levels to text
        danger_map = {
            1: 'Low',
            2: 'Moderate',
            3: 'Considerable',
            4: 'High',
            5: 'Extreme'
        }

        if isinstance(danger_level, int):
            danger_level_text = danger_map.get(danger_level, str(danger_level))
        else:
            danger_level_text = str(danger_level)

    # Create title
    date_str = date.strftime('%Y-%m-%d')

    # Build title with zone name if provided
    if zone_name:
        title = f"{zone_name} Avalanche Forecast - {date_str}"
    else:
        title = f"Avalanche Forecast for {date_str}"

    if danger_level_text:
        title += f" - {danger_level_text}"

    return {
        'title': title,
        'date': date,
        'bottom_line': bottom_line,
        'url': forecast_url,
        'danger_level': danger_level
    }


def generate_rss_feed(
    center_slug: str,
    zone_slug: str,
    config: AvalancheConfig,
    base_url: str = "http://localhost:5000",
    forecasts_dir: str = "forecasts",
    limit: int = 10
) -> str:
    """
    Generate an RSS feed for a specified zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        config: AvalancheConfig instance
        base_url: Base URL for the RSS feed
        forecasts_dir: Directory containing forecasts
        limit: Number of recent forecasts to include

    Returns:
        RSS feed as XML string
    """
    # Get center and zone names
    if center_slug not in config.centers:
        raise ValueError(f"Center not found: {center_slug}")

    center_data = config.centers[center_slug]
    center_name = center_data['name']

    zone_name = None
    for zone in center_data['zones']:
        if zone['slug'] == zone_slug:
            zone_name = zone['name']
            break

    if not zone_name:
        raise ValueError(f"Zone not found: {zone_slug}")

    # Create feed generator
    fg = FeedGenerator()
    fg.id(f"{base_url}/feed/{center_slug}/{zone_slug}")
    fg.title(f"{center_name} - {zone_name} - Avalanche Forecast")
    fg.description(f"RSS feed for avalanche forecasts from {center_name}, {zone_name} zone")
    fg.link(href=f"{base_url}/feed/{center_slug}/{zone_slug}", rel='self')
    fg.language('en')

    # Get recent forecasts
    recent_forecasts = get_recent_forecasts(
        center_slug, zone_slug, limit=limit, base_dir=forecasts_dir
    )

    if not recent_forecasts:
        logger.warning(f"No forecasts found for {center_slug}/{zone_slug}")
        # Add a single entry indicating no forecasts
        fe = fg.add_entry()
        fe.id(f"{base_url}/feed/{center_slug}/{zone_slug}/no-data")
        fe.title("No Forecasts Available")
        fe.description("No forecast data has been downloaded yet for this zone.")
        fe.published(datetime.utcnow())
    else:
        # Add entries for each forecast
        for file_path, forecast_data in recent_forecasts:
            info = extract_forecast_info(forecast_data, zone_name=zone_name)

            fe = fg.add_entry()
            fe.id(f"{base_url}/feed/{center_slug}/{zone_slug}/{info['date'].strftime('%Y-%m-%d')}")
            fe.title(info['title'])
            fe.published(info['date'])

            # Build description HTML
            description_parts = []

            # Add bottom line
            if info['bottom_line']:
                description_parts.append(f"<p><strong>Bottom Line:</strong></p>")
                description_parts.append(f"<p>{info['bottom_line']}</p>")

            # Add link to full forecast
            if info['url']:
                description_parts.append(
                    f"<p><a href='{info['url']}'>View Full Forecast</a></p>"
                )

            description_html = '\n'.join(description_parts)
            fe.description(description_html)

            # Add link to the forecast page
            # This is the primary link that feed readers should use for the entry title
            # Only add a link if we have a valid forecast URL
            if info['url']:
                fe.link(href=info['url'])

    # Generate RSS
    return fg.rss_str(pretty=True).decode('utf-8')


def save_rss_feed(
    center_slug: str,
    zone_slug: str,
    rss_content: str,
    base_dir: str = "feeds"
) -> Path:
    """
    Save an RSS feed to disk.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        rss_content: RSS XML content
        base_dir: Base directory for feeds

    Returns:
        Path where the feed was saved
    """
    file_path = Path(base_dir) / center_slug / f"{zone_slug}.xml"

    # Create directory structure
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write feed to file
    with open(file_path, 'w') as f:
        f.write(rss_content)

    logger.info(f"Saved RSS feed to {file_path}")
    return file_path


def generate_feed_for_zone(
    center_slug: str,
    zone_slug: str,
    config: AvalancheConfig,
    base_url: str = "http://localhost:5000",
    forecasts_dir: str = "forecasts",
    feeds_dir: str = "feeds"
) -> Path:
    """
    Generate and save RSS feed for a single zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        config: AvalancheConfig instance
        base_url: Base URL for the RSS feed
        forecasts_dir: Directory containing forecasts
        feeds_dir: Directory to save feeds

    Returns:
        Path where the feed was saved
    """
    logger.info(f"Generating RSS feed for {center_slug}/{zone_slug}")

    rss_content = generate_rss_feed(
        center_slug, zone_slug, config,
        base_url=base_url,
        forecasts_dir=forecasts_dir
    )

    file_path = save_rss_feed(center_slug, zone_slug, rss_content, feeds_dir)

    return file_path


def generate_all_feeds(
    config: AvalancheConfig,
    base_url: str = "http://localhost:5000",
    forecasts_dir: str = "forecasts",
    feeds_dir: str = "feeds"
) -> Dict[str, int]:
    """
    Generate RSS feeds for all known zones.

    Args:
        config: AvalancheConfig instance
        base_url: Base URL for the RSS feeds
        forecasts_dir: Directory containing forecasts
        feeds_dir: Directory to save feeds

    Returns:
        Dictionary with counts: {'success': N, 'failed': M, 'total': T}
    """
    all_zones = config.get_all_zones()
    results = {'success': 0, 'failed': 0, 'total': len(all_zones)}

    logger.info(f"Generating RSS feeds for {results['total']} zones...")

    for center_slug, zone_slug, zone_id, center_id in all_zones:
        try:
            generate_feed_for_zone(
                center_slug, zone_slug, config,
                base_url=base_url,
                forecasts_dir=forecasts_dir,
                feeds_dir=feeds_dir
            )
            results['success'] += 1
        except Exception as e:
            logger.error(f"Error generating feed for {center_slug}/{zone_slug}: {e}")
            results['failed'] += 1

    logger.info(
        f"Feed generation complete: {results['success']} succeeded, "
        f"{results['failed']} failed out of {results['total']} total"
    )

    return results
