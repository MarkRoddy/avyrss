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
        overall_danger = max(
            danger_current.get('upper', 0),
            danger_current.get('middle', 0),
            danger_current.get('lower', 0)
        )

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

            # Add bottom line FIRST with danger icon (neutral background)
            if info['bottom_line']:
                overall_danger = info.get('overall_danger')
                danger_icon = ""
                if overall_danger:
                    danger_icon = (
                        f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{overall_danger}.png' "
                        f"alt='{danger_level_to_text(overall_danger)}' height='30' style='vertical-align: middle; margin-right: 10px;' />"
                    )

                description_parts.append(
                    "<div style='margin: 20px 0; padding: 15px; background-color: #f5f5f5; border: 2px solid #999; border-radius: 4px;'>"
                    "<p style='font-size: 18px; font-weight: bold; margin: 0 0 10px 0; text-transform: uppercase;'>"
                    f"{danger_icon}The Bottom Line"
                    "</p>"
                    f"<div style='line-height: 1.6;'>{info['bottom_line']}</div>"
                    "</div>"
                )

            # Add danger ratings with color-coded backgrounds (current + tomorrow)
            if info['danger_current']:
                description_parts.append(
                    "<div style='margin: 20px 0;'>"
                    "<p style='font-size: 18px; font-weight: bold; margin: 0 0 15px 0; text-transform: uppercase;'>"
                    "Avalanche Danger"
                    "</p>"
                )

                # Build table with current and tomorrow columns
                # Today column is ~60% width, tomorrow is ~25% width
                description_parts.append("<table style='border-collapse: separate; border-spacing: 0; width: 100%; max-width: 700px; margin-bottom: 20px;'>")

                # Header row
                description_parts.append(
                    "<tr>"
                    "<th style='padding: 8px; border: 1px solid #ddd; background-color: #e0e0e0; text-align: left; width: 15%;'></th>"
                    "<th style='padding: 8px; border: 1px solid #ddd; background-color: #e0e0e0; text-align: left; width: 60%;'>Today</th>"
                )
                if info['danger_tomorrow']:
                    description_parts.append(
                        "<th style='padding: 8px; border: 1px solid #ddd; background-color: #e0e0e0; text-align: left; width: 25%;'>Tomorrow</th>"
                    )
                description_parts.append("</tr>")

                # Above Treeline
                upper_current = info['danger_current'].get('upper')
                upper_color = danger_level_to_color(upper_current)
                description_parts.append(
                    f"<tr>"
                    f"<td style='padding: 12px; background-color: {upper_color}; font-weight: bold; border: 1px solid #ddd;'>Above Treeline</td>"
                    f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                    f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{upper_current}.png' "
                    f"alt='{danger_level_to_text(upper_current)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                    f"<strong style='font-size: 16px;'>{danger_level_to_text(upper_current)}</strong>"
                    f"</td>"
                )
                if info['danger_tomorrow']:
                    upper_tomorrow = info['danger_tomorrow'].get('upper')
                    description_parts.append(
                        f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                        f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{upper_tomorrow}.png' "
                        f"alt='{danger_level_to_text(upper_tomorrow)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                        f"<strong style='font-size: 16px;'>{danger_level_to_text(upper_tomorrow)}</strong>"
                        f"</td>"
                    )
                description_parts.append("</tr>")

                # Treeline
                middle_current = info['danger_current'].get('middle')
                middle_color = danger_level_to_color(middle_current)
                description_parts.append(
                    f"<tr>"
                    f"<td style='padding: 12px; background-color: {middle_color}; font-weight: bold; border: 1px solid #ddd;'>Treeline</td>"
                    f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                    f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{middle_current}.png' "
                    f"alt='{danger_level_to_text(middle_current)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                    f"<strong style='font-size: 16px;'>{danger_level_to_text(middle_current)}</strong>"
                    f"</td>"
                )
                if info['danger_tomorrow']:
                    middle_tomorrow = info['danger_tomorrow'].get('middle')
                    description_parts.append(
                        f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                        f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{middle_tomorrow}.png' "
                        f"alt='{danger_level_to_text(middle_tomorrow)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                        f"<strong style='font-size: 16px;'>{danger_level_to_text(middle_tomorrow)}</strong>"
                        f"</td>"
                    )
                description_parts.append("</tr>")

                # Below Treeline
                lower_current = info['danger_current'].get('lower')
                lower_color = danger_level_to_color(lower_current)
                description_parts.append(
                    f"<tr>"
                    f"<td style='padding: 12px; background-color: {lower_color}; font-weight: bold; border: 1px solid #ddd;'>Below Treeline</td>"
                    f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                    f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{lower_current}.png' "
                    f"alt='{danger_level_to_text(lower_current)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                    f"<strong style='font-size: 16px;'>{danger_level_to_text(lower_current)}</strong>"
                    f"</td>"
                )
                if info['danger_tomorrow']:
                    lower_tomorrow = info['danger_tomorrow'].get('lower')
                    description_parts.append(
                        f"<td style='padding: 12px; border: 1px solid #ddd; background-color: #f5f5f5;'>"
                        f"<img src='https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons/{lower_tomorrow}.png' "
                        f"alt='{danger_level_to_text(lower_tomorrow)}' height='25' style='vertical-align: middle; margin-right: 8px;' />"
                        f"<strong style='font-size: 16px;'>{danger_level_to_text(lower_tomorrow)}</strong>"
                        f"</td>"
                    )
                description_parts.append("</tr>")

                description_parts.append("</table>")
                description_parts.append("</div>")

            # Add avalanche problems
            if info['problems']:
                description_parts.append(
                    "<div style='margin: 20px 0;'>"
                    "<p style='font-size: 18px; font-weight: bold; margin: 0 0 15px 0; text-transform: uppercase;'>"
                    f"Avalanche Problems ({len(info['problems'])})"
                    "</p>"
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
                        f"<div style='margin: 15px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #333;'>"
                        f"<p style='margin: 0 0 8px 0; font-weight: bold; font-size: 16px; text-transform: uppercase;'>"
                        f"Problem #{idx}: {problem['name']}"
                        f"</p>"
                        f"<p style='margin: 0; font-style: italic; color: #555;'>"
                        f"Likelihood: <strong>{problem['likelihood'].capitalize()}</strong> | "
                        f"Size: <strong>{size_text}</strong>"
                        f"</p>"
                        f"</div>"
                    )
                description_parts.append("</div>")

            # Add link to full forecast
            if info['url']:
                description_parts.append(
                    f"<p style='margin-top: 25px; padding: 12px; background-color: #e3f2fd; border-radius: 4px; text-align: center;'>"
                    f"<a href='{info['url']}' style='color: #1976d2; text-decoration: none; font-weight: bold; font-size: 16px;'>"
                    f"→ View Full Forecast on Avalanche Center Website"
                    f"</a>"
                    f"</p>"
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
