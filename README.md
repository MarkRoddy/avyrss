# AvyRSS

RSS feeds for avalanche forecasts, making it easy to stay informed about backcountry conditions through your favorite feed reader.

## Overview

AvyRSS generates and serves RSS feeds for avalanche forecasts from various avalanche centers across North America. The feeds are updated daily and include the latest forecast bottom-line summaries with links to full forecast details.

**Key Features:**
- RSS feeds for 57 zones across 14 avalanche centers
- Pre-generated feeds served as static files (fast and efficient)
- Clean, simple HTML interface to browse and subscribe to feeds
- Offline batch processing for forecast downloads and feed generation

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

### 1. Download forecasts and generate RSS feeds

```bash
# Download a single forecast
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass

# Generate a single RSS feed
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass

# Or do a full update (download all forecasts and generate all feeds)
python3 bin/manage.py full-update
```

### 2. Start the development server (optional)

The Flask development server is useful for local testing:

```bash
python3 app/main.py
```

The application will be available at `http://localhost:5000`

- Index page: `http://localhost:5000/`
- RSS feed example: `http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass`

**Note**: Flask is for development only. In production, serve the static files (`index.html` and `feeds/`) directly using any static file server.

## Project Structure

```
.
├── app/                        # Application code
│   ├── __init__.py
│   ├── main.py                # Flask dev server (development only)
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

## Data Sources

All forecast data comes from the [avalanche.org API](https://api.avalanche.org/v2/public).

## Architecture

AvyRSS uses an offline generation model: forecasts are downloaded and stored as JSON files, RSS feeds are pre-generated from stored forecasts, and the Flask app serves these pre-generated static files. Forecasts are stored at `forecasts/{center-slug}/{zone-slug}/{year}/{YYYY-MM-DD}.json` and feeds at `feeds/{center-slug}/{zone-slug}.xml`.

## License

[Add license information]

## Acknowledgments

- Forecast data provided by [avalanche.org](https://avalanche.org)
- Inspired by [avymail](https://github.com/username/avymail)
