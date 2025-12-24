"""
Flask application for serving RSS feeds.
"""

import os
from pathlib import Path
from flask import Flask, send_file, abort, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get project root directory (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Configuration - resolve paths relative to project root
FEEDS_DIR = PROJECT_ROOT / os.getenv('FEEDS_DIR', 'feeds')
INDEX_HTML_PATH = PROJECT_ROOT / os.getenv('INDEX_HTML_PATH', 'index.html')


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
