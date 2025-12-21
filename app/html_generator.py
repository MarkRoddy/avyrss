"""
HTML index page generation.
"""

import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

from app.avalanche import AvalancheConfig

logger = logging.getLogger(__name__)


def generate_index_html(
    config: AvalancheConfig,
    output_path: str = "index.html",
    base_url: str = "http://localhost:5000",
    template_dir: str = "app/templates"
) -> Path:
    """
    Generate the static HTML index page.

    Args:
        config: AvalancheConfig instance
        output_path: Where to save the generated HTML
        base_url: Base URL for the application
        template_dir: Directory containing Jinja2 templates

    Returns:
        Path where the HTML was saved
    """
    logger.info("Generating index.html...")

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index.html.j2')

    # Calculate statistics
    total_centers = len(config.centers)
    total_zones = sum(len(center['zones']) for center in config.centers.values())

    # Render template
    html_content = template.render(
        centers=config.centers,
        total_centers=total_centers,
        total_zones=total_zones,
        base_url=base_url,
        generation_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    )

    # Save to file
    output_file = Path(output_path)
    with open(output_file, 'w') as f:
        f.write(html_content)

    logger.info(f"Index page saved to {output_file}")
    return output_file
