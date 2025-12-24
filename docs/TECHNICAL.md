# Technical Preferences and Standards

This document defines the technical preferences, coding standards, and tooling choices for the AvyRSS project.

## Language & Framework Choices

### Python
- **Version**: Python 3.12+ (currently 3.12.3)
- **Why**: Modern Python with excellent type hints, walrus operator, pattern matching
- **Type Hints**: Use them everywhere for better IDE support and documentation
- **Format**: Follow PEP 8 style guide

### Development Server
- **Choice**: Flask
- **Purpose**: Development and testing only (NOT for production)
- **Why**: Lightweight, simple, perfect for local testing of static content
- **Configuration**:
  - Development: hot reload enabled
  - Debug mode: on for development
  - Host: 0.0.0.0 (accessible from network)
  - Port: 5000 (configurable via environment)
- **Production**: Flask is NOT used. Serve static files with nginx/S3/etc.

### Frontend
- **HTML**: Static, generated from Jinja2 templates
- **CSS**: Vanilla CSS (no preprocessors)
- **JavaScript**: **AVOID** unless absolutely necessary
  - Current implementation: zero JavaScript
  - If needed in future: vanilla JS first, then simple libraries
  - **NEVER** use React, Vue, Angular, or similar heavy frameworks
- **Why**: Simplicity, no build step, works everywhere, no dependencies

## Dependency Management

### Python Environment
- **Tool**: virtualenv (standard library venv)
- **Location**: `./venv` (gitignored)
- **Activation**: `source venv/bin/activate`

### Dependencies
- **File**: `requirements.txt`
- **Format**: Pinned versions for reproducibility
- **Installation**: `pip install -r requirements.txt`

### Current Dependencies
```
Flask==3.1.0              # Web framework
Werkzeug==3.1.3          # WSGI utilities (Flask dependency)
python-dotenv==1.0.1     # Environment variable loading
PyYAML==6.0.2            # YAML parsing
requests==2.32.3         # HTTP client
feedgen==1.0.0           # RSS feed generation
Jinja2==3.1.4            # Templating (Flask includes it)
```

### Adding New Dependencies
1. Install in venv: `pip install package==version`
2. Update requirements.txt: `pip freeze > requirements.txt`
3. Document why it's needed in commit message
4. Keep dependencies minimal - prefer standard library when possible

## Configuration Management

### Environment Variables
- **Storage**: `.env` file (gitignored)
- **Example**: `.env.example` (checked in)
- **Loading**: `python-dotenv` library
- **Usage**: `os.getenv('VAR_NAME', 'default')`

### Configuration Files
- **avalanche_centers.yaml**: Checked into source control
- **Path Resolution**: Always relative to project root
  ```python
  PROJECT_ROOT = Path(__file__).parent.parent.resolve()
  ```

## Development Tooling

### Version Control
- **Tool**: Git
- **Ignored**: venv/, forecasts/, feeds/, .env, __pycache__/
- **What to commit**:
  - All code (*.py)
  - Templates (*.j2)
  - Configuration (avalanche_centers.yaml)
  - Documentation (*.md)
  - Dependencies (requirements.txt)
  - Example env (.env.example)

### CI/CD
- **Platform**: GitHub Actions (when set up)
- **Principle**: Actions invoke shell scripts, not inline code
- **Why**: Ensures CI commands can be run locally

### Scripts
- **Location**: `bin/` directory
- **Shebang**: `#!/usr/bin/env python3`
- **Permissions**: Make executable (`chmod +x`)
- **Structure**: Use argparse for CLI arguments

## Code Organization

### Module Structure
```python
"""
Module docstring explaining purpose.
"""

import standard_library
import third_party
from app import local_modules

# Constants
CONSTANT_NAME = value

# Classes/Functions
class ClassName:
    """Class docstring."""
    pass

def function_name(arg: Type) -> ReturnType:
    """Function docstring."""
    pass
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Usage
logger.info("Something happened")
logger.error("Error occurred", exc_info=True)
```

### Error Handling
- Catch specific exceptions, not bare `except:`
- Log errors with context
- Fail gracefully - errors in one zone shouldn't break all zones
- Return status tuples: `(success: bool, message: str, data: Optional)`

## File Operations

### Path Handling
```python
from pathlib import Path

# Good
file_path = Path(base_dir) / "subdir" / "file.txt"
if file_path.exists():
    with open(file_path, 'r') as f:
        data = f.read()

# Bad - don't use string concatenation
file_path = base_dir + "/subdir/file.txt"
```

### JSON Files
```python
import json

# Writing
with open(path, 'w') as f:
    json.dump(data, f, indent=2)

# Reading
with open(path, 'r') as f:
    data = json.load(f)
```

### YAML Files
```python
import yaml

# Reading
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Writing
with open('config.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

## API Integration

### HTTP Requests
```python
import requests

response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()
```

### Error Handling
```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f"API error: {e}")
    # Handle gracefully
