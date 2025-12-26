#!/usr/bin/env python3
"""
Download and resize NWAC danger icons for use in RSS feeds.
Creates small (40x40) versions that won't blow up in RSS readers.
"""

import urllib.request
import sys
from pathlib import Path
from PIL import Image
import io

# Icon URLs from NWAC CDN
ICON_BASE_URL = "https://nac-web-platforms.s3.us-west-1.amazonaws.com/assets/danger-icons"
ICON_SIZE = 40  # Resize to 40x40 pixels

# Danger levels to download
DANGER_LEVELS = [1, 2, 3, 4, 5]

# Output directory
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "danger-icons"


def download_and_resize_icon(level: int, output_dir: Path):
    """Download and resize a danger icon."""
    url = f"{ICON_BASE_URL}/{level}.png"
    output_path = output_dir / f"{level}.png"

    print(f"Downloading danger level {level} icon from {url}...")

    try:
        # Download the icon
        with urllib.request.urlopen(url) as response:
            image_data = response.read()

        # Open with PIL
        image = Image.open(io.BytesIO(image_data))
        print(f"  Original size: {image.size}")

        # Resize to specified dimensions using high-quality resampling
        resized = image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        print(f"  Resized to: {resized.size}")

        # Save as PNG
        resized.save(output_path, "PNG", optimize=True)
        print(f"  Saved to: {output_path}")

        return True

    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    print(f"Creating output directory: {ASSETS_DIR}")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading and resizing {len(DANGER_LEVELS)} danger icons...")
    print(f"Target size: {ICON_SIZE}x{ICON_SIZE} pixels\n")

    success_count = 0
    for level in DANGER_LEVELS:
        if download_and_resize_icon(level, ASSETS_DIR):
            success_count += 1
        print()

    print(f"Complete! Successfully processed {success_count}/{len(DANGER_LEVELS)} icons.")

    if success_count < len(DANGER_LEVELS):
        sys.exit(1)


if __name__ == "__main__":
    main()
