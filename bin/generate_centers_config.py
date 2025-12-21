#!/usr/bin/env python3
"""
Generate the avalanche centers configuration YAML file.
This should be run once to create the initial configuration.
"""

import requests
import yaml
import re
from typing import Dict, List

API_BASE = "https://api.avalanche.org/v2/public"

# Supported centers from avymail - filtering out tier 2 centers that don't forecast daily
SUPPORTED_CENTERS = {
    "Northwest Avalanche Center",
    "Central Oregon Avalanche Center",
    "Sawtooth Avalanche Center",
    "Bridger-Teton Avalanche Center",
    "Mount Washington Avalanche Center",
    "Sierra Avalanche Center",
    "Flathead Avalanche Center",
    "Idaho Panhandle Avalanche Center",
    "Payette Avalanche Center",
    "Colorado Avalanche Information Center",
    "Utah Avalanche Center",
    "Gallatin National Forest Avalanche Center",
    "Valdez Avalanche Center",
    "Hatcher Pass Avalanche Center",
    "Chugach National Forest Avalanche Center",
}


def slugify(text: str) -> str:
    """Convert a name to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def fetch_centers_and_zones() -> Dict:
    """Fetch all avalanche centers and their zones from the API."""
    print("Fetching avalanche centers and zones from API...")

    url = f"{API_BASE}/products/map-layer"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()["features"]

    # Build zones list
    zones = [
        {
            "id": f["id"],
            "center": {
                "id": f["properties"]["center_id"],
                "name": f["properties"]["center"],
            },
            "zone_name": f["properties"]["name"],
        }
        for f in data
    ]

    # Get unique centers
    centers_set = set([(z["center"]["name"], z["center"]["id"]) for z in zones])

    # Build centers dictionary
    centers_dict = {}
    for center_name, center_id in sorted(centers_set):
        center_slug = slugify(center_name)
        centers_dict[center_slug] = {
            "name": center_name,
            "id": center_id,
            "zones": []
        }

    # Add zones to each center
    for z in zones:
        center_name = z["center"]["name"]
        center_slug = slugify(center_name)
        zone_slug = slugify(z["zone_name"])

        centers_dict[center_slug]["zones"].append({
            "name": z["zone_name"],
            "slug": zone_slug,
            "id": z["id"]
        })

    # Sort zones by name within each center
    for center in centers_dict.values():
        center["zones"].sort(key=lambda x: x["name"])

    return centers_dict


def main():
    """Main function to generate the centers configuration."""
    all_centers = fetch_centers_and_zones()

    # Filter to only supported centers
    print("\nFiltering to supported centers...")
    filtered_centers = {
        slug: data for slug, data in all_centers.items()
        if data["name"] in SUPPORTED_CENTERS
    }

    # Report on any centers in SUPPORTED_CENTERS that weren't found
    found_names = {data["name"] for data in filtered_centers.values()}
    missing = SUPPORTED_CENTERS - found_names
    if missing:
        print(f"\nWARNING: These centers were not found in the API response:")
        for name in sorted(missing):
            print(f"  - {name}")

    config = {
        "avalanche_centers": filtered_centers
    }

    output_file = "avalanche_centers.yaml"

    print(f"\nGenerating {output_file}...")
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\nSuccessfully created {output_file}")
    print(f"Total centers: {len(filtered_centers)}")
    print(f"Total zones: {sum(len(c['zones']) for c in filtered_centers.values())}")

    print("\nIncluded centers:")
    for slug, center in sorted(filtered_centers.items()):
        print(f"  - {center['name']} ({slug}): {len(center['zones'])} zones")


if __name__ == "__main__":
    main()
