#!/bin/bash
#
# AvyRSS Feed Update Script
#
# This script automates the process of updating the AvyRSS repository
# and regenerating all RSS feeds with the latest avalanche forecasts.
#
# Usage: ./update-feeds.sh <base_directory>
# Example: ./update-feeds.sh /home/me/apps
#
# The script will:
# 1. Clone the repo (if not exists) or pull latest changes (if exists)
# 2. Activate the Python virtual environment
# 3. Download latest forecasts from avalanche.org API
# 4. Generate updated RSS feeds
#

set -e  # Exit on error

# Configuration
REPO_URL="${AVYRSS_REPO_URL:-https://github.com/MarkRoddy/avyrss.git}"
REPO_NAME="avyrss"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -ne 1 ]; then
    log_error "Usage: $0 <base_directory>"
    log_error "Example: $0 /home/me/apps"
    exit 1
fi

BASE_DIR="$1"
REPO_PATH="$BASE_DIR/$REPO_NAME"

# Validate base directory
if [ ! -d "$BASE_DIR" ]; then
    log_error "Directory does not exist: $BASE_DIR"
    exit 1
fi

# Check write permissions
# If repo path already exists, check if we can write to it
# Otherwise, check if we can write to the base directory
if [ -d "$REPO_PATH" ]; then
    if [ ! -w "$REPO_PATH" ]; then
        log_error "Repository directory is not writable: $REPO_PATH"
        exit 1
    fi
else
    if [ ! -w "$BASE_DIR" ]; then
        log_error "Base directory is not writable: $BASE_DIR"
        log_error "Cannot create repository at: $REPO_PATH"
        exit 1
    fi
fi

log_info "Starting AvyRSS update process"
log_info "Base directory: $BASE_DIR"
log_info "Repository path: $REPO_PATH"

# Step 1: Clone or pull repository
if [ -d "$REPO_PATH" ]; then
    log_info "Repository exists, pulling latest changes..."
    cd "$REPO_PATH"

    # Check if it's a git repository
    if [ ! -d ".git" ]; then
        log_error "$REPO_PATH exists but is not a git repository"
        exit 1
    fi

    # Pull latest changes
    log_info "Running: git pull origin main"
    if git pull origin main; then
        log_info "Successfully pulled latest changes"
    else
        log_error "Failed to pull from repository"
        exit 1
    fi
else
    log_info "Repository does not exist, cloning..."
    cd "$BASE_DIR"

    # Clone repository
    log_info "Running: git clone $REPO_URL"
    if git clone "$REPO_URL" "$REPO_NAME"; then
        log_info "Successfully cloned repository"
        cd "$REPO_PATH"
    else
        log_error "Failed to clone repository"
        log_error "Make sure AVYRSS_REPO_URL is set correctly or update REPO_URL in this script"
        exit 1
    fi
fi

# Step 2: Check for virtual environment
if [ ! -d "venv" ]; then
    log_warn "Virtual environment not found"
    log_info "Creating virtual environment..."
    python3 -m venv venv

    log_info "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    log_info "Activating virtual environment..."
    source venv/bin/activate

    # Update dependencies in case requirements.txt changed
    log_info "Updating dependencies..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
fi

# Verify we're in the right place
if [ ! -f "bin/manage.py" ]; then
    log_error "bin/manage.py not found. Are we in the right directory?"
    exit 1
fi

# Step 3: Run full update
log_info "Running full update (downloading forecasts and generating feeds)..."
log_info "This may take a few minutes..."

# Use AVYRSS_BASE_URL environment variable if set, otherwise default to http://www.avyrss.com
BASE_URL="${AVYRSS_BASE_URL:-https://www.avyrss.com}"

if python3 bin/manage.py --base-url "$BASE_URL" full-update; then
    log_info "✓ Successfully completed full update"
else
    log_error "Failed to complete full update"
    exit 1
fi

# Step 4: Summary
echo ""
log_info "================================================"
log_info "AvyRSS Update Complete!"
log_info "================================================"
log_info "Repository: $REPO_PATH"
log_info "Forecasts: $REPO_PATH/forecasts/"
log_info "RSS Feeds: $REPO_PATH/feeds/"
log_info "Index Page: $REPO_PATH/index.html"
log_info "================================================"

exit 0
