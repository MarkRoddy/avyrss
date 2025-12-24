# Installation Files

This directory contains production installation configuration files for AvyRSS.

## Files

- **install.sh** - Automated installation script
- **avyrss-update.timer** - Systemd timer for scheduled feed updates
- **avyrss-update.service** - Systemd service for running feed updates
- **nginx.conf** - Nginx web server configuration for avyrss.com
- **README.md** - This file

## Quick Start Installation

### Option A: Automated Installation (Recommended)

```bash
sudo bash install/install.sh
```

This will guide you through the complete setup process.

### Option B: Manual Installation

### 1. Prerequisites

```bash
# Create dedicated avyrss user
sudo useradd -r -s /bin/bash -d /var/lib/avyrss -c "AvyRSS Service User" avyrss

# Add avyrss to www-data group for file sharing
sudo usermod -a -G www-data avyrss

# Create log file
sudo touch /var/log/avyrss-update.log
sudo chown avyrss:www-data /var/log/avyrss-update.log
```

### 2. Install Systemd Timer and Service

```bash
# Copy systemd files
sudo cp install/avyrss-update.timer /etc/systemd/system/
sudo cp install/avyrss-update.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable avyrss-update.timer
sudo systemctl start avyrss-update.timer

# Verify installation
sudo systemctl status avyrss-update.timer
sudo systemctl list-timers avyrss-update.timer
```

**Important**: The timer uses fixed UTC times and works on any server timezone.

### 3. Initial Repository Setup

```bash
# Manually run the update script for first-time setup
sudo -u avyrss bash -c "curl -fsSL https://raw.githubusercontent.com/MarkRoddy/avyrss/refs/heads/main/bin/update-feeds.sh | bash -s -- /var/www"

# Set up group permissions with setgid bit
sudo chown -R avyrss:www-data /var/www/avyrss/forecasts /var/www/avyrss/feeds
sudo chmod -R g+w /var/www/avyrss/forecasts /var/www/avyrss/feeds
sudo chmod g+s /var/www/avyrss/forecasts /var/www/avyrss/feeds
sudo chown avyrss:www-data /var/www/avyrss/index.html
sudo chmod g+w /var/www/avyrss/index.html
```

This will:
- Clone the repository to `/var/www/avyrss`
- Set up the Python virtual environment
- Download initial forecasts
- Generate RSS feeds and index page
- Configure permissions so avyrss creates files accessible by www-data

### 4. Install Nginx Configuration

```bash
# Copy nginx config
sudo cp install/nginx.conf /etc/nginx/sites-available/avyrss.com

# Create symlink to enable site
sudo ln -s /etc/nginx/sites-available/avyrss.com /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 5. Set Up SSL (Recommended)

```bash
# Install certbot if not already installed
sudo apt install certbot python3-certbot-nginx

# Obtain and install SSL certificate
sudo certbot --nginx -d avyrss.com -d www.avyrss.com

# Certbot will automatically modify nginx.conf to add SSL
```

## Update Schedule

The systemd timer runs every 6 hours at fixed UTC times:
- **3am UTC** - 7pm PST / 8pm PDT (catches fresh forecasts that publish around 6pm PT)
- **9am UTC** - 1am PST / 2am PDT
- **3pm UTC** - 7am PST / 8am PDT
- **9pm UTC** - 1pm PST / 2pm PDT

The timer uses fixed UTC times and works on any server timezone.

## File Permissions

The update service runs as the dedicated `avyrss` user with group `www-data`:
- Service creates files as avyrss:www-data with group-write permissions
- Setgid bit on directories ensures new files inherit www-data group
- Nginx reads files as www-data (group access)
- www-data stays locked down (no shell required)

## Directory Structure

After installation, your structure will be:

```
/var/www/avyrss/
├── app/                    # Application code
├── bin/                    # Utility scripts
├── forecasts/              # Downloaded forecasts (www-data owned)
├── feeds/                  # Generated RSS feeds (www-data owned)
├── index.html              # Generated index page (www-data owned)
├── requirements.txt
├── avalanche_centers.yaml
└── ...
```

## Monitoring

### Check Service Logs

```bash
# View update logs (journald)
sudo journalctl -u avyrss-update -f

