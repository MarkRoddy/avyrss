#!/bin/bash
#
# AvyRSS Standalone Installation Script
#
# This script contains all necessary configuration files embedded as heredocs.
# Download and run this single file to install AvyRSS on a production server.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/MarkRoddy/avyrss/main/install/install-standalone.sh | sudo bash
#   OR
#   wget -O - https://raw.githubusercontent.com/MarkRoddy/avyrss/main/install/install-standalone.sh | sudo bash
#   OR
#   Download and run locally:
#   curl -fsSL https://raw.githubusercontent.com/MarkRoddy/avyrss/main/install/install-standalone.sh -o install-avyrss.sh
#   sudo bash install-avyrss.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Configuration
BASE_DIR="/var/www"
LOG_FILE="/var/log/avyrss-update.log"
NGINX_SITE="avyrss.com"

echo ""
echo "========================================="
echo "  AvyRSS Installation Script"
echo "========================================="
echo ""
log_info "This script will install AvyRSS on your server"
log_info "Base directory: $BASE_DIR"
log_info "Domain: $NGINX_SITE"
echo ""

# Step 1: Check prerequisites
log_step "Step 1/5: Checking prerequisites..."

# Check for required commands
MISSING_COMMANDS=()

if ! command -v nginx &> /dev/null; then
    MISSING_COMMANDS+=("nginx")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_COMMANDS+=("python3")
fi

if ! command -v git &> /dev/null; then
    MISSING_COMMANDS+=("git")
fi

if ! command -v curl &> /dev/null; then
    MISSING_COMMANDS+=("curl")
fi

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    log_error "Missing required commands: ${MISSING_COMMANDS[*]}"
    log_error "Please install them and try again"
    log_error "Example: sudo apt install nginx python3 git curl"
    exit 1
fi

log_info "✓ All prerequisites satisfied"

# Check if www-data user exists
if ! id -u www-data &> /dev/null; then
    log_error "www-data user does not exist"
    exit 1
fi

log_info "✓ www-data user exists"

# Create dedicated avyrss user if it doesn't exist
if ! id -u avyrss &> /dev/null; then
    log_info "Creating dedicated avyrss user..."
    useradd -r -s /bin/bash -d /var/lib/avyrss -c "AvyRSS Service User" avyrss
    log_info "✓ Created avyrss user"
else
    log_info "✓ avyrss user already exists"
fi

# Add avyrss user to www-data group for file sharing
if ! id -nG avyrss | grep -qw www-data; then
    log_info "Adding avyrss to www-data group..."
    usermod -a -G www-data avyrss
    log_info "✓ avyrss added to www-data group"
else
    log_info "✓ avyrss already in www-data group"
fi

# Create base directory if needed
if [ ! -d "$BASE_DIR" ]; then
    log_info "Creating base directory: $BASE_DIR"
    mkdir -p "$BASE_DIR"
fi

# Create and set ownership of avyrss directory for update script
if [ ! -d "$BASE_DIR/avyrss" ]; then
    log_info "Creating AvyRSS directory: $BASE_DIR/avyrss"
    mkdir -p "$BASE_DIR/avyrss"
fi

chown -R avyrss:www-data "$BASE_DIR/avyrss"
log_info "✓ Base directory configured: $BASE_DIR/avyrss"

echo ""

# Step 2: Set up log file
log_step "Step 2/5: Setting up log file..."

if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    log_info "Created log file: $LOG_FILE"
fi

chown avyrss:www-data "$LOG_FILE"
chmod 644 "$LOG_FILE"

log_info "✓ Log file configured: $LOG_FILE"

echo ""

# Step 3: Install systemd timer and service
log_step "Step 3/5: Installing systemd timer and service..."

# Create systemd timer file
log_info "Creating systemd timer..."
cat > /etc/systemd/system/avyrss-update.timer <<'EOF'
# AvyRSS Feed Update Timer
#
# This systemd timer runs the feed update process every 6 hours at fixed UTC times.
#
# Schedule (UTC times - works regardless of server timezone):
#   3am UTC  - 7pm PST / 8pm PDT (catches fresh forecasts)
#   9am UTC  - 1am PST / 2am PDT
#   3pm UTC  - 7am PST / 8am PDT
#   9pm UTC  - 1pm PST / 2pm PDT

[Unit]
Description=AvyRSS Feed Update Timer
Documentation=https://github.com/MarkRoddy/avyrss

