# AvyRss

RSS feeds for avalanche forecasts, making it easy to stay informed about backcountry conditions through your favorite feed reader.

## Overview

AvyRss generates and serves RSS feeds for avalanche forecasts from various avalanche centers across North America. The feeds are updated daily and include the latest forecast bottom-line summaries with links to full forecast details.

**Key Features:**
- RSS feeds for 57 zones across 14 avalanche centers
- Pre-generated feeds served as static files (fast and efficient)
- Clean, simple HTML interface to browse and subscribe to feeds
- Offline batch processing for forecast downloads and feed generation

## Supported Avalanche Centers

- Northwest Avalanche Center
- Central Oregon Avalanche Center
- Sawtooth Avalanche Center
- Bridger-Teton Avalanche Center
- Mount Washington Avalanche Center
- Sierra Avalanche Center
- Flathead Avalanche Center
- Idaho Panhandle Avalanche Center
- Payette Avalanche Center
- Colorado Avalanche Information Center
- Utah Avalanche Center
- Valdez Avalanche Center
- Hatcher Pass Avalanche Center
- Chugach National Forest Avalanche Center

## Prerequisites

- Python 3.12+ (currently using Python 3.12.3)
- pip and virtualenv

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd avyrss
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables (optional)

```bash
cp .env.example .env
# Edit .env if you need to customize settings
```

## Quick Start

### 1. Generate the HTML index page

```bash
python3 bin/manage.py generate-index
```

### 2. Download forecasts and generate RSS feeds

```bash
# Download a single forecast
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass

# Generate a single RSS feed
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass

# Or do a full update (download all forecasts and generate all feeds)
python3 bin/manage.py full-update
```

### 3. Start the development server

```bash
python3 app/main.py
```

The application will be available at `http://localhost:5000`

- Index page: `http://localhost:5000/`
- RSS feed example: `http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass`
- Health check: `http://localhost:5000/health`

## Project Structure

```
.
├── app/                        # Flask application code
│   ├── __init__.py
│   ├── main.py                # Flask app entry point
│   ├── avalanche.py           # Avalanche center/zone configuration
│   ├── forecasts.py           # Forecast downloading and storage
│   ├── rss.py                 # RSS feed generation
│   ├── html_generator.py      # HTML index page generation
│   └── templates/
│       └── index.html.j2      # Jinja2 template for index page
├── bin/                       # Utility scripts
│   ├── manage.py              # Offline operations CLI
│   └── generate_centers_config.py  # One-time config generation
├── forecasts/                 # Downloaded forecast data (not in git)
├── feeds/                     # Generated RSS feeds (not in git)
├── avalanche_centers.yaml     # Avalanche centers configuration
├── index.html                 # Generated index page
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## Usage

### Offline Operations CLI

The `bin/manage.py` script provides commands for managing forecasts and feeds:

```bash
# Show help
python3 bin/manage.py --help

# Full update - download all forecasts and regenerate all feeds
python3 bin/manage.py full-update

# Download forecast for a specific zone
python3 bin/manage.py download-forecast <center-slug> <zone-slug>
# Example:
python3 bin/manage.py download-forecast utah-avalanche-center salt-lake

# Generate RSS feed for a specific zone (without downloading new forecast)
python3 bin/manage.py generate-feed <center-slug> <zone-slug>

# Generate the HTML index page
python3 bin/manage.py generate-index
```

#### Finding Zone Slugs

Zone slugs are URL-friendly versions of zone names. You can find them by:
1. Looking at `avalanche_centers.yaml`
2. Running `bin/generate_centers_config.py` to see the full list
3. Browsing the generated `index.html` page

Examples:
- "Snoqualmie Pass" → `snoqualmie-pass`
- "Salt Lake" → `salt-lake`
- "Tetons" → `tetons`

### Development Server

Run the Flask development server with hot reload:

```bash
# Using Python directly
python3 app/main.py