# Check recent updates
sudo journalctl -u avyrss-update -n 100

# View legacy log file (if exists)
sudo tail -f /var/log/avyrss-update.log
```

### Check Timer Status

```bash
# Check if timer is active and when it runs next
sudo systemctl status avyrss-update.timer

# List all timers
sudo systemctl list-timers avyrss-update.timer

# Manually trigger an update
sudo systemctl start avyrss-update.service
```

### Check Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/avyrss-access.log

# Error logs
sudo tail -f /var/log/nginx/avyrss-error.log
```

### Verify Feeds Are Updating

```bash
# Check most recent feed modification time
ls -lt /var/www/avyrss/feeds/*/*.xml | head -5

# Check how many feeds exist
find /var/www/avyrss/feeds -name "*.xml" | wc -l
# Should show 57 feeds (one per zone)
```

## Troubleshooting

### Timer Not Running

```bash
# Check if timer is installed and active
sudo systemctl status avyrss-update.timer

# Check when timer will run next
sudo systemctl list-timers avyrss-update.timer

# Check service logs for errors
sudo journalctl -u avyrss-update -n 50

# Manually test the service
sudo systemctl start avyrss-update.service
sudo journalctl -u avyrss-update -f
```

### Permission Issues

```bash
# Verify ownership
ls -la /var/www/avyrss/

# Should show avyrss:www-data for forecasts/, feeds/, index.html

# Fix ownership if needed
sudo chown -R avyrss:www-data /var/www/avyrss/forecasts
sudo chown -R avyrss:www-data /var/www/avyrss/feeds
sudo chown avyrss:www-data /var/www/avyrss/index.html

# Ensure group write permissions
sudo chmod -R g+w /var/www/avyrss/forecasts /var/www/avyrss/feeds
sudo chmod g+s /var/www/avyrss/forecasts /var/www/avyrss/feeds
```

### Nginx 404 Errors

```bash
# Verify files exist
ls -la /var/www/avyrss/index.html
ls -la /var/www/avyrss/feeds/

# Test nginx config
sudo nginx -t

# Check error logs
sudo tail -50 /var/log/nginx/avyrss-error.log
```

### Manual Update

If you need to manually trigger an update:

```bash
# Using systemd (recommended)
sudo systemctl start avyrss-update.service

# Or directly run the script
sudo -u avyrss bash -c "curl -fsSL https://raw.githubusercontent.com/MarkRoddy/avyrss/refs/heads/main/bin/update-feeds.sh | bash -s -- /var/www"
```

## Updating Configuration

### Update Systemd Timer/Service

```bash
# Edit the local files
vim install/avyrss-update.timer
vim install/avyrss-update.service

# Reinstall
sudo cp install/avyrss-update.timer /etc/systemd/system/
sudo cp install/avyrss-update.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart avyrss-update.timer
```

### Update Nginx Config

```bash
# Edit the local file
vim install/nginx.conf

# Copy to nginx directory
sudo cp install/nginx.conf /etc/nginx/sites-available/avyrss.com

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

## Security Notes

- RSS feeds and index.html are public by design (world-readable is fine)
- Sensitive files (.git, .env, venv/, bin/) are blocked by nginx config
- SSL/HTTPS is strongly recommended (use certbot)
- The update script is fetched from GitHub main branch each time it runs
- Dedicated avyrss user runs updates (separation of concerns)
- www-data user stays locked down (no shell required)
- Systemd service has security hardening (PrivateTmp, ProtectSystem, etc.)

## Backup Considerations

The generated files (forecasts, feeds, index.html) are ephemeral and can be regenerated:
- No need to backup forecasts/ or feeds/
- The repository itself is the source of truth
- Configuration files (avalanche_centers.yaml) are in the git repository

For disaster recovery:
1. Redeploy nginx config
2. Reinstall systemd timer and service
3. Run manual update to regenerate all files
