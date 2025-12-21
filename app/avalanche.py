"""
Avalanche forecast fetching and zone management.
"""

import os
import yaml
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime
import time


API_BASE = "https://api.avalanche.org/v2/public"


class AvalancheConfig:
    """Manages avalanche center and zone configuration."""

    def __init__(self, config_path: str = "avalanche_centers.yaml"):
        """Load configuration from YAML file."""
        self.config_path = config_path
        self.centers = self._load_config()

    def _load_config(self) -> Dict:
        """Load the avalanche centers configuration from YAML."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)

        return data.get('avalanche_centers', {})

    def get_zone_id(self, center_slug: str, zone_slug: str) -> Optional[str]:
        """
        Translate human-readable center and zone slugs to avalanche.org zone ID.

        Args:
            center_slug: URL-friendly slug for the avalanche center
            zone_slug: URL-friendly slug for the zone

        Returns:
            Zone ID string, or None if not found
        """
        if center_slug not in self.centers:
            return None

        center = self.centers[center_slug]
        for zone in center['zones']:
            if zone['slug'] == zone_slug:
                return zone['id']

        return None

    def get_center_id(self, center_slug: str) -> Optional[str]:
        """
        Get the center ID for a given center slug.

        Args:
            center_slug: URL-friendly slug for the avalanche center

        Returns:
            Center ID string, or None if not found
        """
        if center_slug not in self.centers:
            return None

        return self.centers[center_slug]['id']

    def get_all_zones(self) -> list:
        """
        Get all center/zone combinations.

        Returns:
            List of tuples: (center_slug, zone_slug, zone_id, center_id)
        """
        zones = []
        for center_slug, center_data in self.centers.items():
            center_id = center_data['id']
            for zone in center_data['zones']:
                zones.append((
                    center_slug,
                    zone['slug'],
                    zone['id'],
                    center_id
                ))
        return zones


def fetch_forecast(center_id: str, zone_id: str) -> Dict:
    """
    Fetch today's forecast for a specified zone.

    Args:
        center_id: The avalanche center ID
        zone_id: The zone ID

    Returns:
        Dictionary containing:
            - request_time: ISO format timestamp when request was initiated (UTC)
            - request_duration_ms: How long the request took in milliseconds
            - forecast: The forecast data from the API
    """
    request_start = datetime.utcnow()
    start_time = time.time()

    url = f"{API_BASE}/product?type=forecast&center_id={center_id}&zone_id={zone_id}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        forecast_data = response.json()

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "request_time": request_start.isoformat() + "Z",
            "request_duration_ms": duration_ms,
            "forecast": forecast_data
        }

    except requests.RequestException as e:
        # Return error information in the same structure
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "request_time": request_start.isoformat() + "Z",
            "request_duration_ms": duration_ms,
            "error": str(e),
            "forecast": None
        }
