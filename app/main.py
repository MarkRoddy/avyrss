"""
Flask application for serving RSS feeds.
"""

import os
from pathlib import Path
from flask import Flask, send_file, abort, Response
from dotenv import load_dotenv

from app.avalanche import AvalancheConfig
from app.forecasts import get_recent_forecasts
from app.rss import extract_forecast_info

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get project root directory (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Configuration - resolve paths relative to project root
FEEDS_DIR = PROJECT_ROOT / os.getenv('FEEDS_DIR', 'feeds')
INDEX_HTML_PATH = PROJECT_ROOT / os.getenv('INDEX_HTML_PATH', 'index.html')
FORECASTS_DIR = PROJECT_ROOT / os.getenv('FORECASTS_DIR', 'forecasts')
CONFIG_PATH = PROJECT_ROOT / 'avalanche_centers.yaml'


@app.route('/feed/<center_slug>/<zone_slug>')
def serve_feed(center_slug: str, zone_slug: str):
    """
    Serve a pre-generated RSS feed for a specific zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug

    Returns:
        RSS feed XML file
    """
    # Construct path to feed file
    feed_path = FEEDS_DIR / center_slug / f"{zone_slug}.xml"

    # Check if feed exists
    if not feed_path.exists():
        abort(404, description=f"Feed not found for {center_slug}/{zone_slug}")

    # Serve the feed with correct content type
    return send_file(
        feed_path,
        mimetype='application/rss+xml',
        as_attachment=False
    )


@app.route('/')
def index():
    """Serve the generated index page."""
    index_path = INDEX_HTML_PATH

    if not index_path.exists():
        return Response(
            "<html><body><h1>AvyRSS</h1><p>Avalanche Forecast RSS Feeds</p>"
            "<p>Index page not yet generated. Run <code>bin/manage.py generate-index</code> to create it.</p>"
            "</body></html>",
            mimetype='text/html'
        )

    return send_file(index_path, mimetype='text/html')


@app.route('/dev/preview-entry/<center_slug>/<zone_slug>')
def preview_entry(center_slug: str, zone_slug: str):
    """
    Development endpoint to preview the HTML content of an RSS feed entry.
    Shows the latest forecast entry for the specified zone.

    Args:
        center_slug: Avalanche center slug
        zone_slug: Zone slug

    Returns:
        HTML page showing the RSS entry content
    """
    try:
        # Load config
        config = AvalancheConfig(str(CONFIG_PATH))

        # Get center and zone names
        if center_slug not in config.centers:
            abort(404, description=f"Center not found: {center_slug}")

        center_data = config.centers[center_slug]
        center_name = center_data['name']

        zone_name = None
        for zone in center_data['zones']:
            if zone['slug'] == zone_slug:
                zone_name = zone['name']
                break

        if not zone_name:
            abort(404, description=f"Zone not found: {zone_slug}")

        # Get the most recent forecast
        recent_forecasts = get_recent_forecasts(
            center_slug, zone_slug, limit=1, base_dir=str(FORECASTS_DIR)
        )

        if not recent_forecasts:
            return Response(
                f"<html><body><h1>No Forecasts Available</h1>"
                f"<p>No forecast data found for {center_name} - {zone_name}</p>"
                f"<p>Run <code>python3 bin/manage.py download-forecast {center_slug} {zone_slug}</code> to download forecasts.</p>"
                "</body></html>",
                mimetype='text/html'
            )

        # Extract forecast info
        file_path, forecast_data = recent_forecasts[0]
        info = extract_forecast_info(forecast_data)

        # Build the same description HTML that goes into the RSS feed
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

        # Wrap in a simple HTML page for viewing
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>RSS Entry Preview - {center_name} - {zone_name}</title>
            <style>
                body {{
                    font-family: system-ui, -apple-system, sans-serif;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 0 20px;
                    line-height: 1.6;
                }}
                .header {{
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .metadata {{
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }}
                .content {{
                    border: 1px solid #ddd;
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 4px;
                }}
                .note {{
                    margin-top: 30px;
                    padding: 15px;
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RSS Entry Preview</h1>
                <h2>{center_name} - {zone_name}</h2>
            </div>

            <div class="metadata">
                <strong>Entry Title:</strong> {info['title']}<br>
                <strong>Entry Link (title link):</strong> {f"<a href='{info['url']}'>{info['url']}</a>" if info['url'] else "No link available"}<br>
                <strong>Published:</strong> {info['date'].strftime('%Y-%m-%d %H:%M UTC')}
            </div>

            <div class="content">
                <h3>RSS Entry Content (HTML):</h3>
                {description_html}
            </div>

            <div class="note">
                <strong>Note:</strong> This is a development endpoint showing what appears in the RSS feed entry.
                This content is extracted from the latest downloaded forecast for this zone.
            </div>
        </body>
        </html>
        """

        return Response(html, mimetype='text/html')

    except Exception as e:
        abort(500, description=f"Error previewing entry: {str(e)}")


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok'}


if __name__ == '__main__':
    # Development server with hot reload
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    port = int(os.getenv('FLASK_PORT', '5000'))

    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )
