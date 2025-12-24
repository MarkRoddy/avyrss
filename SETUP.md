# AvyRss - Complete Setup Guide

This guide will walk you through setting up AvyRss from scratch, whether you're cloning the repository for the first time or starting fresh.

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- git (for cloning the repository)
- Internet connection (for API access)

## Initial Setup

### Step 1: Clone and Enter Project

```bash
git clone <repository-url>
cd avyrss
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Verify activation**: Your prompt should show `(venv)` prefix.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output**: Installation of Flask, requests, PyYAML, feedgen, and dependencies.

### Step 4: Set Up Environment Variables (Optional)

```bash
cp .env.example .env
```

Edit `.env` if you need to customize:
- `FLASK_PORT` - Change from default 5000
- `FEEDS_DIR` - Use different feeds directory
- `INDEX_HTML_PATH` - Use different index location

**For most users**: The defaults in `.env.example` are fine.

### Step 5: Generate Avalanche Centers Configuration

**Important**: This file should already exist in the repository. Only run this if it's missing:

```bash
python3 bin/generate_centers_config.py
```

This creates `avalanche_centers.yaml` with all supported avalanche centers and zones.

**You should see**: Confirmation that 14 centers and 57 zones were found.

## Verifying Setup

### Check Configuration

```bash
# Verify config file exists
ls -l avalanche_centers.yaml

# View first few lines
head -20 avalanche_centers.yaml
```

### Test the Offline Tools

```bash
# Generate the index page (works even without data)
python3 bin/manage.py generate-index

# Verify it was created
ls -l index.html
```

## Getting Your First Data

### Option A: Test with a Single Zone

Best for testing and development:

```bash
# Download one forecast
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass

# Generate RSS feed for that zone
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass

# Regenerate index (optional, but good practice)
python3 bin/manage.py generate-index
```

### Option B: Download Everything

Takes longer but gets you all data:

```bash
python3 bin/manage.py full-update
```

This will:
1. Download forecasts for all 57 zones (~2-3 minutes)
2. Generate RSS feeds for all zones
3. Display a summary of successes/failures

## Starting the Server

```bash
python3 app/main.py
```

**Expected output**:
```
 * Serving Flask app 'main'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

## Verifying Everything Works

### Test Endpoints

Open these URLs in your browser:

1. **Index Page**: http://localhost:5000/
   - Should show list of all centers and zones
   - Links should work (relative URLs)

2. **Health Check**: http://localhost:5000/health
   - Should return: `{"status": "ok"}`

3. **RSS Feed**: http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass
   - Should return XML (RSS feed)
   - Test in a feed reader for best experience

### Using curl (Alternative)

```bash
# Health check
curl http://localhost:5000/health

# Get RSS feed
curl http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass

# Get index page
curl http://localhost:5000/ | head -50
```

## Directory Structure After Setup

After successful setup, your directory should look like:

```
avyrss/
├── venv/                           # Virtual environment (gitignored)
├── app/                            # Application code
│   ├── main.py
│   ├── avalanche.py
│   ├── forecasts.py
│   ├── rss.py
│   ├── html_generator.py
│   └── templates/
│       └── index.html.j2
├── bin/                            # Utility scripts
│   ├── manage.py
│   └── generate_centers_config.py
├── forecasts/                      # Downloaded forecasts (gitignored)
│   └── northwest-avalanche-center/
│       └── snoqualmie-pass/
│           └── 2025/
│               └── 2025-12-21.json
├── feeds/                          # Generated RSS feeds (gitignored)
│   └── northwest-avalanche-center/
│       └── snoqualmie-pass.xml
├── avalanche_centers.yaml          # Configuration
├── index.html                      # Generated index page
├── requirements.txt                # Python dependencies
├── .env                            # Your environment config (gitignored)
├── .env.example                    # Example environment config
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── TECHNICAL.md
├── SETUP.md (this file)
└── FUTURE.md
```

## Common Issues and Solutions

### Issue: "avalanche_centers.yaml not found"

**Solution**: Generate it:
```bash
python3 bin/generate_centers_config.py
```

### Issue: "No module named 'flask'"

**Solution**: Activate venv and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: RSS feed returns 404

**Solution**: Generate the feed first:
```bash
python3 bin/manage.py generate-feed <center-slug> <zone-slug>
```

### Issue: Index page shows "not yet generated"

**Solution**: Generate it:
```bash
python3 bin/manage.py generate-index
```

### Issue: Forecast download fails

**Possible causes**:
- No internet connection
- API is down
- Invalid center/zone slug

**Debug**:
```bash
# Check center/zone exists in config
grep -A 5 "center-slug" avalanche_centers.yaml

# Try health check first
curl http://localhost:5000/health
```

### Issue: "Port 5000 already in use"

**Solution**: Either stop the other process or use different port:
```bash
FLASK_PORT=8000 python3 app/main.py
```

Or edit `.env`:
```
FLASK_PORT=8000
```

### Issue: Links on index page don't work

**Cause**: Hardcoded localhost URLs in old version.

**Solution**: The current version uses relative URLs. If you see absolute URLs, regenerate:
```bash
python3 bin/manage.py generate-index
```

## Next Steps

### For Development

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. Read [TECHNICAL.md](TECHNICAL.md) for coding standards
3. Make changes to code
4. Test with single zone before full update

### For Production Deployment

1. Set up scheduled daily updates:
   ```bash
   # Cron example: daily at 6 AM
   0 6 * * * cd /path/to/avyrss && /path/to/avyrss/venv/bin/python bin/manage.py full-update
   ```

2. Use production WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
   ```

3. Set up reverse proxy (nginx, caddy, etc.)

4. Configure environment for production:
   ```bash
   FLASK_DEBUG=0
   FLASK_ENV=production
   ```

### For Daily Operations

Update forecasts and feeds:
```bash
python3 bin/manage.py full-update
```

This should be run daily (via cron or scheduled task) to keep feeds fresh.

## Getting Help

- **README.md**: General usage and features
- **ARCHITECTURE.md**: System design and decisions
- **TECHNICAL.md**: Coding standards and preferences
- **FUTURE.md**: Planned enhancements

## Cheat Sheet

```bash
# Activate environment
source venv/bin/activate

# Download single forecast
python3 bin/manage.py download-forecast <center> <zone>

# Generate single feed
python3 bin/manage.py generate-feed <center> <zone>

# Full update (all zones)
python3 bin/manage.py full-update

# Generate index page
python3 bin/manage.py generate-index

# Start server
python3 app/main.py

# View logs (verbose)
python3 bin/manage.py full-update --verbose

# Get help
python3 bin/manage.py --help
python3 bin/manage.py <command> --help
```

## Finding Zone Slugs

Zone slugs are URL-friendly versions of zone names. Find them in:

1. **Config file**:
   ```bash
   cat avalanche_centers.yaml | grep -A 3 "slug:"
   ```

2. **Index page**: Browse to http://localhost:5000/ and look at the URLs

3. **Examples**:
   - "Snoqualmie Pass" → `snoqualmie-pass`
   - "Salt Lake" → `salt-lake`
   - "Tetons" → `tetons`
   - "Snake River Range" → `snake-river-range`