[Timer]
# Run at 3am, 9am, 3pm, 9pm UTC daily
OnCalendar=*-*-* 03,09,15,21:00:00

# If system was down, run missed updates on next boot
Persistent=true

# Randomize start time by up to 5 minutes to avoid thundering herd
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

log_info "✓ Created systemd timer"

# Create systemd service file
log_info "Creating systemd service..."
cat > /etc/systemd/system/avyrss-update.service <<'EOF'
# AvyRSS Feed Update Service
#
# This systemd service updates AvyRSS feeds by fetching fresh avalanche forecasts
# and regenerating RSS feeds and the index page.
#
# Security:
#   - Runs as dedicated 'avyrss' user (not www-data)
#   - Files created with group www-data for nginx access
#   - UMask 0002 ensures group write permissions
#   - www-data remains locked down (no shell required)

[Unit]
Description=AvyRSS Feed Update Service
Documentation=https://github.com/MarkRoddy/avyrss
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot

# Run as dedicated user with www-data group
User=avyrss
Group=www-data

# Ensure group-writable files for www-data nginx access
UMask=0002

# Working directory
WorkingDirectory=/var/www

# Fetch and execute update script from GitHub
# This ensures we always run the latest version
ExecStart=/bin/bash -c 'curl -fsSL https://raw.githubusercontent.com/MarkRoddy/avyrss/refs/heads/main/bin/update-feeds.sh | bash -s -- /var/www'

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=avyrss-update

# Security hardening
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/avyrss /var/log

# Resource limits
# Timeout after 15 minutes (should complete in <5 minutes normally)
TimeoutStartSec=900
EOF

log_info "✓ Created systemd service"

# Reload systemd daemon
systemctl daemon-reload
log_info "✓ Systemd daemon reloaded"

# Enable and start timer
systemctl enable avyrss-update.timer
systemctl start avyrss-update.timer
log_info "✓ Timer enabled and started"

log_info "Update schedule:"
log_info "  • 3am UTC  - 7pm PST / 8pm PDT (catches fresh forecasts)"
log_info "  • 9am UTC  - 1am PST / 2am PDT"
log_info "  • 3pm UTC  - 7am PST / 8am PDT"
log_info "  • 9pm UTC  - 1pm PST / 2pm PDT"

echo ""

# Step 4: Clone repository and run initial update
log_step "Step 4/5: Setting up repository and generating initial feeds (this may take a few minutes)..."

REPO_PATH="$BASE_DIR/avyrss"
REPO_URL="https://github.com/MarkRoddy/avyrss.git"

# Clone or update repository
if [ -d "$REPO_PATH/.git" ]; then
    log_info "Repository exists, pulling latest changes..."
    cd "$REPO_PATH"
    sudo -u avyrss git pull origin main 2>&1 | tee -a "$LOG_FILE"
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_error "Failed to pull latest changes"
        exit 1
    fi
else
    log_info "Cloning repository..."
    # Clone as root, then fix ownership
    if [ -d "$REPO_PATH" ]; then
        rm -rf "$REPO_PATH"
    fi

    git clone "$REPO_URL" "$REPO_PATH" 2>&1 | tee -a "$LOG_FILE"
    if [ $? -ne 0 ]; then
        log_error "Failed to clone repository"
        exit 1
    fi

    # Set ownership to avyrss user
    chown -R avyrss:www-data "$REPO_PATH"
    log_info "✓ Repository cloned successfully"
fi

cd "$REPO_PATH"

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    sudo -u avyrss python3 -m venv venv 2>&1 | tee -a "$LOG_FILE"

    log_info "Installing dependencies..."
    sudo -u avyrss bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt" 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_error "Failed to install dependencies"
        exit 1
    fi
else
    log_info "✓ Virtual environment already exists"
fi

# Run full update to generate feeds
log_info "Downloading forecasts and generating RSS feeds..."
sudo -u avyrss bash -c "source venv/bin/activate && python3 bin/manage.py full-update" 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_info "✓ Initial update completed successfully"

    # Set up group permissions with setgid for future updates
    if [ -d "$REPO_PATH/forecasts" ]; then
        chown -R avyrss:www-data "$REPO_PATH/forecasts"
        chmod -R g+w "$REPO_PATH/forecasts"
        chmod g+s "$REPO_PATH/forecasts"
        log_info "✓ Set group permissions on forecasts/"
    fi

    if [ -d "$REPO_PATH/feeds" ]; then
        chown -R avyrss:www-data "$REPO_PATH/feeds"
        chmod -R g+w "$REPO_PATH/feeds"
        chmod g+s "$REPO_PATH/feeds"
        log_info "✓ Set group permissions on feeds/"
    fi

    if [ -f "$REPO_PATH/index.html" ]; then
        chown avyrss:www-data "$REPO_PATH/index.html"
        chmod g+w "$REPO_PATH/index.html"
        log_info "✓ Set group permissions on index.html"
    fi
