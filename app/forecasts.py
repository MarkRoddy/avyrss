"""
Forecast downloading and storage management.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from app.avalanche import AvalancheConfig, fetch_forecast

logger = logging.getLogger(__name__)


def get_forecast_path(
    center_slug: str,
    zone_slug: str,
    date: datetime,
    base_dir: str = "forecasts"
) -> Path:
    """
    Generate the file path for storing a forecast.

    Structure: forecasts/{center_slug}/{zone_slug}/{YYYY}/{YYYY-MM-DD}.json

    This structure makes it easy to:
    - List all forecasts for a zone
    - Find the N most recent forecasts (sorted by filename)
    - Organize by year for archival purposes

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        date: Date of the forecast
        base_dir: Base directory for forecasts

    Returns:
        Path object for the forecast file
    """
    year = date.strftime("%Y")
    date_str = date.strftime("%Y-%m-%d")

    path = Path(base_dir) / center_slug / zone_slug / year / f"{date_str}.json"
    return path


def save_forecast(
    center_slug: str,
    zone_slug: str,
    forecast_data: Dict,
    base_dir: str = "forecasts"
) -> Path:
    """
    Save a forecast to disk.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        forecast_data: Forecast data (including request_time, duration, forecast)
        base_dir: Base directory for forecasts

    Returns:
        Path where the forecast was saved
    """
    # Use the published time from the forecast, fall back to request time if not available
    forecast = forecast_data.get('forecast', {})
    published_time = forecast.get('published_time')

    if published_time:
        date = datetime.fromisoformat(published_time.rstrip('Z'))
    else:
        date = datetime.fromisoformat(forecast_data['request_time'].rstrip('Z'))

    file_path = get_forecast_path(center_slug, zone_slug, date, base_dir)

    # Create directory structure
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write forecast to file
    with open(file_path, 'w') as f:
        json.dump(forecast_data, f, indent=2)

    logger.info(f"Saved forecast to {file_path}")
    return file_path


def get_recent_forecasts(
    center_slug: str,
    zone_slug: str,
    limit: int = 10,
    base_dir: str = "forecasts"
) -> List[Tuple[Path, Dict]]:
    """
    Get the N most recent forecasts for a zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        limit: Maximum number of forecasts to return
        base_dir: Base directory for forecasts

    Returns:
        List of (file_path, forecast_data) tuples, newest first
    """
    zone_dir = Path(base_dir) / center_slug / zone_slug

    if not zone_dir.exists():
        logger.warning(f"No forecasts found for {center_slug}/{zone_slug}")
        return []

    # Find all JSON files recursively
    forecast_files = sorted(zone_dir.glob("**/*.json"), reverse=True)

    # Load and return the most recent ones
    results = []
    for file_path in forecast_files[:limit]:
        try:
            with open(file_path, 'r') as f:
                forecast_data = json.load(f)
            results.append((file_path, forecast_data))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading forecast from {file_path}: {e}")
            continue

    return results


def download_forecast_for_zone(
    center_slug: str,
    zone_slug: str,
    config: AvalancheConfig,
    base_dir: str = "forecasts"
) -> Tuple[bool, str, Optional[Path]]:
    """
    Download and save forecast for a single zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug
        config: AvalancheConfig instance
        base_dir: Base directory for forecasts

    Returns:
        Tuple of (success, message, file_path)
    """
    # Get zone and center IDs
    zone_id = config.get_zone_id(center_slug, zone_slug)
    center_id = config.get_center_id(center_slug)

    if not zone_id or not center_id:
        return False, f"Zone or center not found: {center_slug}/{zone_slug}", None

    logger.info(f"Fetching forecast for {center_slug}/{zone_slug} (zone_id={zone_id})")

    # Fetch forecast
    forecast_data = fetch_forecast(center_id, zone_id)

    if "error" in forecast_data:
        return False, f"Error fetching forecast: {forecast_data['error']}", None

    # Save to disk
    file_path = save_forecast(center_slug, zone_slug, forecast_data, base_dir)

    return True, f"Successfully downloaded forecast", file_path


def download_all_forecasts(
    config: AvalancheConfig,
    base_dir: str = "forecasts"
) -> Dict[str, int]:
    """
    Download forecasts for all known zones.

    Args:
        config: AvalancheConfig instance
        base_dir: Base directory for forecasts

    Returns:
        Dictionary with counts: {'success': N, 'failed': M, 'total': T}
    """
    all_zones = config.get_all_zones()
    results = {'success': 0, 'failed': 0, 'total': len(all_zones)}

    logger.info(f"Downloading forecasts for {results['total']} zones...")

    for center_slug, zone_slug, zone_id, center_id in all_zones:
        success, message, file_path = download_forecast_for_zone(
            center_slug, zone_slug, config, base_dir
        )

        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
            logger.error(f"{center_slug}/{zone_slug}: {message}")

    logger.info(
        f"Download complete: {results['success']} succeeded, "
        f"{results['failed']} failed out of {results['total']} total"
    )

    return results
