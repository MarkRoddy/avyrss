# Running the Development Server

## Starting the Dev Server

The Flask development server must be run with the correct Python path so it can find the `app` module.

### Option 1: Using the provided command (Recommended)

From the project root directory:

```bash
source venv/bin/activate
PYTHONPATH=/home/exedev/dev/avyrss python3 app/main.py
```

Or use the full path to your project:

```bash
source venv/bin/activate
PYTHONPATH=$(pwd) python3 app/main.py
```

### Option 2: Run in background with logging

To run the server in the background and capture output to a log file:

```bash
source venv/bin/activate
PYTHONPATH=$(pwd) python3 app/main.py > logs/dev-server.log 2>&1 &
```

View the logs:
```bash
tail -f logs/dev-server.log
```

Stop the background server:
```bash
pkill -f "python3 app/main.py"
```

## Accessing the Server

Once running, the server is available at:

- **http://localhost:5000/** - Main index page
- **http://localhost:5000/feed/{center-slug}/{zone-slug}** - RSS feed for a specific zone
- **http://localhost:5000/health** - Health check endpoint

### Development Endpoints

- **http://localhost:5000/dev/preview-entry/{center-slug}/{zone-slug}** - Preview the HTML content of the latest RSS feed entry for a zone

Example:
```
http://localhost:5000/dev/preview-entry/northwest-avalanche-center/snoqualmie-pass
```

## Why PYTHONPATH is Required

The `app/main.py` file uses absolute imports like `from app.avalanche import AvalancheConfig`. When running Python scripts directly, Python needs to know where to find the `app` module. Setting `PYTHONPATH` to the project root tells Python where to look.

Without setting `PYTHONPATH`, you'll get this error:
```
ModuleNotFoundError: No module named 'app'
```

## Configuration

The dev server reads configuration from environment variables (optional):

- `FLASK_DEBUG` - Enable debug mode (default: 1)
- `FLASK_PORT` - Port to run on (default: 5000)
- `FEEDS_DIR` - Directory for RSS feeds (default: feeds)
- `INDEX_HTML_PATH` - Path to index.html (default: index.html)
- `FORECASTS_DIR` - Directory for forecasts (default: forecasts)

Example with custom port:
```bash
PYTHONPATH=$(pwd) FLASK_PORT=8000 python3 app/main.py
```

## Hot Reload

The dev server runs with debug mode enabled by default, which provides:
- Automatic reload when code changes
- Interactive debugger in the browser on errors
- Detailed error pages

**Note:** This is for development only. Never use the Flask development server in production.

## When to Restart the Dev Server

**You rarely need to manually restart the dev server.** Flask's debug mode automatically handles most changes:

- **Python code changes**: Flask automatically reloads (no manual restart needed)
- **RSS feed regeneration**: Read from disk on each request (no restart needed)
- **New forecast downloads**: Read from disk on each request (no restart needed)
- **index.html updates**: Read from disk on each request (no restart needed)

The only time you might need to manually restart is if Flask's auto-reload mechanism fails, which is uncommon during normal development.
