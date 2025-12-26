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


def danger_level_to_text(level: int) -> str:
    """
    Convert numeric danger level to text.

    Args:
        level: Danger level (1-5)

    Returns:
        Text name of danger level
    """
    mapping = {
        1: 'Low',
        2: 'Moderate',
        3: 'Considerable',
        4: 'High',
        5: 'Extreme'
    }
    return mapping.get(level, 'Unknown')


def danger_level_to_color(level: int) -> str:
    """
    Convert numeric danger level to NWAC color scheme.

    Args:
        level: Danger level (1-5)

    Returns:
        Hex color code
    """
    mapping = {
        1: '#4CAF50',  # Green - Low
        2: '#FFEB3B',  # Yellow - Moderate
        3: '#FF9800',  # Orange - Considerable
        4: '#F44336',  # Red - High
        5: '#000000'   # Black - Extreme
    }
    return mapping.get(level, '#999999')


def extract_forecast_info(forecast_data: Dict, zone_name: str = None) -> Dict:
    """
    Extract relevant information from a forecast data structure.

    Args:
        forecast_data: The full forecast data dict (with request_time, forecast, etc)
        zone_name: Optional zone name to include in the title

    Returns:
        Dictionary with extracted info: title, date, bottom_line, url, author, danger_current, danger_tomorrow, problems, overall_danger
    """
    forecast = forecast_data.get('forecast', {})

    # Handle empty or error forecasts
    if not forecast:
        return {
            'title': 'No forecast available',
            'date': datetime.fromisoformat(forecast_data['request_time'].rstrip('Z')),
            'bottom_line': 'Forecast data not available.',
            'url': None,
            'author': None,
            'danger_current': None,
            'danger_tomorrow': None,
            'problems': [],
            'overall_danger': None
        }

    # Extract published date
    published_time = forecast.get('published_time')
    if published_time:
        date = datetime.fromisoformat(published_time.rstrip('Z'))
    else:
        date = datetime.fromisoformat(forecast_data['request_time'].rstrip('Z'))

    # Extract bottom line
    bottom_line = forecast.get('bottom_line', 'No bottom line available.')

    # Extract forecast discussion
    forecast_discussion = forecast.get('hazard_discussion', '')

    # Extract forecast URL from forecast_zone
    forecast_url = None
    forecast_zones = forecast.get('forecast_zone', [])
    if forecast_zones and len(forecast_zones) > 0:
        forecast_url = forecast_zones[0].get('url')

    # Extract author
    author = forecast.get('author')

    # Extract danger ratings for current and tomorrow
    danger_current = None
    danger_tomorrow = None
    danger_list = forecast.get('danger', [])
    for danger_entry in danger_list:
        if danger_entry.get('valid_day') == 'current':
            danger_current = danger_entry
        elif danger_entry.get('valid_day') == 'tomorrow':
            danger_tomorrow = danger_entry

    # Calculate overall danger (highest of the three elevation bands for current day)
    overall_danger = None
    if danger_current:
        # Filter out None values before calculating max
        levels = [
            danger_current.get('upper'),
            danger_current.get('middle'),
            danger_current.get('lower')
        ]
        levels = [l for l in levels if l is not None]
        if levels:
            overall_danger = max(levels)

    # Extract avalanche problems
    problems = []
    for problem in forecast.get('forecast_avalanche_problems', []):
        problems.append({
            'name': problem.get('name', 'Unknown'),
            'likelihood': problem.get('likelihood', 'Unknown'),
            'size': problem.get('size', [])
        })

    # Create title
    date_str = date.strftime('%Y-%m-%d')

    # Build title with zone name if provided
    if zone_name:
        title = f"{zone_name} Avalanche Forecast for {date_str}"
    else:
        title = f"Avalanche Forecast for {date_str}"

    return {
        'title': title,
        'date': date,
        'bottom_line': bottom_line,
        'forecast_discussion': forecast_discussion,
        'url': forecast_url,
        'author': author,
        'danger_current': danger_current,
        'danger_tomorrow': danger_tomorrow,
        'problems': problems,
        'overall_danger': overall_danger
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

            # Add author
            if info['author']:
                description_parts.append(
                    f"<p style='margin: 0 0 20px 0; color: #666; font-size: 14px;'>"
                    f"<strong>Forecaster:</strong> {info['author']}"
                    f"</p>"
                )

            # Add bottom line with small danger icon
            if info['bottom_line']:
                overall_danger = info.get('overall_danger')
                danger_icon = ""
                if overall_danger:
                    # Use our locally hosted, small (40x40) danger icons
                    danger_icon = (
                        f'<img src="{base_url}/assets/danger-icons/{overall_danger}.png" '
                        f'alt="{danger_level_to_text(overall_danger)}" /> '
                    )

                description_parts.append(
                    f"<p><strong>{danger_icon}THE BOTTOM LINE</strong></p>"
                    f"<p>{info['bottom_line']}</p>"
                    "<hr>"
                )

            # Add danger ratings with small icons - ONLY TODAY (tomorrow moved to bottom)
            if info['danger_current']:
                description_parts.append("<p><strong>AVALANCHE DANGER - TODAY</strong></p>")

                # Today's danger
                upper_current = info['danger_current'].get('upper')
                middle_current = info['danger_current'].get('middle')
                lower_current = info['danger_current'].get('lower')

                description_parts.append(
                    "<p>"
                    f'<img src="{base_url}/assets/danger-icons/{upper_current}.png" alt="{danger_level_to_text(upper_current)}" /> '
                    f"Above Treeline: <strong>{danger_level_to_text(upper_current).upper()}</strong><br>"
                    f'<img src="{base_url}/assets/danger-icons/{middle_current}.png" alt="{danger_level_to_text(middle_current)}" /> '
                    f"Treeline: <strong>{danger_level_to_text(middle_current).upper()}</strong><br>"
                    f'<img src="{base_url}/assets/danger-icons/{lower_current}.png" alt="{danger_level_to_text(lower_current)}" /> '
                    f"Below Treeline: <strong>{danger_level_to_text(lower_current).upper()}</strong></p>"
                )

                description_parts.append("<hr>")

            # Add avalanche problems - simplified for RSS readers
            if info['problems']:
                description_parts.append(
                    f"<p><strong>AVALANCHE PROBLEMS ({len(info['problems'])})</strong></p>"
                )
                for idx, problem in enumerate(info['problems'], 1):
                    # Format size range properly (e.g., "D1-D2" instead of "D1, 2")
                    if problem['size'] and len(problem['size']) > 0:
                        if len(problem['size']) == 1:
                            size_text = f"D{problem['size'][0]}"
                        else:
                            size_text = f"D{problem['size'][0]}-D{problem['size'][-1]}"
                    else:
                        size_text = 'Unknown'

                    description_parts.append(
                        f"<p><strong>#{idx}: {problem['name'].upper()}</strong><br>"
                        f"Likelihood: {problem['likelihood'].capitalize()} | "
                        f"Size: {size_text}</p>"
                    )
                description_parts.append("<hr>")

            # Add forecast discussion - simplified
            if info.get('forecast_discussion'):
                description_parts.append(
                    "<p><strong>FORECAST DISCUSSION</strong></p>"
                    f"<p>{info['forecast_discussion']}</p>"
                    "<hr>"
                )

            # Add tomorrow's forecast at the bottom (less prominent)
            if info['danger_tomorrow']:
                description_parts.append("<p><strong>TOMORROW'S FORECAST</strong></p>")

                upper_tomorrow = info['danger_tomorrow'].get('upper')
                middle_tomorrow = info['danger_tomorrow'].get('middle')
                lower_tomorrow = info['danger_tomorrow'].get('lower')

                description_parts.append(
                    "<p>"
                    f'<img src="{base_url}/assets/danger-icons/{upper_tomorrow}.png" alt="{danger_level_to_text(upper_tomorrow)}" /> '
                    f"Above Treeline: <strong>{danger_level_to_text(upper_tomorrow).upper()}</strong><br>"
                    f'<img src="{base_url}/assets/danger-icons/{middle_tomorrow}.png" alt="{danger_level_to_text(middle_tomorrow)}" /> '
                    f"Treeline: <strong>{danger_level_to_text(middle_tomorrow).upper()}</strong><br>"
                    f'<img src="{base_url}/assets/danger-icons/{lower_tomorrow}.png" alt="{danger_level_to_text(lower_tomorrow)}" /> '
                    f"Below Treeline: <strong>{danger_level_to_text(lower_tomorrow).upper()}</strong></p>"
                )

                description_parts.append("<hr>")

            # Add link to full forecast - simple text link
            if info['url']:
                description_parts.append(
                    f"<p><a href='{info['url']}'>→ View Full Forecast on Avalanche Center Website</a></p>"
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
        Dictionary with counts: {'success': N, 'failed': M, 'total': T, 'failed_zones': [(center, zone), ...]}
    """
    all_zones = config.get_all_zones()
    results = {'success': 0, 'failed': 0, 'total': len(all_zones), 'failed_zones': []}

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
            results['failed_zones'].append((center_slug, zone_slug))

    logger.info(
        f"Feed generation complete: {results['success']} succeeded, "
        f"{results['failed']} failed out of {results['total']} total"
    )

    return results