```

### Rate Limiting
- Batch job runs once daily
- No rate limiting needed currently
- API is public, no authentication required

## Database

### Current Status
- **None** - filesystem only
- **Why**: Simple, sufficient for current scale
- **Future**: Only add if file-based queries become too complex

## Storage

### Current: Filesystem
- **Forecasts**: `forecasts/{center}/{zone}/{year}/{date}.json`
- **Feeds**: `feeds/{center}/{zone}.xml`
- **Generated**: `index.html`

### Future: S3 (not implemented)
- When implemented, maintain same logical structure
- Use boto3 for S3 operations
- Keep filesystem as option for local development

## Testing

### Current Approach
- Manual testing using single-zone commands
- Test with real API data
- Verify in browser/feed reader

### Future (if needed)
- pytest for unit tests
- Test with mock API responses
- Integration tests for full workflow

## Naming Conventions

### Files
- Python modules: `lowercase_with_underscores.py`
- Templates: `name.html.j2`
- Config: `lowercase_name.yaml`
- Scripts: `script_name.py`

### Code
- Functions: `lowercase_with_underscores`
- Classes: `PascalCase`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Variables: `lowercase_with_underscores`

### URL/Slugs
- Centers: `lowercase-with-hyphens`
- Zones: `lowercase-with-hyphens`
- Routes: `/lowercase/path`

## Flask Development Server

**Important**: Flask is for development/testing only. Production serves static files directly.

### Application Structure
```python
from flask import Flask

app = Flask(__name__)

@app.route('/path')
def handler():
    # Serve pre-generated static file
    return send_file(path, mimetype='...')

if __name__ == '__main__':
    # Development server only
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Response Types
- HTML: `send_file(path, mimetype='text/html')`
- RSS: `send_file(path, mimetype='application/rss+xml')`
- JSON: `return {'key': 'value'}` (Flask auto-converts)
- 404: `abort(404, description="message")`

### Static Files
- Serve pre-generated files using `send_file()`
- Never generate content in request handlers
- Keep routes thin - they're just file servers

### Production Serving
Flask is NOT used in production. Options include:
- **nginx**: Directly serve `index.html` and `feeds/` directory
- **S3 + CloudFront**: Upload static files to S3, serve via CDN
- **Apache**: Configure DocumentRoot to serve static files
- **Caddy**: Simple static file server with automatic HTTPS

No Python runtime required in production.

## Performance Considerations

### File I/O
- Use context managers (`with` statements)
- Close files properly
- Use buffered I/O for large files

### Memory
- Don't load all forecasts into memory
- Process zones one at a time
- Generator patterns where appropriate

### Network
- Set timeouts on all HTTP requests
- Handle connection errors gracefully
- Log request durations for monitoring

## Security Practices

### Input Validation
- Validate center/zone slugs against configuration
- Use Path objects to prevent traversal attacks
- Never execute user input

### Secrets Management
- Store in environment variables
- Use `.env` for development
- Never commit secrets to git
- Use .env.example for documentation

### File Permissions
- Forecasts/feeds: readable by web server
- Scripts: executable by developer
- Config files: readable by all

## Code Review Standards

When reviewing code (or AI-generated code):

1. **Correctness**: Does it work as intended?
2. **Simplicity**: Is it as simple as possible?
3. **Consistency**: Follows established patterns?
4. **Error handling**: Fails gracefully?
5. **Logging**: Sufficient for debugging?
6. **Documentation**: Clear docstrings and comments?
7. **No over-engineering**: Doesn't add unnecessary complexity?

## Anti-Patterns to Avoid

### Don't
- ❌ Dynamic content generation in request handlers
- ❌ Hardcoded localhost URLs in templates
- ❌ Heavy JavaScript frameworks
- ❌ Database for current scale
- ❌ Complex async/background workers (cron is sufficient)
- ❌ Modifying avalanche_centers.yaml without permission
- ❌ Flattening the forecast directory structure
- ❌ Using global mutable state

### Do
- ✅ Pre-generate all content offline
- ✅ Use relative URLs
- ✅ Keep frontend simple (HTML + CSS)
- ✅ Use filesystem storage
- ✅ Simple batch processing
- ✅ Treat config as immutable
- ✅ Maintain logical directory structure
- ✅ Pass state explicitly

## Questions Before Making Changes

Before implementing a feature, ask:

1. Can this be pre-generated instead of dynamic?
2. Is this the simplest solution?
3. Does this follow the static-first architecture?
4. Will this work on any domain (not just localhost)?
5. Is the added complexity justified?
6. Does this maintain the offline/online separation?

## Documentation Standards

### Code Comments
- Docstrings for all modules, classes, functions
- Explain "why" not "what" in comments
- Type hints serve as inline documentation

### Commit Messages
- First line: brief summary (<50 chars)
- Body: explanation of why (if non-obvious)
- Reference issues/tasks when applicable

### README Updates
- Keep README in sync with code
- Update examples when commands change
- Document new features immediately
