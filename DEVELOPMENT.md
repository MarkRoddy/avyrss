# Development Guide

This guide is for AI agents and developers working on AvyRss code.

## Quick Context

AvyRss generates static RSS feeds for avalanche forecasts. The architecture follows a strict **offline/online separation**:

- **Offline**: Download forecasts, generate RSS feeds and HTML (via `bin/manage.py`)
- **Online Development**: Flask dev server serves pre-generated static files for testing
- **Online Production**: Static file server (nginx/S3/etc.) serves pre-generated files - no Python runtime

## Starting a New Development Session

### 1. Read These Files First
- **README.md** - User-facing documentation, features, usage
- **ARCHITECTURE.md** - System design, critical rules, data flow
- **TECHNICAL.md** - Code standards, preferences, anti-patterns
- **SETUP.md** - Complete setup instructions

### 2. Understand Current State

```bash
# Check what's been generated
ls -la *.yaml *.html
ls -R forecasts/ feeds/ | head -20

# Check if server runs
source venv/bin/activate
python3 app/main.py
# Ctrl+C to stop

# Run health check
curl http://localhost:5000/health
```

### 3. Key Architectural Rules

**NEVER do these without explicit permission:**
- Regenerate or modify `avalanche_centers.yaml`
- Add dynamic content generation to Flask routes
- Use absolute URLs (http://localhost:...) in templates
- Change the forecast directory structure
- Add a database
- Use Flask in production (it's dev-only)

**ALWAYS do these:**
- Use relative URLs in templates (`/feed/...` not `http://...`)
- Use Path objects for file operations
- Resolve paths relative to PROJECT_ROOT
- Keep offline/online separation clear
- Test with single zone before full updates
- Remember Flask is for development/testing only

## Common Development Tasks

### Adding a New Feature

1. **Determine if it's offline or online**
   - Offline: Batch processing, generation → Add to `bin/manage.py` or app modules
   - Online: Serving content → Add to `app/main.py` (but probably just serve static files)

2. **Follow the pattern**
   - Look at similar existing code
   - Maintain consistency with established patterns
   - Keep it simple

3. **Test incrementally**
   ```bash
   # Test with one zone
   python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass
   python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass

   # Then test in Flask
   python3 app/main.py
   curl http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass
   ```

### Modifying RSS Feed Content

1. **Edit**: `app/rss.py` - specifically `extract_forecast_info()` and `generate_rss_feed()`
2. **Test generation**:
   ```bash
   python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass
   cat feeds/northwest-avalanche-center/snoqualmie-pass.xml
   ```
3. **Validate**: Feed readers or https://validator.w3.org/feed/

### Modifying HTML Index Page

1. **Edit**: `app/templates/index.html.j2`
2. **Regenerate**:
   ```bash
   python3 bin/manage.py generate-index
   ```
3. **Test**:
   ```bash
   python3 app/main.py
   # Browse to http://localhost:5000/
   ```

### Adding a Flask Route

**Note**: Flask is for development only. Only add routes for local testing purposes.

```python
# In app/main.py

@app.route('/new-route')
def new_route():
    """Describe what this route does."""
    # Serve a static file (preferred)
    file_path = PROJECT_ROOT / 'path' / 'to' / 'file.ext'
    if not file_path.exists():
        abort(404, description="File not found")
    return send_file(file_path, mimetype='...')
```

**Remember**:
- Don't generate content dynamically. Serve pre-generated files.
- Flask routes are for development testing only
- Production will serve the same static files directly (no Flask)

### Modifying API Calls

1. **Edit**: `app/avalanche.py` - specifically `fetch_forecast()`
2. **Understand the response**:
   ```bash
   # Download and inspect
   python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass
   cat forecasts/northwest-avalanche-center/snoqualmie-pass/2025/2025-12-21.json | jq .
   ```
3. **Update downstream code** if response structure changes

### Adding a New CLI Command

```python
# In bin/manage.py

def cmd_new_command(args):
    """Description of what this command does."""
    # Implementation
    print(f"✓ Success message")

# In main(), add to subparsers:
parser_new = subparsers.add_parser(
    'new-command',
    help='Help text for command'
)
parser_new.add_argument('arg1', help='Argument help')
parser_new.set_defaults(func=cmd_new_command)
```

## Testing Strategy

### Manual Testing (Current Approach)

```bash
# 1. Test with single zone
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass
python3 bin/manage.py generate-index

# 2. Start server
python3 app/main.py

# 3. Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/
curl http://localhost:5000/feed/northwest-avalanche-center/snoqualmie-pass

# 4. Test in feed reader
# Copy URL to your favorite RSS reader app
```

### What to Test

- ✅ Forecast downloads successfully
- ✅ RSS feed generates valid XML
- ✅ Index page lists all zones
- ✅ Links in index are relative (not absolute)
- ✅ Server serves files correctly
- ✅ 404 handling works for missing feeds
- ✅ Error handling doesn't crash full-update

## Code Review Checklist

When reviewing changes (your own or others'):

### Functionality
- [ ] Does it work as intended?
- [ ] Edge cases handled?
- [ ] Errors logged appropriately?

### Architecture
- [ ] Maintains offline/online separation?
- [ ] No dynamic generation in Flask routes?
- [ ] Uses relative URLs?
- [ ] Follows static-first principle?

### Code Quality
- [ ] Follows patterns in TECHNICAL.md?
- [ ] Proper type hints?
- [ ] Docstrings for new functions?
- [ ] Logging added where needed?
- [ ] No unnecessary complexity?

### Testing
- [ ] Tested with single zone?
- [ ] Tested in browser/feed reader?
- [ ] No regressions in existing features?

## Debugging Tips

### Forecast Download Issues

```bash
# Check config has the zone
grep -A 10 "northwest-avalanche-center" avalanche_centers.yaml

# Try with verbose logging
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from app.avalanche import AvalancheConfig, fetch_forecast
config = AvalancheConfig()
center_id = config.get_center_id('northwest-avalanche-center')
zone_id = config.get_zone_id('northwest-avalanche-center', 'snoqualmie-pass')
print(f'Center: {center_id}, Zone: {zone_id}')
result = fetch_forecast(center_id, zone_id)
print(result)
"
```

### RSS Feed Generation Issues

```bash
# Check forecasts exist
ls -la forecasts/northwest-avalanche-center/snoqualmie-pass/

# Try generating directly
python3 -c "
from app.avalanche import AvalancheConfig
from app.rss import generate_feed_for_zone
config = AvalancheConfig()
path = generate_feed_for_zone('northwest-avalanche-center', 'snoqualmie-pass', config)
print(f'Generated: {path}')
"

# Validate XML
python3 -m xml.etree.ElementTree feeds/northwest-avalanche-center/snoqualmie-pass.xml
```

### Flask Route Issues

```bash
# Check path resolution
python3 -c "
from pathlib import Path
PROJECT_ROOT = Path('app/main.py').parent.parent.resolve()
print(f'Project root: {PROJECT_ROOT}')
print(f'Feeds dir: {PROJECT_ROOT / \"feeds\"}')
print(f'Exists: {(PROJECT_ROOT / \"feeds\").exists()}')
"

# Check server logs
python3 app/main.py
# Server logs will show file paths being accessed
```

### Path Issues

```python
# Always do this in Flask app
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FEEDS_DIR = PROJECT_ROOT / os.getenv('FEEDS_DIR', 'feeds')

# Use paths relative to PROJECT_ROOT
feed_path = FEEDS_DIR / center_slug / f"{zone_slug}.xml"
```

## Common Mistakes to Avoid

### ❌ Hardcoded Localhost

```html
<!-- BAD -->
<a href="http://localhost:5000/feed/...">

<!-- GOOD -->
<a href="/feed/...">
```

### ❌ Dynamic Generation in Routes

```python
# BAD
@app.route('/feed/<center>/<zone>')
def serve_feed(center, zone):
    forecast = download_forecast(center, zone)  # ❌ Downloading on request
    rss = generate_rss(forecast)                # ❌ Generating on request
    return Response(rss, mimetype='application/rss+xml')

# GOOD
@app.route('/feed/<center>/<zone>')
def serve_feed(center, zone):
    feed_path = FEEDS_DIR / center / f"{zone}.xml"  # ✅ Pre-generated file
    if not feed_path.exists():
        abort(404)
    return send_file(feed_path, mimetype='application/rss+xml')
```

### ❌ String Path Concatenation

```python
# BAD
path = base_dir + "/" + center + "/" + zone + ".xml"

# GOOD
path = Path(base_dir) / center / f"{zone}.xml"
```

### ❌ Modifying avalanche_centers.yaml Without Permission

```python
# BAD - regenerating config without asking
centers = fetch_all_centers()
save_config(centers)

# GOOD - only when explicitly requested
# And ask user first before regenerating
```

## File Modification Guidelines

### Can Modify Freely
- `app/*.py` - Application code
- `app/templates/*.j2` - Templates
- `bin/manage.py` - CLI tool
- Test data in `forecasts/` and `feeds/` (not committed)

### Modify Carefully
- `avalanche_centers.yaml` - Only when adding/removing centers (ask first)
- `requirements.txt` - Only when adding dependencies (document why)
- `.gitignore` - Only when needed (consider impact)

### Never Modify Without Permission
- The core architecture (static file serving)
- The directory structure for forecasts/feeds
- The offline/online separation principle

## Environment Variables

Current variables (see `.env.example`):

```bash
# Flask config
FLASK_APP=app.main
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_PORT=5000

# Paths
FEEDS_DIR=feeds
INDEX_HTML_PATH=index.html
```

When adding new variables:
1. Add to `.env.example` with comment
2. Use `os.getenv('VAR', 'default')` in code
3. Document in README.md

## Dependencies

Current stack is minimal. Before adding new dependencies, ask:

1. Can we use the standard library instead?
2. Is this dependency well-maintained?
3. Does it add significant value?
4. What's the cost (size, complexity, security)?

## Git Workflow

### Before Committing

```bash
# Check what's changed
git status
git diff

# Don't commit generated files
# These should already be in .gitignore:
# - venv/
# - forecasts/
# - feeds/
# - __pycache__/
# - .env

# index.html CAN be committed (it's static and rarely changes)
```

### Commit Message Format

```
Brief summary (50 chars or less)

More detailed explanation if needed. Explain WHY the
change was made, not just WHAT was changed.

- Bullet points for multiple changes
- Reference issues if applicable
```

## Performance Considerations

### File I/O
- Use context managers (`with`)
- Process zones sequentially (don't load all at once)
- Close files properly

### Network
- API calls should timeout (currently 30s)
- Batch job runs once daily (not per request)
- Log request durations

### Memory
- Don't load all forecasts into memory
- Process one zone at a time in full-update
- Use generators when appropriate

## When to Ask for Help

Ask the user if you're unsure about:

1. **Architectural changes** - Affects core design
2. **Config changes** - Modifying `avalanche_centers.yaml`
3. **New dependencies** - Adding to `requirements.txt`
4. **Breaking changes** - Affects existing functionality
5. **Multiple approaches** - Which direction to take
6. **Requirements unclear** - Need clarification

## Quick Reference

```bash
# Project setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate config (if needed)
python3 bin/generate_centers_config.py

# Test single zone
python3 bin/manage.py download-forecast northwest-avalanche-center snoqualmie-pass
python3 bin/manage.py generate-feed northwest-avalanche-center snoqualmie-pass
python3 bin/manage.py generate-index

# Run server
python3 app/main.py

# Full update
python3 bin/manage.py full-update

# Common paths
# - Config: avalanche_centers.yaml
# - Templates: app/templates/
# - Generated HTML: index.html
# - Forecasts: forecasts/{center}/{zone}/{year}/{date}.json
# - Feeds: feeds/{center}/{zone}.xml
```

## Resources

- **Flask docs**: https://flask.palletsprojects.com/
- **feedgen docs**: https://feedgen.kiesow.be/
- **avalanche.org API**: https://api.avalanche.org/v2/public
- **RSS 2.0 spec**: https://www.rssboard.org/rss-specification