else
    log_error "Initial update failed - check $LOG_FILE for details"
    exit 1
fi

echo ""

# Step 5: Install nginx configuration
log_step "Step 5/5: Installing nginx configuration..."

# Create nginx config file
log_info "Creating nginx configuration..."
cat > "/etc/nginx/sites-available/$NGINX_SITE" <<'EOF'
# AvyRSS Nginx Configuration
#
# This configuration serves the AvyRSS static files for avyrss.com

# Redirect www to non-www
server {
    listen 80;
    listen [::]:80;

    server_name www.avyrss.com;

    # Redirect to non-www
    return 301 http://avyrss.com$request_uri;
}

# Main server block
server {
    listen 80;
    listen [::]:80;

    server_name avyrss.com;

    # Root directory where AvyRSS files are located
    root /var/www/avyrss;

    # Logging
    access_log /var/log/nginx/avyrss-access.log;
    error_log /var/log/nginx/avyrss-error.log;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Serve index.html at root
    location = / {
        try_files /index.html =404;

        # Cache for 1 hour (forecasts don't change that often)
        add_header Cache-Control "public, max-age=3600";
    }

    # Serve RSS feeds
    location /feed/ {
        # RSS feeds are in feeds/ directory
        # URL: /feed/center/zone maps to feeds/center/zone.xml
        rewrite ^/feed/(.*)$ /feeds/$1.xml break;

        try_files $uri =404;

        # Correct content type for RSS
        types {
            application/rss+xml xml;
        }

        # Cache for 1 hour
        add_header Cache-Control "public, max-age=3600";

        # CORS headers (allow feed readers from any origin)
        add_header Access-Control-Allow-Origin "*";
    }

    # Deny access to hidden files (except .well-known for certbot)
    location ~ /\.(?!well-known) {
        deny all;
    }

    # Deny access to sensitive files
    location ~ /\.(git|env|yaml)$ {
        deny all;
    }

    location ~ /venv/ {
        deny all;
    }

    location ~ /bin/ {
        deny all;
    }
}
EOF

log_info "✓ Created nginx configuration at /etc/nginx/sites-available/$NGINX_SITE"

# Enable site
if [ ! -L "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
    ln -s "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/$NGINX_SITE"
    log_info "✓ Enabled nginx site"
else
    log_info "✓ Nginx site already enabled"
fi

# Test nginx configuration
log_info "Testing nginx configuration..."
if nginx -t 2>&1; then
    log_info "✓ Nginx configuration is valid"

    # Reload nginx
    systemctl reload nginx
    log_info "✓ Nginx reloaded"
else
    log_error "Nginx configuration test failed"
    log_error "Please check the nginx configuration"
    exit 1
fi

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
log_info "AvyRSS has been installed successfully"
echo ""
log_info "Next steps:"
log_info "  1. Ensure DNS for avyrss.com points to this server"
log_info "  2. Site should be accessible at http://avyrss.com"
log_info "  3. Check logs: journalctl -u avyrss-update -f"
log_info "  4. Monitor timer: systemctl status avyrss-update.timer"
echo ""
log_info "Files installed:"
log_info "  • Repository: $BASE_DIR/avyrss"
log_info "  • RSS feeds: $BASE_DIR/avyrss/feeds/"
log_info "  • Index page: $BASE_DIR/avyrss/index.html"
log_info "  • Nginx config: /etc/nginx/sites-available/$NGINX_SITE"
log_info "  • Systemd timer: /etc/systemd/system/avyrss-update.timer"
log_info "  • Systemd service: /etc/systemd/system/avyrss-update.service"
log_info "  • Logs: $LOG_FILE and journalctl -u avyrss-update"
echo ""

if [ -f "$BASE_DIR/avyrss/index.html" ]; then
    log_info "✓ Site is ready!"
else
    log_warn "Index file not found - initial update may have failed"
    log_warn "Check $LOG_FILE for errors"
fi

echo ""
