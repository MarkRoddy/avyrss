# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AvyRSS generates and serves RSS feeds for avalanche forecasts from various avalanche centers across North America. The project uses an **offline generation model**: forecasts are downloaded and stored as JSON files, RSS feeds are pre-generated from stored forecasts, and served as static files.

- 57 zones across 14 avalanche centers
- Data source: avalanche.org API (https://api.avalanche.org/v2/public)
- Python 3.12+ with Flask for development server only

## Key Commands

### Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables (optional)
cp .env.example .env
```

### Core Operations (use bin/manage.py)

```bash
# Full update - download ALL forecasts and generate ALL feeds
python3 bin/manage.py full-update

# Download forecast for a single zone
python3 bin/manage.py download-forecast <center-slug> <zone-slug>
# Example:
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass

# Generate RSS feed for a single zone (without downloading new forecast)
python3 bin/manage.py generate-feed <center-slug> <zone-slug>

# Generate all RSS feeds (without downloading new forecasts)
python3 bin/manage.py generate-all-feeds

# Generate the HTML index page
python3 bin/manage.py generate-index
```

### Development Server (optional, for local testing only)

```bash
# Run Flask development server
python3 app/main.py
# Available at http://localhost:5000

# Preview RSS entry content (development endpoint)
# http://localhost:5000/dev/preview-entry/<center-slug>/<zone-slug>
# http://localhost:5000/dev/preview-entry/<center-slug>/<zone-slug>/rss  # Simulates RSS reader
```

**Important**: The Flask server is ONLY for development. In production, serve the static files (`index.html` and `feeds/`) directly.

## Architecture

### Data Flow

1. **Forecast Download** (`app/forecasts.py`): Fetches forecasts from avalanche.org API
2. **Storage**: Forecasts saved to `forecasts/{center-slug}/{zone-slug}/{year}/{YYYY-MM-DD}.json`
   - Filename uses the forecast's `published_time` (falls back to `request_time` if not available)
3. **Feed Generation** (`app/rss.py`): Reads stored forecasts and generates RSS XML files
4. **Feed Storage**: RSS feeds saved to `feeds/{center-slug}/{zone-slug}.xml`
5. **Serving**: Static files served directly (or via Flask dev server)

### Key Components

**app/avalanche.py**
- `AvalancheConfig`: Loads and manages configuration from `avalanche_centers.yaml`
- `fetch_forecast()`: Fetches forecast data from avalanche.org API
- Maps human-readable slugs to API IDs

**app/forecasts.py**
- `download_forecast_for_zone()`: Download and save forecast for single zone
- `download_all_forecasts()`: Download forecasts for all zones
- `get_recent_forecasts()`: Retrieve N most recent forecasts for a zone
- `save_forecast()`: Saves forecast using published_time for filename (or request_time as fallback)
- Organizes forecasts by year for easy archival

**app/rss.py**
- `generate_rss_feed()`: Creates RSS XML from stored forecasts
- `generate_feed_for_zone()`: Generate and save feed for single zone
- `generate_all_feeds()`: Generate feeds for all zones
- `extract_forecast_info()`: Extracts bottom line, danger ratings, avalanche problems from forecast data
- Includes danger icons, bottom line, danger ratings (today/tomorrow), avalanche problems, and forecast discussion

**app/html_generator.py**
- Generates the index.html page listing all available feeds

**app/main.py**
- Flask application (development only)
- Routes: `/`, `/feed/<center>/<zone>`, `/assets/<path>`, `/dev/preview-entry/<center>/<zone>`
- `/dev/preview-entry` endpoint supports `/normal` and `/rss` modes for testing RSS reader rendering

**bin/manage.py**
- CLI for all offline operations
- Main entry point for forecast downloads and feed generation

### Configuration

**avalanche_centers.yaml**
- Defines all avalanche centers and their zones
- Structure: `avalanche_centers -> {center-slug} -> zones -> [{name, slug, id}]`
- Maps human-readable slugs to avalanche.org zone IDs

### Directory Structure

```
forecasts/           # Downloaded forecast JSON files (not in git)
  {center-slug}/
    {zone-slug}/
      {year}/
        YYYY-MM-DD.json

feeds/               # Generated RSS XML files (not in git)
  {center-slug}/
    {zone-slug}.xml

assets/              # Static assets (danger icons, etc.)
  danger-icons/      # Resized danger level icons (40x40 PNG)

app/                 # Application code
  avalanche.py       # Config & API fetching
  forecasts.py       # Forecast download & storage
  rss.py            # RSS feed generation
  html_generator.py  # Index page generation
  main.py           # Flask dev server
  templates/        # Jinja2 templates
    index.html.j2

bin/                 # Utility scripts
  manage.py         # Main CLI tool
  update-feeds.sh   # Automated update script (for production cron)
  generate_centers_config.py  # One-time config generation
```

## Development Workflow

### Making Changes to RSS Feed Format

1. Modify `app/rss.py` (specifically `extract_forecast_info()` or `generate_rss_feed()`)
2. Regenerate feeds: `python3 bin/manage.py generate-all-feeds`
3. Preview changes: `python3 app/main.py` then visit `http://localhost:5000/dev/preview-entry/<center>/<zone>/rss`

### Adding a New Avalanche Center or Zone

1. Update `avalanche_centers.yaml` with new center/zone configuration
2. Get zone ID from avalanche.org API
3. Test with single download: `python3 bin/manage.py download-forecast <center-slug> <zone-slug>`
4. Regenerate index page: `python3 bin/manage.py generate-index`

### Testing RSS Feed Rendering

Use the `/dev/preview-entry` endpoint with `/rss` mode to simulate how RSS readers (like Feedly) will render the content. This mode strips inline styles and resizes images to match RSS reader behavior.

## Production Deployment

The application is designed to be deployed as static files with a cron job:

1. Set up cron job to run `bin/update-feeds.sh` daily (e.g., 6 AM)
2. Serve `index.html` and `feeds/` directory using any static file server (nginx, Apache, GitHub Pages, etc.)
3. No Flask server needed in production

Example cron entry:
```bash
0 6 * * * /path/to/avyrss/bin/update-feeds.sh /var/www >> /var/log/avyrss-update.log 2>&1
```

## Important Notes

- RSS feed generation reads from stored forecasts (offline mode)
- The Flask server is strictly for development - never deploy it to production
- All slug-to-ID mapping happens through `avalanche_centers.yaml`
- Danger icons are resized to 40x40 PNG for better RSS reader compatibility
- Tomorrow's forecast is intentionally placed at the bottom of RSS entries for better readability
- Forecast files are named using the forecast's `published_time` (or `request_time` if unavailable)
