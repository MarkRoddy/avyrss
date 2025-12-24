# AvyRss - Architecture

This document outlines the system architecture, design decisions, and constraints for the AvyRss project.

## Overview

AvyRss is a web application that generates and serves RSS feeds for avalanche forecasts. The key architectural principle is **static content generation** - all user-facing content is pre-generated offline and served as static files.

## System Architecture

### High-Level Flow

```
1. Offline: Download forecasts from avalanche.org API → Store as JSON
2. Offline: Generate RSS feeds from stored forecasts → Store as XML
3. Offline: Generate HTML index page from configuration
4. Online: Flask app serves pre-generated static files
```

### Why Static Generation?

- **Performance**: No on-demand generation = fast response times
- **Reliability**: API issues don't affect user-facing service
- **Simplicity**: No database, no complex caching, minimal infrastructure
- **Efficiency**: Low server load, can handle high traffic

## Key Architectural Decisions

### 1. Avalanche Centers Configuration

**Storage**: `avalanche_centers.yaml` - checked into source control

**Structure**:
```yaml
avalanche_centers:
  center-slug:
    name: "Human Readable Name"
    id: "API_ID"
    zones:
      - name: "Zone Name"
        slug: "zone-slug"
        id: "zone_api_id"
```

**Rules**:
- Generated once using `bin/generate_centers_config.py`
- Filtered to only include tier-1 centers that forecast daily
- Should rarely change - only modify deliberately
- Uses slugs (URL-friendly names) as keys for consistent routing

### 2. Forecast Storage

**Location**: `forecasts/{center-slug}/{zone-slug}/{YYYY}/{YYYY-MM-DD}.json`

**Why This Structure?**:
- Date-based organization makes it easy to find recent forecasts
- Hierarchical by center/zone for logical organization
- Year subdirectory for archival management
- Filename sorting gives chronological order naturally

**Storage Format**:
```json
{
  "request_time": "2025-12-21T17:06:13.276Z",
  "request_duration_ms": 203,
  "forecast": { /* raw API response */ }
}
```

**Rules**:
- One file per forecast per day
- Includes metadata (when fetched, how long it took)
- Preserves original API response format
- Not checked into source control (generated data)

### 3. RSS Feed Generation

**Location**: `feeds/{center-slug}/{zone-slug}.xml`

**Content**:
- Last 10 forecasts per zone
- Bottom-line summary as description
- Link to full forecast on avalanche.org
- Proper RSS 2.0 format with publication dates

**Generation**:
- Reads from stored forecast JSON files
- Extracts bottom_line and relevant metadata
- Generates valid RSS XML using feedgen library
- Saved as static XML file

**Rules**:
- Pre-generated offline, not on request
- Not checked into source control (generated data)
- One XML file per zone

### 4. HTML Index Page

**Location**: `index.html` (project root)

**Generation**:
- Template: `app/templates/index.html.j2`
- Uses Jinja2 templating
- Reads from `avalanche_centers.yaml`
- Lists all centers and zones with RSS feed links

**Rules**:
- Pre-generated offline
- Can be checked into source control (static, rarely changes)
- Uses relative URLs (works on any domain)

### 5. Flask Web Application

**Responsibilities**:
- Serve pre-generated RSS feeds at `/feed/{center}/{zone}`
- Serve pre-generated index.html at `/`
- Health check endpoint at `/health`
- **NOT** responsible for generating content

**Configuration**:
- Uses environment variables for paths
- Resolves paths relative to project root
- Development mode: hot reload enabled
- Production: should use WSGI server (gunicorn)

## Data Flow Diagrams

### Offline Processing (Daily Batch Job)

```
avalanche_centers.yaml
        ↓
[Enumerate all zones] → [For each zone:]
        ↓
[Fetch from API] → forecasts/{center}/{zone}/{year}/{date}.json
        ↓
[Read last 10] → [Generate RSS] → feeds/{center}/{zone}.xml
        ↓
[Generate index.html from config]
```

### Online Request Flow

```
User Request → Flask App
                 ↓
        /feed/{center}/{zone}
                 ↓
        Read feeds/{center}/{zone}.xml
                 ↓
        Return XML with RSS content-type
```

