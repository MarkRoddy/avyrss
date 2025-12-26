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
ASSETS_DIR = PROJECT_ROOT / 'assets'
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


@app.route('/assets/<path:filename>')
def serve_assets(filename: str):
    """Serve static assets (like danger icons)."""
    asset_path = ASSETS_DIR / filename

    if not asset_path.exists():
        abort(404, description=f"Asset not found: {filename}")

    return send_file(asset_path)


@app.route('/dev/preview-entry/<center_slug>/<zone_slug>')
@app.route('/dev/preview-entry/<center_slug>/<zone_slug>/<mode>')
def preview_entry(center_slug: str, zone_slug: str, mode: str = 'normal'):
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
        info = extract_forecast_info(forecast_data, zone_name=zone_name)

        # Import the helper functions
        from app.rss import danger_level_to_text, danger_level_to_color

        # Build the same description HTML that goes into the RSS feed
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
                    f'<img src="/assets/danger-icons/{overall_danger}.png" '
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
                f'<img src="/assets/danger-icons/{upper_current}.png" alt="{danger_level_to_text(upper_current)}" /> '
                f"Above Treeline: <strong>{danger_level_to_text(upper_current).upper()}</strong><br>"
                f'<img src="/assets/danger-icons/{middle_current}.png" alt="{danger_level_to_text(middle_current)}" /> '
                f"Treeline: <strong>{danger_level_to_text(middle_current).upper()}</strong><br>"
                f'<img src="/assets/danger-icons/{lower_current}.png" alt="{danger_level_to_text(lower_current)}" /> '
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
                f'<img src="/assets/danger-icons/{upper_tomorrow}.png" alt="{danger_level_to_text(upper_tomorrow)}" /> '
                f"Above Treeline: <strong>{danger_level_to_text(upper_tomorrow).upper()}</strong><br>"
                f'<img src="/assets/danger-icons/{middle_tomorrow}.png" alt="{danger_level_to_text(middle_tomorrow)}" /> '
                f"Treeline: <strong>{danger_level_to_text(middle_tomorrow).upper()}</strong><br>"
                f'<img src="/assets/danger-icons/{lower_tomorrow}.png" alt="{danger_level_to_text(lower_tomorrow)}" /> '
                f"Below Treeline: <strong>{danger_level_to_text(lower_tomorrow).upper()}</strong></p>"
            )

            description_parts.append("<hr>")

        # Add link to full forecast - simple text link
        if info['url']:
            description_parts.append(
                f"<p><a href='{info['url']}'>→ View Full Forecast on Avalanche Center Website</a></p>"
            )

        description_html = '\n'.join(description_parts)

        # Determine mode-specific styles
        if mode == 'rss':
            # RSS Reader simulation mode - match Feedly's exact behavior
            import re

            # Strip ALL inline style attributes (Feedly does this)
            description_html_stripped = re.sub(r'\s*style="[^"]*"', '', description_html)

            # Wrap images in span.PinableImageContainer (Feedly adds this)
            description_html_stripped = re.sub(
                r'<img\s+([^>]*?)>',
                r'<span class="PinableImageContainer"><img \1></span>',
                description_html_stripped
            )

            # Replace height attributes on img tags - Feedly ignores these
            description_html_stripped = re.sub(r'\s*height="[^"]*"', '', description_html_stripped)
            description_html_stripped = re.sub(r'\s*width="[^"]*"', '', description_html_stripped)

            description_html = description_html_stripped

            body_style = """
                font-family: system-ui, -apple-system, sans-serif;
                max-width: 600px;
                margin: 20px auto;
                padding: 0 20px;
                line-height: 1.6;
                font-size: 15px;
                background: #fff;
            """
            content_style = """
                padding: 10px;
                background: #fff;
            """
            # Match Feedly's actual rendering behavior
            extra_css = """
                /* Simulate Feedly's exact rendering */
                .content img {
                    max-width: 580px !important;
                    height: auto !important;
                    display: block !important;
                }
                .content table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .content td, .content th {
                    padding: 8px;
                    vertical-align: top;
                }
                .content strong {
                    font-weight: 600;
                }
            """
            mode_label = "RSS Reader Simulation Mode (Feedly-exact)"
            mode_note = "This exactly matches Feedly's behavior: strips all inline styles, removes height/width attributes on images, wraps images in PinableImageContainer spans. The bottom line icon becomes huge because it has no size constraint."
        else:
            extra_css = ""
            # Normal preview mode
            body_style = """
                font-family: system-ui, -apple-system, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                padding: 0 20px;
                line-height: 1.6;
            """
            content_style = "border: 1px solid #ddd; padding: 20px; background: #f9f9f9; border-radius: 4px;"
            mode_label = "Normal Preview Mode"
            mode_note = "This shows the RSS entry content with full browser rendering. Switch to RSS mode to see how feed readers render it."

        # Wrap in a simple HTML page for viewing
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RSS Entry Preview - {center_name} - {zone_name}</title>
            <style>
                body {{
                    {body_style}
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
                    {content_style}
                }}
                .note {{
                    margin-top: 30px;
                    padding: 15px;
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    font-size: 0.9em;
                }}
                .mode-toggle {{
                    margin-bottom: 20px;
                    padding: 10px;
                    background: #e3f2fd;
                    border-radius: 4px;
                    text-align: center;
                }}
                .mode-toggle a {{
                    margin: 0 10px;
                    text-decoration: none;
                    font-weight: bold;
                    color: #1976d2;
                }}
                {extra_css}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RSS Entry Preview</h1>
                <h2>{center_name} - {zone_name}</h2>
            </div>

            <div class="mode-toggle">
                <strong>{mode_label}</strong><br>
                <a href="/dev/preview-entry/{center_slug}/{zone_slug}/normal">Normal Mode</a> |
                <a href="/dev/preview-entry/{center_slug}/{zone_slug}/rss">RSS Reader Mode</a>
            </div>

            <div class="metadata">
                <strong>Entry Title:</strong> {info['title']}<br>
                <strong>Entry Link (title link):</strong> {f"<a href='{info['url']}'>{info['url']}</a>" if info['url'] else "No link available"}<br>
                <strong>Published:</strong> {info['date'].strftime('%Y-%m-%d %H:%M UTC')}
            </div>

            <div class="content">
                <h3 style="margin-top: 0;">RSS Entry Content:</h3>
                {description_html}
            </div>

            <div class="note">
                <strong>Note:</strong> {mode_note}
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