# Or using Flask CLI
export FLASK_APP=app.main
flask run
```

Environment variables:
- `FLASK_DEBUG`: Enable debug mode (default: 1)
- `FLASK_PORT`: Port to run on (default: 5000)
- `FEEDS_DIR`: Directory for RSS feeds (default: feeds)
- `INDEX_HTML_PATH`: Path to index.html (default: index.html)

## Data Sources

All forecast data comes from the [avalanche.org API](https://api.avalanche.org/v2/public).

## Architecture

### Static Content Generation

AvyRss uses an offline generation model:
1. Forecasts are downloaded and stored as JSON files on disk
2. RSS feeds are pre-generated from stored forecasts
3. The HTML index page is generated from the configuration
4. The Flask app serves these pre-generated static files

This approach ensures:
- Fast response times (no on-demand generation)
- Low server load
- Simple deployment
- Reliable operation

### Directory Structure for Forecasts

Forecasts are stored in a hierarchical structure:
```
forecasts/{center-slug}/{zone-slug}/{year}/{YYYY-MM-DD}.json
```

This structure makes it easy to:
- Find the N most recent forecasts (sorted by date)
- Archive old forecasts by year
- Organize by center and zone

### RSS Feed Storage

RSS feeds are stored as:
```
feeds/{center-slug}/{zone-slug}.xml
```

## Development Workflow

### Adding a New Avalanche Center

If new centers need to be added to the configuration:

1. Edit `bin/generate_centers_config.py` and add the center to `SUPPORTED_CENTERS`
2. Run the script to regenerate `avalanche_centers.yaml`:
   ```bash
   python3 bin/generate_centers_config.py
   ```
3. Commit the updated YAML file

**Note:** The avalanche centers configuration should rarely change and should only be modified deliberately.

### Testing a Single Zone

To test with a single zone without downloading all forecasts:

```bash
# Download forecast for one zone
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass

# Generate RSS feed for that zone
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass

# Generate the index page
python3 bin/manage.py generate-index

# Start the server and test
python3 app/main.py
```

## Deployment

### Production Considerations

1. **Scheduled Updates**: Set up a cron job or scheduled task to run `bin/manage.py full-update` daily
2. **Environment Variables**: Configure production URLs in `.env`
3. **Web Server**: Use a production WSGI server like gunicorn instead of Flask's dev server
4. **Static Files**: Ensure `feeds/` and `forecasts/` directories are persistent
5. **Monitoring**: Use the `/health` endpoint for health checks

### Example Cron Job

```cron
# Update forecasts and feeds daily at 6 AM
0 6 * * * cd /path/to/avyrss && /path/to/avyrss/venv/bin/python bin/manage.py full-update
```

### Example Production Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

## Documentation

### For Users
- **[README.md](README.md)** (this file) - Overview, features, and basic usage
- **[SETUP.md](SETUP.md)** - Complete setup guide from scratch

### For Developers
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, data flow, critical rules
- **[TECHNICAL.md](TECHNICAL.md)** - Coding standards, preferences, anti-patterns
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow, debugging, common tasks
- **[FUTURE.md](FUTURE.md)** - Planned enhancements and roadmap

### Quick Links for AI Agents
If you're an AI agent starting a new session:
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) first for critical rules
2. Read [TECHNICAL.md](TECHNICAL.md) for coding standards
3. Read [DEVELOPMENT.md](DEVELOPMENT.md) for workflow guidance
4. Refer to [SETUP.md](SETUP.md) if troubleshooting setup issues

## Future Enhancements

See [FUTURE.md](FUTURE.md) for detailed roadmap. Planned enhancements include:
- Expanded HTML content for RSS feed entries
- Migration to S3 storage for forecasts and feeds


## License

[Add license information]

## Acknowledgments

- Forecast data provided by [avalanche.org](https://avalanche.org)
- Inspired by [avymail](https://github.com/username/avymail)