## Technology Stack

### Backend
- **Python 3.12+**: Modern Python with type hints
- **Flask**: Lightweight web framework for serving static content
- **requests**: HTTP client for API calls
- **PyYAML**: Configuration file parsing
- **feedgen**: RSS feed generation
- **Jinja2**: HTML templating (included with Flask)
- **python-dotenv**: Environment variable management

### Frontend
- **Static HTML**: No JavaScript framework needed
- **CSS**: Vanilla CSS for styling
- **SVG**: For icons (RSS icon)

### Storage
- **Filesystem**: Current implementation
- **S3**: Future enhancement (not yet implemented)

### Infrastructure
- **No database**: All data in files
- **No task queue**: Batch processing via cron/scheduled task
- **No caching layer**: Files are the cache

## Security Considerations

### Input Validation
- Zone/center slugs validated against configuration
- Path traversal prevented by using Path objects
- 404 for missing feeds (no error details exposed)

### API Usage
- No API keys required (public avalanche.org API)
- Rate limiting: batch job runs once daily
- Error handling: API failures don't crash the system

### File Safety
- Forecasts/feeds stored outside web root
- No user-uploaded content
- Static file serving only (no code execution)

## Scalability

### Current Limits
- 14 avalanche centers
- 57 zones total
- ~50KB per RSS feed
- ~50KB per forecast JSON
- Approx 3MB total storage for all feeds

### Growth Handling
- Linear scaling: more zones = more files
- No database bottlenecks
- Static files can be CDN-cached
- Can move to S3 for distributed storage

## Error Handling Strategy

### API Failures
- Log error but continue processing other zones
- Store error in forecast JSON for debugging
- Old RSS feeds remain available
- Full update provides summary of successes/failures

### Missing Data
- RSS feed shows "no data available" if no forecasts
- Index page works even if feeds don't exist
- Graceful degradation throughout

## Future Architecture Considerations

### Planned Enhancements (see FUTURE.md)
1. **S3 Storage**: Move forecasts/feeds to object storage
2. **Enhanced RSS Content**: More forecast details in feed entries
3. **Email Notifications**: Optional (separate from RSS)

### Potential Improvements (not planned)
- Database for forecast metadata (if querying becomes complex)
- API endpoint for programmatic access
- Webhook notifications when forecasts update
- Multi-region deployment

## Development Principles

1. **Keep it simple**: Avoid over-engineering
2. **Static first**: Pre-generate when possible
3. **Fail gracefully**: Errors shouldn't break the whole system
4. **Log everything**: Comprehensive logging for debugging
5. **Test manually**: Use single-zone commands for testing

## File Organization

```
/
├── app/                    # Application code
│   ├── main.py            # Flask app
│   ├── avalanche.py       # Config & API client
│   ├── forecasts.py       # Forecast management
│   ├── rss.py             # RSS generation
│   ├── html_generator.py  # Index page generation
│   └── templates/         # Jinja2 templates
├── bin/                   # CLI scripts
│   ├── manage.py          # Main operations script
│   └── generate_centers_config.py  # One-time setup
├── forecasts/             # Generated data (gitignored)
├── feeds/                 # Generated RSS (gitignored)
├── avalanche_centers.yaml # Configuration
├── index.html            # Generated index
├── requirements.txt      # Python dependencies
├── .env                  # Environment config (gitignored)
└── README.md             # User documentation
```

## Critical Rules for AI Agents

1. **NEVER regenerate avalanche_centers.yaml without explicit permission**
   - It's configuration, not code
   - Changes affect all zones/feeds
   - Only modify to add/remove centers deliberately

2. **Always use relative URLs in HTML templates**
   - App may be accessed from different domains
   - Never hardcode localhost or specific domains

3. **Preserve the directory structure for forecasts**
   - Code depends on date-based organization
   - Don't flatten or reorganize arbitrarily

4. **Flask app serves static files only**
   - Don't add dynamic generation to request handlers
   - Keep the offline/online separation clear

5. **Use Path objects for file operations**
   - Resolve paths relative to project root
   - Prevents path issues when running from different directories
